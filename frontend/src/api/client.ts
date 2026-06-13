import axios from "axios";
import toast from "react-hot-toast";
import { useAuthStore } from "@/store/authStore";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = token;
  }
  return config;
});

let isRefreshing = false;
let pendingQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

function processPending(token: string) {
  pendingQueue.forEach((p) => p.resolve(token));
  pendingQueue = [];
}
function rejectPending(err: unknown) {
  pendingQueue.forEach((p) => p.reject(err));
  pendingQueue = [];
}

apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;

    if (error.response?.status === 401 && !original._retry) {
      const store = useAuthStore.getState();

      if (original.url?.includes("/auth/login")) {
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          pendingQueue.push({
            resolve: (token: string) => {
              original.headers.Authorization = token;
              resolve(apiClient(original));
            },
            reject,
          });
        });
      }

      original._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = store.refreshToken;
        if (!refreshToken) throw new Error("No refresh token");

        const { data } = await axios.post(
          `${API_BASE}/v1/users/auth/login/refresh`,
          null,
          { headers: { Authorization: refreshToken } },
        );

        const newAccess = data.access_token as string;
        const newRefresh = data.refresh_token as string;
        store.setTokens(newAccess, newRefresh);
        processPending(newAccess);

        original.headers.Authorization = newAccess;
        return apiClient(original);
      } catch (refreshError) {
        rejectPending(refreshError);
        store.logout();
        window.location.href = "/login";
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    if (error.response) {
      const status = error.response.status as number;
      const detail = error.response.data?.detail;

      if (status === 422 && Array.isArray(detail)) {
        const messages = detail.map((d: { msg: string }) => d.msg).join(", ");
        toast.error(`Validation error: ${messages}`);
      } else if (status === 403) {
        toast.error("Access denied");
      } else if (status !== 401) {
        const msg = typeof detail === "string" ? detail : "Something went wrong";
        toast.error(msg);
      }
    }

    return Promise.reject(error);
  },
);
