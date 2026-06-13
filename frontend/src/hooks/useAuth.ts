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
    onError: () => {
      toast.error("Invalid login or password");
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
