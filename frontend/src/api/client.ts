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
let refreshPromise: Promise<string> | null = null;
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

/**
 * Exchange the stored refresh token for a fresh access token, update the store,
 * and return the new access token. Concurrent callers share a single in-flight
 * request. Used by both the 401 response interceptor and the WebSocket hook (on
 * a 1008 close) so the operator is not logged out when the access token expires.
 */
export async function refreshAccessToken(): Promise<string> {
  if (isRefreshing && refreshPromise) return refreshPromise;

  isRefreshing = true;
  refreshPromise = (async () => {
    const store = useAuthStore.getState();
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
    return newAccess;
  })();

  try {
    const token = await refreshPromise;
    processPending(token);
    return token;
  } catch (err) {
    rejectPending(err);
    throw err;
  } finally {
    isRefreshing = false;
    refreshPromise = null;
  }
}

apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;

    if (error.response?.status === 401 && !original._retry) {
      if (original.url?.includes("/auth/login")) {
        return Promise.reject(error);
      }

      // Mark before re-issuing so a replayed request that 401s again does not
      // re-enter this branch and trigger a refresh storm.
      original._retry = true;

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

      try {
        const newAccess = await refreshAccessToken();
        original.headers.Authorization = newAccess;
        return apiClient(original);
      } catch (refreshError) {
        useAuthStore.getState().logout();
        window.location.href = "/login";
        return Promise.reject(refreshError);
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
