import client from "./client";
import type { TokenResponse, LoginRequest, RegisterRequest, UserInfo } from "@/types";

export const authApi = {
  login(data: LoginRequest): Promise<TokenResponse> {
    const form = new FormData();
    form.append("username", data.username);
    form.append("password", data.password);
    return client.post("/auth/token", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    }).then((r) => r.data);
  },

  register(data: RegisterRequest): Promise<UserInfo> {
    return client.post("/auth/register", data).then((r) => r.data);
  },

  getMe(): Promise<UserInfo> {
    return client.get("/users/me").then((r) => r.data);
  },
};
