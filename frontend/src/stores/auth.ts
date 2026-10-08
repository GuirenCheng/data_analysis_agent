import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { authApi } from "@/api/auth";
import type { UserInfo } from "@/types";

export const useAuthStore = defineStore("auth", () => {
  const token = ref<string>(localStorage.getItem("access_token") || "");
  const user = ref<UserInfo | null>(null);
  const loading = ref(false);

  const isLoggedIn = computed(() => !!token.value);

  async function login(username: string, password: string) {
    loading.value = true;
    try {
      const res = await authApi.login({ username, password });
      token.value = res.access_token;
      localStorage.setItem("access_token", res.access_token);
      await fetchUser();
      return true;
    } finally {
      loading.value = false;
    }
  }

  async function register(username: string, email: string, password: string) {
    loading.value = true;
    try {
      await authApi.register({ username, email, password });
      return true;
    } finally {
      loading.value = false;
    }
  }

  async function fetchUser() {
    if (!token.value) return;
    try {
      user.value = await authApi.getMe();
    } catch {
      logout();
    }
  }

  function logout() {
    token.value = "";
    user.value = null;
    localStorage.removeItem("access_token");
  }

  return { token, user, loading, isLoggedIn, login, register, fetchUser, logout };
});
