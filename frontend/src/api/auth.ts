import { apiClient } from "./client";
import type {
  PasswordLoginRequest,
  PasswordAuthResponse,
  UserProfileViewModel,
} from "@/types/api";

export const authApi = {
  login(data: PasswordLoginRequest) {
    return apiClient.post<PasswordAuthResponse>(
      "/v1/users/auth/login/password",
      data,
    );
  },

  getMe() {
    return apiClient.get<UserProfileViewModel>("/v1/users/me");
  },

  getUser(userId: string) {
    return apiClient.get<UserProfileViewModel>(`/v1/users/${userId}`);
  },
};
