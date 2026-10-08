<template>
  <div class="auth-container">
    <el-card class="auth-card">
      <h2>🔬 数据分析智能体</h2>
      <p class="subtitle">企业级 LLM 驱动数据分析平台</p>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="0" @submit.prevent="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" size="large" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" size="large" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" :loading="loading" native-type="submit" style="width:100%">
            登 录
          </el-button>
        </el-form-item>
      </el-form>
      <p class="switch-link">
        还没有账号？<router-link to="/register">立即注册</router-link>
      </p>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { ElMessage } from "element-plus";

const router = useRouter();
const authStore = useAuthStore();
const loading = ref(false);

const form = reactive({ username: "", password: "" });
const rules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
};

async function handleLogin() {
  loading.value = true;
  try {
    const ok = await authStore.login(form.username, form.password);
    if (ok) {
      ElMessage.success("登录成功");
      router.push("/dashboard");
    }
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #1d1e2c 0%, #2d3748 100%);
}
.auth-card {
  width: 420px;
  padding: 20px;
}
.auth-card h2 {
  text-align: center;
  margin-bottom: 4px;
  color: #1d1e2c;
}
.subtitle {
  text-align: center;
  color: #718096;
  font-size: 14px;
  margin-bottom: 32px;
}
.switch-link {
  text-align: center;
  font-size: 14px;
  color: #718096;
}
.switch-link a {
  color: #409eff;
}
</style>
