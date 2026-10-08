<template>
  <div class="dashboard">
    <div class="page-header">
      <h2>📊 分析面板</h2>
      <el-button type="primary" @click="$router.push('/analysis/new')">
        <el-icon><Plus /></el-icon> 新建分析
      </el-button>
    </div>

    <el-row :gutter="16" class="stats-row">
      <el-col :span="6" v-for="stat in stats" :key="stat.label">
        <el-card shadow="hover">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>分析历史</span>
          <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width:140px" @change="loadSessions">
            <el-option label="全部" value="" />
            <el-option label="运行中" value="running" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </div>
      </template>

      <el-table :data="store.sessions" v-loading="store.loading" stripe @row-click="goDetail" style="cursor:pointer">
        <el-table-column prop="query" label="分析需求" min-width="240" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="进度" width="160">
          <template #default="{ row }">
            <el-progress
              :percentage="Math.round((row.progress || 0) * 100)"
              :status="row.status === 'failed' ? 'exception' : row.status === 'completed' ? 'success' : undefined"
              :stroke-width="8"
            />
          </template>
        </el-table-column>
        <el-table-column prop="current_round" label="轮次" width="70" />
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click.stop="goDetail(row)">详情</el-button>
            <el-button link type="danger" size="small" @click.stop="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="page"
          :page-size="20"
          :total="store.total"
          layout="prev, pager, next"
          @current-change="loadSessions"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { useAnalysisStore } from "@/stores/analysis";
import { ElMessageBox } from "element-plus";
import dayjs from "dayjs";
import type { SessionOut } from "@/types";

const router = useRouter();
const store = useAnalysisStore();
const page = ref(1);
const filterStatus = ref("");

const stats = computed(() => {
  const items = store.sessions;
  return [
    { label: "总分析数", value: store.total },
    { label: "运行中", value: items.filter((s) => s.status === "running").length },
    { label: "已完成", value: items.filter((s) => s.status === "completed").length },
    { label: "失败", value: items.filter((s) => s.status === "failed").length },
  ];
});

function statusType(s: string) {
  const map: Record<string, any> = { pending: "info", running: "warning", completed: "success", failed: "danger", cancelled: "info" };
  return map[s] || "info";
}
function statusLabel(s: string) {
  const map: Record<string, string> = { pending: "等待中", running: "运行中", completed: "已完成", failed: "失败", cancelled: "已取消" };
  return map[s] || s;
}
function formatTime(t?: string) {
  return t ? dayjs(t).format("YYYY-MM-DD HH:mm") : "-";
}

async function loadSessions() {
  await store.fetchSessions(page.value, 20, filterStatus.value || undefined);
}

function goDetail(row: SessionOut) {
  router.push(`/analysis/${row.id}`);
}

async function handleDelete(row: SessionOut) {
  try {
    await ElMessageBox.confirm("确定删除此分析会话？", "确认删除", { type: "warning" });
    await store.deleteSession(row.id);
  } catch { /* cancelled */ }
}

onMounted(() => loadSessions());
onUnmounted(() => store.stopAllStreams());
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
}
.stats-row {
  margin-bottom: 20px;
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1d1e2c;
}
.stat-label {
  font-size: 13px;
  color: #718096;
  margin-top: 4px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}
</style>
