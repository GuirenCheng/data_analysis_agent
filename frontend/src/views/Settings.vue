<template>
  <div class="settings-page">
    <div class="page-header">
      <h2>⚙️ 系统配置</h2>
    </div>

    <el-card v-loading="loading">
      <el-form :model="form" label-width="140px">
        <el-divider content-position="left">LLM 配置</el-divider>
        <el-form-item label="模型提供商">
          <el-select v-model="form.llm_provider" style="width:240px">
            <el-option label="OpenAI" value="openai" />
            <el-option label="OpenAI 兼容" value="openai_compatible" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型名称">
          <el-input v-model="form.llm_model" placeholder="如 gpt-4-turbo-preview" style="width:300px" />
        </el-form-item>
        <el-form-item label="API Base URL">
          <el-input v-model="form.llm_base_url" placeholder="https://api.openai.com/v1" style="width:400px" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="form.llm_api_key" type="password" show-password placeholder="留空不修改" style="width:400px" />
        </el-form-item>
        <el-form-item label="Temperature">
          <el-slider v-model="form.temperature" :min="0" :max="2" :step="0.05" show-input style="width:300px" />
        </el-form-item>
        <el-form-item label="Max Tokens">
          <el-input-number v-model="form.max_tokens" :min="100" :max="128000" :step="1000" />
        </el-form-item>

        <el-divider content-position="left">分析默认值</el-divider>
        <el-form-item label="默认最大轮次">
          <el-input-number v-model="form.default_max_rounds" :min="5" :max="50" />
        </el-form-item>
        <el-form-item label="默认输出目录">
          <el-input v-model="form.default_output_dir" style="width:300px" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="saveConfig">保存配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from "vue";
import { configsApi } from "@/api/configs";
import { ElMessage } from "element-plus";
import type { UserConfig } from "@/types";

const loading = ref(false);
const saving = ref(false);

interface ConfigForm extends Partial<UserConfig> {
  llm_api_key?: string;
}

const form = reactive<ConfigForm>({
  llm_provider: "openai",
  llm_model: "",
  llm_base_url: "",
  llm_api_key: "",
  temperature: 0.1,
  max_tokens: 16384,
  default_max_rounds: 20,
  default_output_dir: "outputs",
});

onMounted(async () => {
  loading.value = true;
  try {
    const cfg = await configsApi.get();
    Object.assign(form, {
      llm_provider: cfg.llm_provider,
      llm_model: cfg.llm_model,
      llm_base_url: cfg.llm_base_url || "",
      temperature: cfg.temperature,
      max_tokens: cfg.max_tokens,
      default_max_rounds: cfg.default_max_rounds,
      default_output_dir: cfg.default_output_dir,
    });
  } finally {
    loading.value = false;
  }
});

async function saveConfig() {
  saving.value = true;
  try {
    await configsApi.update({
      llm_provider: form.llm_provider,
      llm_model: form.llm_model,
      llm_base_url: form.llm_base_url || undefined,
      llm_api_key: form.llm_api_key || undefined,
      temperature: form.temperature,
      max_tokens: form.max_tokens,
      default_max_rounds: form.default_max_rounds,
      default_output_dir: form.default_output_dir,
    });
    ElMessage.success("配置已保存");
  } finally {
    saving.value = false;
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
