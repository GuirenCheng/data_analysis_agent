<template>
  <div class="auth-container">
    <el-card class="auth-card">
      <h2>📝 创建账号</h2>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="0" @submit.prevent="handleRegister">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" size="large" />
        </el-form-item>
        <el-form-item prop="email">
          <el-input v-model="form.email" placeholder="邮箱" size="large" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码（至少8位）" size="large" show-password />
        </el-form-item>
        <el-form-item prop="confirmPassword">
          <el-input v-model="form.confirmPassword" type="password" placeholder="确认密码" size="large" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" :loading="loading" native-type="submit" style="width:100%">
            注 册
          </el-button>
        </el-form-item>
      </el-form>
      <p class="switch-link">
        已有账号？<router-link to="/login">立即登录</router-link>
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

const form = reactive({ username: "", email: "", password: "", confirmPassword: "" });

const validateConfirm = (_rule: any, value: string, callback: any) => {
  if (value !== form.password) callback(new Error("两次密码不一致"));
  else callback();
};

const rules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  email: [
    { required: true, message: "请输入邮箱", trigger: "blur" },
    { type: "email", message: "邮箱格式不正确", trigger: "blur" },
  ],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 8, message: "密码至少8位", trigger: "blur" },
  ],
  confirmPassword: [
    { required: true, message: "请确认密码", trigger: "blur" },
    { validator: validateConfirm, trigger: "blur" },
  ],
};

async function handleRegister() {
  loading.value = true;
  try {
    await authStore.register(form.username, form.email, form.password);
    ElMessage.success("注册成功，请登录");
    router.push("/login");
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
  margin-bottom: 32px;
  color: #1d1e2c;
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
