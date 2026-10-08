<template>
  <div class="rag-page">
    <div class="page-header">
      <h2>🔍 知识搜索</h2>
      <p class="subtitle">基于语义搜索历史分析中的代码、报告和洞察</p>
    </div>

    <el-card>
      <div class="search-bar">
        <el-input
          v-model="query"
          placeholder="输入关键词搜索历史分析..."
          size="large"
          clearable
          @keyup.enter="doSearch"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
          <template #append>
            <el-button type="primary" :loading="searching" @click="doSearch">搜索</el-button>
          </template>
        </el-input>
        <el-select v-model="contentType" placeholder="内容类型" clearable style="width:140px;margin-left:12px">
          <el-option label="全部" value="" />
          <el-option label="查询" value="query" />
          <el-option label="代码" value="code" />
          <el-option label="报告" value="report" />
          <el-option label="图表" value="figure" />
        </el-select>
      </div>

      <div v-if="results.length > 0" class="results">
        <div v-for="(r, idx) in results" :key="idx" class="result-item">
          <div class="result-header">
            <el-tag :type="typeColor(r.content_type)" size="small">{{ r.content_type }}</el-tag>
            <span class="similarity">相似度: {{ (r.similarity * 100).toFixed(1) }}%</span>
          </div>
          <div class="result-content">
            <pre v-if="r.content_type === 'code'"><code>{{ r.content_text }}</code></pre>
            <p v-else>{{ r.content_text }}</p>
          </div>
        </div>
      </div>

      <el-empty v-if="!searching && query && results.length === 0" description="未找到相关结果" />
      <el-empty v-if="!query" description="输入关键词开始搜索历史分析" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { ragApi } from "@/api/rag";
import type { RagResult } from "@/types";

const query = ref("");
const contentType = ref("");
const searching = ref(false);
const results = ref<RagResult[]>([]);

function typeColor(type: string) {
  const map: Record<string, any> = { query: "", code: "success", report: "warning", figure: "info" };
  return map[type] || "";
}

async function doSearch() {
  if (!query.value.trim()) return;
  searching.value = true;
  try {
    const res = await ragApi.search(query.value, 10, contentType.value || undefined);
    results.value = res.results;
  } finally {
    searching.value = false;
  }
}
</script>

<style scoped>
.page-header {
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
}
.subtitle {
  color: #718096;
  font-size: 14px;
  margin: 4px 0 0;
}
.search-bar {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}
.results {
  max-height: 600px;
  overflow-y: auto;
}
.result-item {
  padding: 16px;
  margin-bottom: 12px;
  background: #f7fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.similarity {
  font-size: 12px;
  color: #a0aec0;
}
.result-content pre {
  background: #edf2f7;
  padding: 12px;
  border-radius: 4px;
  font-size: 13px;
  overflow-x: auto;
  max-height: 200px;
}
.result-content p {
  font-size: 14px;
  color: #2d3748;
  line-height: 1.6;
}
</style>
