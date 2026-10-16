<template>
  <div class="ppt-preview-page">
    <div class="page-header">
      <el-button link @click="$router.push(`/analysis/${sessionId}/report`)">
        <el-icon><ArrowLeft /></el-icon> 返回报告
      </el-button>
      <h2>📊 幻灯片预览</h2>
      <el-button type="primary" @click="downloadPpt(sessionId)">下载 .pptx</el-button>
    </div>

    <el-card v-loading="loading">
      <div v-if="error" class="preview-error">
        <el-empty :description="error">
          <el-button type="primary" @click="downloadPpt(sessionId)">下载 .pptx</el-button>
        </el-empty>
      </div>
      <div v-show="!error" ref="viewerHost" class="viewer-host"></div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from "vue";
import { useRoute } from "vue-router";
import { pptUrl, downloadPpt } from "@/api/analyses";
import { createPptxViewer } from "pptx-vanilla-viewer";

const route = useRoute();
const sessionId = route.params.id as string;
const loading = ref(false);
const error = ref("");
const viewerHost = ref<HTMLDivElement | null>(null);
let viewer: any = null;

onMounted(async () => {
  loading.value = true;
  error.value = "";
  try {
    if (viewerHost.value) {
      viewer = createPptxViewer(viewerHost.value, {
        source: pptUrl(sessionId),
        onLoad: () => {
          loading.value = false;
        },
        onError: (e: unknown) => {
          error.value = "幻灯片预览加载失败";
          console.error("PPT 预览失败:", e);
          loading.value = false;
        },
      });
      // 若返回 Promise 则等待其完成，避免 loading 状态提前结束
      if (viewer && typeof viewer.then === "function") {
        await viewer;
        loading.value = false;
      }
    }
  } catch (e) {
    error.value = "幻灯片预览加载失败";
    console.error("PPT 预览失败:", e);
    loading.value = false;
  }
});

onBeforeUnmount(() => {
  try {
    viewer?.destroy?.();
  } catch {
    /* 忽略销毁异常 */
  }
});
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
  flex: 1;
}
.viewer-host {
  width: 100%;
  height: calc(100vh - 200px);
  min-height: 480px;
  background: #f5f7fa;
  border-radius: 6px;
  overflow: hidden;
}
.preview-error {
  padding: 40px 0;
}
</style>
