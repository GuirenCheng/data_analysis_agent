<template>
  <div class="files-page">
    <div class="page-header">
      <h2>📁 文件管理</h2>
    </div>

    <el-card>
      <el-upload
        :auto-upload="false"
        :on-change="handleUpload"
        :limit="10"
        accept=".csv,.xlsx,.xls,.json,.parquet"
        drag
        style="margin-bottom:20px"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">拖拽文件到此处，或 <em>点击上传</em></div>
      </el-upload>

      <el-table :data="files" stripe>
        <el-table-column prop="original_name" label="文件名" min-width="200" />
        <el-table-column label="大小" width="100">
          <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column label="列数" width="80">
          <template #default="{ row }">{{ row.columns_detected?.length || "-" }}</template>
        </el-table-column>
        <el-table-column label="行数" width="80">
          <template #default="{ row }">{{ row.row_count ?? "-" }}</template>
        </el-table-column>
        <el-table-column label="上传时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="previewFile(row)">预览</el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 预览对话框 -->
    <el-dialog v-model="previewVisible" title="文件预览" width="80%">
      <el-table :data="previewData.rows" border max-height="400">
        <el-table-column
          v-for="col in previewData.columns"
          :key="col"
          :label="col"
          :prop="col"
          min-width="120"
          show-overflow-tooltip
        />
      </el-table>
      <p style="margin-top: 12px; color: #718096; font-size:13px">
        共 {{ previewData.total_rows }} 行，当前显示前 {{ previewData.rows.length }} 行
      </p>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue";
import { filesApi } from "@/api/files";
import { ElMessage, ElMessageBox } from "element-plus";
import dayjs from "dayjs";
import type { FileOut } from "@/types";
import type { UploadFile } from "element-plus";

const files = ref<FileOut[]>([]);
const previewVisible = ref(false);
const previewData = reactive({ columns: [] as string[], rows: [] as any[][], total_rows: 0 });

function formatSize(bytes?: number) {
  if (!bytes) return "-";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
function formatTime(t?: string) {
  return t ? dayjs(t).format("YYYY-MM-DD HH:mm") : "-";
}

async function handleUpload(file: UploadFile) {
  if (!file.raw) return;
  try {
    const res = await filesApi.upload(file.raw);
    files.value.unshift(res.file);
    ElMessage.success(`上传成功: ${res.file.original_name}`);
  } catch { /* handled */ }
}

async function previewFile(file: FileOut) {
  try {
    const data = await filesApi.preview(file.id);
    previewData.columns = data.columns;
    // 转换行数据为对象数组以便 el-table 渲染
    previewData.rows = data.rows.map((row: any[]) => {
      const obj: Record<string, any> = {};
      data.columns.forEach((col, idx) => { obj[col] = row[idx]; });
      return obj;
    }) as any;
    previewData.total_rows = data.total_rows;
    previewVisible.value = true;
  } catch { /* handled */ }
}

async function handleDelete(file: FileOut) {
  try {
    await ElMessageBox.confirm(`确定删除文件 ${file.original_name}？`, "确认", { type: "warning" });
    await filesApi.delete(file.id);
    files.value = files.value.filter((f) => f.id !== file.id);
    ElMessage.success("已删除");
  } catch { /* cancelled */ }
}
</script>

<style scoped>
.page-header {
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
}
</style>
