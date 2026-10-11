<template>
  <div class="settings-page">
    <div class="page-header">
      <h2>⚙️ 系统配置</h2>
    </div>

    <el-card v-loading="loading">
      <el-form :model="form" label-width="140px">
        <el-divider content-position="left">LLM 配置</el-divider>
        <el-form-item label="使用自定义模型">
          <el-switch v-model="form.use_custom_llm" active-text="启用" inactive-text="关闭" />
          <div class="field-hint">
            开启后，分析任务将使用下方配置的模型与接口；关闭则使用服务器全局默认配置（.env）
          </div>
        </el-form-item>
        <el-form-item label="模型提供商">
          <el-select v-model="form.llm_provider" style="width:300px" :disabled="!form.use_custom_llm" @change="onProviderChange">
            <el-option
              v-for="p in LLM_PRESETS"
              :key="p.key"
              :label="p.label"
              :value="p.key"
            />
          </el-select>
          <div class="field-hint">选择提供商后会自动填好接口地址和常用模型，无需手动输入</div>
        </el-form-item>
        <el-form-item label="模型名称">
          <el-select
            v-model="form.llm_model"
            filterable
            allow-create
            default-first-option
            placeholder="选择常用模型，或直接输入自定义名称"
            style="width:400px"
            :disabled="!form.use_custom_llm"
          >
            <el-option v-for="m in modelOptions" :key="m" :label="m" :value="m" />
          </el-select>
        </el-form-item>
        <el-form-item label="API Base URL">
          <el-input v-model="form.llm_base_url" placeholder="https://api.openai.com/v1" style="width:400px" :disabled="!form.use_custom_llm" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="form.llm_api_key" type="password" show-password placeholder="留空不修改" style="width:400px" :disabled="!form.use_custom_llm" />
        </el-form-item>
        <el-form-item label="Temperature">
          <el-slider v-model="form.temperature" :min="0" :max="2" :step="0.05" show-input style="width:300px" :disabled="!form.use_custom_llm" />
          <div class="field-hint">数值越低回答越稳定，越高越有创意（范围 0–2）</div>
        </el-form-item>
        <el-form-item label="Max Tokens">
          <el-input-number v-model="form.max_tokens" :min="100" :max="128000" :step="1000" :disabled="!form.use_custom_llm" />
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
import { computed, reactive, ref, onMounted } from "vue";
import { configsApi } from "@/api/configs";
import { ElMessage } from "element-plus";
import type { UserConfig } from "@/types";
import { LLM_PRESETS, getPreset, normalizeProviderKey } from "@/config/llmPresets";

const loading = ref(false);
const saving = ref(false);

interface ConfigForm extends Partial<UserConfig> {
  llm_api_key?: string;
}

const form = reactive<ConfigForm>({
  use_custom_llm: false,
  llm_provider: "deepseek",
  llm_model: "",
  llm_base_url: "",
  llm_api_key: "",
  temperature: 0.1,
  max_tokens: 16384,
  default_max_rounds: 20,
  default_output_dir: "outputs",
});

const currentPreset = computed(() => getPreset(form.llm_provider ?? "custom"));
const modelOptions = computed(() => currentPreset.value?.models ?? []);

function onProviderChange(key: string) {
  const preset = getPreset(key);
  if (preset) {
    form.llm_base_url = preset.baseUrl;
    form.llm_model = preset.models[0] ?? "";
  }
}

onMounted(async () => {
  loading.value = true;
  try {
    const cfg = await configsApi.get();
    const providerKey = normalizeProviderKey(cfg.llm_provider);
    const preset = getPreset(providerKey);
    Object.assign(form, {
      use_custom_llm: cfg.use_custom_llm,
      llm_provider: providerKey,
      llm_model: cfg.llm_model,
      llm_base_url: cfg.llm_base_url || preset?.baseUrl || "",
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
      use_custom_llm: form.use_custom_llm,
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
.field-hint {
  width: 100%;
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}
</style>
