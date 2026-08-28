<template>
  <div class="login-wrap">
    <el-card class="login-card">
      <h2 style="text-align:center;margin-bottom:8px">Easy WorkBuddy</h2>
      <p style="text-align:center;color:#888;margin-bottom:20px">轻量智能体工作台</p>
      <el-tabs v-model="mode">
        <el-tab-pane label="登录" name="login" />
        <el-tab-pane label="注册" name="register" />
      </el-tabs>

      <!-- 登录表单 -->
      <el-form v-if="mode === 'login'" ref="loginFormRef" :model="loginForm" :rules="loginRules"
        @submit.prevent="submit">
        <el-form-item prop="account">
          <el-input v-model="loginForm.account" placeholder="用户名或邮箱" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="loginForm.password" type="password" placeholder="密码" show-password />
        </el-form-item>
        <el-button type="primary" style="width:100%" :loading="loading" @click="submit">登录</el-button>
      </el-form>

      <!-- 注册表单 -->
      <el-form v-else ref="registerFormRef" :model="registerForm" :rules="registerRules"
        @submit.prevent="submit">
        <el-form-item prop="username">
          <el-input v-model="registerForm.username" placeholder="用户名" />
        </el-form-item>
        <el-form-item prop="email">
          <el-input v-model="registerForm.email" placeholder="邮箱" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="registerForm.password" type="password" placeholder="密码（6-10 位）" show-password />
        </el-form-item>
        <el-button type="primary" style="width:100%" :loading="loading" @click="submit">注册</el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const mode = ref('login')
const loading = ref(false)

// 登录 / 注册数据完全独立，互不影响
const loginFormRef = ref()
const registerFormRef = ref()
const loginForm = reactive({ account: '', password: '' })
const registerForm = reactive({ username: '', email: '', password: '' })

const loginRules = {
  account: [{ required: true, message: '请输入用户名或邮箱', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const registerRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 10, message: '密码长度需为 6-10 位', trigger: 'blur' },
  ],
}

async function submit() {
  const isLogin = mode.value === 'login'
  const formRef = isLogin ? loginFormRef.value : registerFormRef.value

  // 先做前端校验（失焦时已提示，这里提交前兜底拦截）
  try {
    await formRef.validate()
  } catch {
    ElMessage.warning('请检查输入内容')
    return
  }

  loading.value = true
  try {
    if (isLogin) {
      const data = await authApi.login({
        account: loginForm.account,
        password: loginForm.password,
      })
      auth.setSession(data.access_token, null)
      const me = await authApi.me()
      auth.setSession(data.access_token, me)
      router.push('/')
    } else {
      await authApi.register({
        username: registerForm.username,
        email: registerForm.email,
        password: registerForm.password,
      })
      const data = await authApi.login({
        account: registerForm.username,
        password: registerForm.password,
      })
      auth.setSession(data.access_token, null)
      const me = await authApi.me()
      auth.setSession(data.access_token, me)
      router.push('/')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrap { display:flex; justify-content:center; align-items:center; height:100vh; }
.login-card { width: 360px; padding: 8px 8px 16px; }
</style>
