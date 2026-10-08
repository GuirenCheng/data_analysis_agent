import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/login",
      name: "Login",
      component: () => import("@/views/Login.vue"),
      meta: { guest: true },
    },
    {
      path: "/register",
      name: "Register",
      component: () => import("@/views/Register.vue"),
      meta: { guest: true },
    },
    {
      path: "/",
      component: () => import("@/components/Layout.vue"),
      redirect: "/dashboard",
      children: [
        {
          path: "dashboard",
          name: "Dashboard",
          component: () => import("@/views/Dashboard.vue"),
        },
        {
          path: "analysis/new",
          name: "AnalysisCreate",
          component: () => import("@/views/AnalysisCreate.vue"),
        },
        {
          path: "analysis/:id",
          name: "AnalysisDetail",
          component: () => import("@/views/AnalysisDetail.vue"),
        },
        {
          path: "analysis/:id/report",
          name: "Report",
          component: () => import("@/views/Report.vue"),
        },
        {
          path: "files",
          name: "Files",
          component: () => import("@/views/Files.vue"),
        },
        {
          path: "settings",
          name: "Settings",
          component: () => import("@/views/Settings.vue"),
        },
        {
          path: "rag",
          name: "RagSearch",
          component: () => import("@/views/RagSearch.vue"),
        },
      ],
    },
  ],
});

// 路由守卫 — 未登录重定向
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem("access_token");

  if (to.meta.guest && token) {
    return next("/dashboard");
  }

  if (!to.meta.guest && !token) {
    return next("/login");
  }

  next();
});

export default router;
