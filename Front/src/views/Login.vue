<template>
  <div class="login-wrap">
    <div class="theme-fab">
      <el-button circle @click="theme.toggle()">
        <el-icon><Sunny v-if="theme.dark" /><Moon v-else /></el-icon>
      </el-button>
    </div>

    <el-card class="login-card" shadow="always">
      <div class="brand">
        <div class="brand-mark">W</div>
        <h2>Easy WorkBuddy</h2>
        <p>轻量智能体工作台</p>
      </div>
      <el-tabs v-model="mode" class="login-tabs" stretch>
        <el-tab-pane label="登录" name="login" />
        <el-tab-pane label="注册" name="register" />
      </el-tabs>

      <!-- 登录表单 -->
      <el-form v-if="mode === 'login'" ref="loginFormRef" :model="loginForm" :rules="loginRules"
        @submit.prevent="submit">
        <el-form-item prop="account">
          <el-input v-model="loginForm.account" placeholder="用户名或邮箱" size="large" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="loginForm.password" type="password" placeholder="密码" size="large" show-password />
        </el-form-item>
        <el-button type="primary" size="large" class="submit" :loading="loading" @click="submit">登录</el-button>
      </el-form>

      <!-- 注册表单 -->
      <el-form v-else ref="registerFormRef" :model="registerForm" :rules="registerRules"
        @submit.prevent="submit">
        <el-form-item prop="username">
          <el-input v-model="registerForm.username" placeholder="用户名" size="large" />
        </el-form-item>
        <el-form-item prop="email">
          <el-input v-model="registerForm.email" placeholder="邮箱" size="large" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="registerForm.password" type="password" placeholder="密码（6-10 位）" size="large" show-password />
        </el-form-item>
        <el-button type="primary" size="large" class="submit" :loading="loading" @click="submit">注册</el-button>
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
import { useThemeStore } from '@/stores/theme'

const router = useRouter()
const auth = useAuthStore()
const theme = useThemeStore()
const mode = ref('login')
const loading = ref(false)

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
  try {
    await formRef.validate()
  } catch {
    ElMessage.warning('请检查输入内容')
    return
  }

  loading.value = true
  try {
    if (isLogin) {
      const data = await authApi.login({ account: loginForm.account, password: loginForm.password })
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
      const data = await authApi.login({ account: registerForm.username, password: registerForm.password })
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
.login-wrap {
  display: flex; justify-content: center; align-items: center; height: 100vh;
  background: radial-gradient(1200px 600px at 20% -10%, var(--primary-soft), transparent),
    radial-gradient(1000px 600px at 110% 110%, rgba(124, 77, 255, 0.12), transparent),
    var(--bg);
}
.theme-fab { position: absolute; top: 20px; right: 24px; }
.theme-fab .el-button { font-size: 18px; background: var(--card-bg); border: 1px solid var(--border); color: var(--text); }
.login-card {
  width: 400px; padding: 28px 32px 24px; border-radius: 20px; border: 1px solid var(--border);
  background: var(--card-bg);
}
.brand { text-align: center; margin-bottom: 8px; }
.brand-mark { width: 52px; height: 52px; margin: 0 auto 12px; border-radius: 14px;
  background: linear-gradient(135deg, #409eff, #7c4dff); color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 26px; font-weight: 700; }
.brand h2 { margin: 0 0 4px; font-size: 22px; }
.brand p { margin: 0; color: var(--muted); font-size: 13px; }
.login-tabs { margin-bottom: 8px; }
.submit { width: 100%; border-radius: 10px; margin-top: 4px; }
</style>
