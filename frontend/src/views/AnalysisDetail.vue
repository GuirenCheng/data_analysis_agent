<template>
  <div class="detail">
    <div class="page-header">
      <el-button link @click="$router.push('/dashboard')">
        <el-icon><ArrowLeft /></el-icon> 返回
      </el-button>
      <h2>分析详情</h2>
      <el-button
        v-if="session?.status === 'completed'"
        type="primary"
        @click="$router.push(`/analysis/${session?.id}/report`)"
      >查看报告</el-button>
      <el-button v-if="session?.status === 'running'" type="warning" @click="handleCancel">取消分析</el-button>
    </div>

    <el-card v-if="session" class="info-card">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="需求">{{ session.query }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType(session.status)">{{ statusLabel(session.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="轮次">{{ session.current_round }} / {{ session.max_rounds }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(session.created_at) }}</el-descriptions-item>
      </el-descriptions>

      <div class="progress-section">
        <el-progress
          :percentage="Math.round(progress * 100)"
          :status="session.status === 'failed' ? 'exception' : session.status === 'completed' ? 'success' : undefined"
          :stroke-width="12"
          :text-inside="true"
        />
      </div>
    </el-card>

    <!-- 分析步骤 -->
    <el-card v-if="session?.steps?.length" class="steps-card">
      <template #header><span>📋 分析步骤</span></template>
      <el-timeline>
        <el-timeline-item
          v-for="step in session.steps"
          :key="step.id"
          :timestamp="`第 ${step.round_number} 轮 · ${step.action}`"
          :type="step.execution_success === false ? 'danger' : step.execution_success ? 'success' : 'primary'"
        >
          <div v-if="step.code" class="step-code">
            <el-collapse>
              <el-collapse-item title="查看代码">
                <pre><code>{{ step.code }}</code></pre>
              </el-collapse-item>
            </el-collapse>
          </div>
          <div v-if="step.execution_output" class="step-output">
            <strong>输出:</strong>
            <pre>{{ step.execution_output }}</pre>
          </div>
          <div v-if="step.execution_error" class="step-error">
            <el-alert :title="step.execution_error" type="error" :closable="false" />
          </div>
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <!-- 图表展示 -->
    <el-card v-if="session?.figures?.length" class="figures-card">
      <template #header><span>📈 分析图表 ({{ session.figures.length }})</span></template>
      <el-row :gutter="16">
        <el-col :span="12" v-for="fig in session.figures" :key="fig.filename" style="margin-bottom:16px">
          <el-card shadow="hover">
            <template #header>{{ fig.filename }}</template>
            <el-image
              v-if="fig.filename"
              :src="figureUrl(sid, fig.filename)"
              fit="contain"
              style="width:100%;max-height:300px"
              :preview-src-list="[figureUrl(sid, fig.filename)]"
            />
            <p class="fig-desc">{{ fig.description }}</p>
            <p class="fig-analysis">{{ fig.analysis }}</p>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <!-- 分析结果（最终报告） -->
    <el-card v-if="report?.markdown" class="report-card">
      <template #header><span>📄 分析结果</span></template>
      <div class="markdown-body" v-html="renderedReport" />
    </el-card>

    <!-- 空状态 -->
    <el-empty v-if="!session" description="加载中..." />
    <el-empty v-if="session?.status === 'pending'" description="任务等待中..." />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import { useRoute } from "vue-router";
import { useAnalysisStore } from "@/stores/analysis";
import { analysesApi, figureUrl } from "@/api/analyses";
import { renderMarkdown } from "@/utils/markdown";
import { ElMessage, ElMessageBox } from "element-plus";
import dayjs from "dayjs";
import type { SessionDetail, ReportOut } from "@/types";

const route = useRoute();
const store = useAnalysisStore();
const sid = route.params.id as string;
const session = ref<SessionDetail | null>(null);
const report = ref<ReportOut | null>(null);
const renderedReport = computed(() =>
  report.value?.markdown ? renderMarkdown(report.value.markdown, sid) : ""
);
const progress = computed(() => {
  const evt = store.streamProgress[sid];
  return evt?.progress ?? session.value?.progress ?? 0;
});

function statusType(s: string) {
  const map: Record<string, any> = { pending: "info", running: "warning", completed: "success", failed: "danger" };
  return map[s] || "info";
}
function statusLabel(s: string) {
  const map: Record<string, string> = { pending: "等待中", running: "运行中", completed: "已完成", failed: "失败", cancelled: "已取消" };
  return map[s] || s;
}
function formatTime(t?: string) {
  return t ? dayjs(t).format("YYYY-MM-DD HH:mm:ss") : "-";
}
async function loadDetail() {
  session.value = await store.fetchSessionDetail(sid);

  // 等待中或运行中都启动 SSE 监听（任务从 pending 转 running 也能收到进度）
  const status = session.value?.status;
  if (status === "pending" || status === "running") {
    store.startStream(sid);
  } else if (status === "completed") {
    // 已完成的会话直接拉取最终报告
    try {
      report.value = await analysesApi.getReport(sid);
    } catch { /* 报告可能尚未生成 */ }
  }
}

async function handleCancel() {
  try {
    await ElMessageBox.confirm("确定取消此分析？", "确认", { type: "warning" });
    await analysesApi.cancel(sid);
    store.stopStream(sid);
    ElMessage.success("已取消");
    loadDetail();
  } catch { /* cancelled */ }
}

// 定时刷新（当有 SSE 推送状态变更时）
const pollTimer = ref<ReturnType<typeof setInterval>>();
onMounted(() => {
  loadDetail();
  pollTimer.value = setInterval(() => {
    const evt = store.streamProgress[sid];
    if (evt && (evt.status === "completed" || evt.status === "failed")) {
      store.stopStream(sid);
      loadDetail();
    } else if (
      session.value &&
      (session.value.status === "pending" || session.value.status === "running")
    ) {
      // 流未建立或已断开时重连（幂等）
      store.startStream(sid);
    }
  }, 2000);
});

onUnmounted(() => {
  if (pollTimer.value) clearInterval(pollTimer.value);
  store.stopStream(sid);
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
.info-card {
  margin-bottom: 16px;
}
.progress-section {
  margin-top: 16px;
}
.steps-card,
.figures-card {
  margin-bottom: 16px;
}
.step-code pre,
.step-output pre {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-size: 13px;
  overflow-x: auto;
  max-height: 200px;
}
.step-error {
  margin-top: 8px;
}
.fig-desc {
  font-size: 14px;
  color: #4a5568;
  margin: 8px 0 4px;
}
.fig-analysis {
  font-size: 13px;
  color: #718096;
}
.report-card {
  margin-bottom: 16px;
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
