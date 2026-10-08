<template>
  <div class="analysis-create">
    <div class="page-header">
      <h2>🆕 新建分析</h2>
    </div>

    <el-card>
      <el-form :model="form" label-width="100px" @submit.prevent="handleSubmit">
        <el-form-item label="分析需求" required>
          <el-input
            v-model="form.query"
            type="textarea"
            :rows="4"
            placeholder="请用自然语言描述您的数据分析需求，例如：基于销售数据，分析近五年的营收趋势并生成可视化图表"
            maxlength="10000"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="数据文件">
          <el-upload
            v-model:file-list="uploadFiles"
            :auto-upload="false"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :limit="5"
            accept=".csv,.xlsx,.xls,.json,.parquet"
            drag
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽文件到此处，或 <em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 CSV / Excel / JSON / Parquet，单个文件不超过 50MB</div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="已上传文件">
          <div v-if="uploadedFiles.length === 0" style="color:#999">暂无已上传文件</div>
          <el-tag
            v-for="f in uploadedFiles"
            :key="f.id"
            closable
            @close="removeUploadedFile(f.id)"
            style="margin-right:8px"
          >
            {{ f.original_name }}
          </el-tag>
          <el-button link type="primary" @click="$router.push('/files')" style="margin-left:8px">
            管理文件 →
          </el-button>
        </el-form-item>

        <el-form-item label="最大轮次">
          <el-slider v-model="form.max_rounds" :min="5" :max="50" show-input style="width:300px" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" size="large" :loading="submitting" @click="handleSubmit">
            <el-icon><VideoPlay /></el-icon> 开始分析
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 提交后自动跳转 -->
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { useAnalysisStore } from "@/stores/analysis";
import { filesApi } from "@/api/files";
import { ElMessage } from "element-plus";
import type { FileOut } from "@/types";
import type { UploadFile } from "element-plus";

const router = useRouter();
const store = useAnalysisStore();
const submitting = ref(false);

const form = reactive({
  query: "",
  max_rounds: 20,
});

const uploadFiles = ref<UploadFile[]>([]);
const uploadedFiles = ref<FileOut[]>([]);

async function handleFileChange(file: UploadFile) {
  if (!file.raw) return;
  try {
    const res = await filesApi.upload(file.raw);
    uploadedFiles.value.push(res.file);
    ElMessage.success(`文件 ${res.file.original_name} 上传成功`);
  } catch {
    // 错误已在拦截器中处理
  }
}

function handleFileRemove(file: UploadFile) {
  const idx = uploadFiles.value.findIndex((f) => f.uid === file.uid);
  if (idx >= 0) uploadFiles.value.splice(idx, 1);
}

function removeUploadedFile(fileId: string) {
  uploadedFiles.value = uploadedFiles.value.filter((f) => f.id !== fileId);
}

async function handleSubmit() {
  if (!form.query.trim()) {
    ElMessage.warning("请输入分析需求");
    return;
  }
  submitting.value = true;
  try {
    const fileIds = uploadedFiles.value.map((f) => f.id);
    const session = await store.createSession(form.query, fileIds, form.max_rounds);
    ElMessage.success("分析任务已创建");
    router.push(`/analysis/${session.id}`);
  } finally {
    submitting.value = false;
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
</style>
