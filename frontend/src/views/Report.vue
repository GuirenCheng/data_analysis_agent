<template>
  <div class="report-page">
    <div class="page-header">
      <el-button link @click="$router.push(`/analysis/${sessionId}`)">
        <el-icon><ArrowLeft /></el-icon> 返回分析详情
      </el-button>
      <h2>📄 最终分析报告</h2>
    </div>

    <el-card v-loading="loading">
      <div v-if="report" class="report-content markdown-body" v-html="renderedMarkdown" />
      <el-empty v-else description="报告尚未生成或不可用" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { analysesApi } from "@/api/analyses";
import { renderMarkdown } from "@/utils/markdown";

const route = useRoute();
const sessionId = route.params.id as string;
const loading = ref(false);
const report = ref<any>(null);

const renderedMarkdown = computed(() => {
  if (!report.value?.markdown) return "";
  return renderMarkdown(report.value.markdown, sessionId);
});

onMounted(async () => {
  loading.value = true;
  try {
    report.value = await analysesApi.getReport(sessionId);
  } finally {
    loading.value = false;
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
.report-content {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}
.markdown-body :deep(h1) {
  font-size: 24px;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 8px;
}
.markdown-body :deep(h2) {
  font-size: 20px;
  margin-top: 24px;
}
.markdown-body :deep(h3) {
  font-size: 17px;
  margin-top: 20px;
}
.markdown-body :deep(pre) {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
}
.markdown-body :deep(img) {
  max-width: 100%;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
}
.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid #e2e8f0;
  padding: 8px 12px;
  text-align: left;
}
.markdown-body :deep(th) {
  background: #f5f7fa;
  font-weight: 600;
}
</style>
