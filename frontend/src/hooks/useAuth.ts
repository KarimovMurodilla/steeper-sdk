import { AxiosError } from "axios";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { authApi } from "@/api/auth";
import { useAuthStore } from "@/store/authStore";
import type { PasswordLoginRequest } from "@/types/api";

export function useLogin() {
  const { setTokens, setUser } = useAuthStore();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: PasswordLoginRequest) => authApi.login(data),
    onSuccess: ({ data }) => {
      setTokens(data.tokens.access_token, data.tokens.refresh_token);
      setUser(data.user);
      queryClient.invalidateQueries({ queryKey: ["me"] });
      toast.success("Welcome back!");
      navigate("/");
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      const status = error.response?.status;
      const detail = error.response?.data?.detail;

      if (status === 401 || status === 403) {
        toast.error("Invalid login or password");
        return;
      }
      if (detail === "Database query error.") {
        // The backend hides the SQL error; on a fresh install this almost
        // always means the schema or the first superadmin is missing.
        toast.error(
          "Oops, the server could not reach the database. Migrations may not have been applied yet, or the superadmin was never created.",
        );
        return;
      }
      if (!error.response) {
        toast.error("The server is unreachable. Check that the backend is running.");
        return;
      }
      toast.error("Something went wrong. Please try again.");
    },
  });
}

export function useMe() {
  const { setUser, isAuthenticated } = useAuthStore();

  return useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const { data } = await authApi.getMe();
      setUser(data);
      return data;
    },
    enabled: isAuthenticated(),
    retry: false,
    staleTime: 5 * 60 * 1000,
  });
}
