<template>
  <el-container class="layout">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <el-icon :size="28"><DataAnalysis /></el-icon>
        <span>数据分析智能体</span>
      </div>
      <el-menu
        :default-active="currentRoute"
        router
        background-color="#1d1e2c"
        text-color="#a0aec0"
        active-text-color="#409eff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Monitor /></el-icon>
          <span>分析面板</span>
        </el-menu-item>
        <el-menu-item index="/analysis/new">
          <el-icon><Plus /></el-icon>
          <span>新建分析</span>
        </el-menu-item>
        <el-menu-item index="/files">
          <el-icon><FolderOpened /></el-icon>
          <span>文件管理</span>
        </el-menu-item>
        <el-menu-item index="/rag">
          <el-icon><Search /></el-icon>
          <span>知识搜索</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统配置</span>
        </el-menu-item>
      </el-menu>
      <div class="user-footer">
        <span>{{ authStore.user?.username }}</span>
        <el-button text size="small" @click="handleLogout">退出</el-button>
      </div>
    </el-aside>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useAnalysisStore } from "@/stores/analysis";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const analysisStore = useAnalysisStore();

const currentRoute = computed(() => route.path);

function handleLogout() {
  analysisStore.stopAllStreams();
  authStore.logout();
  router.push("/login");
}
</script>

<style scoped>
.layout {
  min-height: 100vh;
}
.sidebar {
  background: #1d1e2c;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px;
  color: #e2e8f0;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 1px solid #2d2e3c;
}
.el-menu {
  border-right: none;
  flex: 1;
}
.user-footer {
  padding: 16px 20px;
  color: #a0aec0;
  font-size: 13px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #2d2e3c;
}
.el-main {
  background: #f5f7fa;
  padding: 24px;
}
</style>
