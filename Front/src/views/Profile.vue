<template>
  <div class="profile-page">
    <el-card class="profile-card">
      <template #header><b>个人信息</b></template>
      <el-form :model="form" label-width="88px">
        <el-form-item label="用户名">
          <el-input :model-value="user?.username" disabled />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input :model-value="user?.email" disabled />
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="form.nickname" />
        </el-form-item>
        <el-form-item label="手机">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="form.bio" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="saveProfile">保存资料</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="profile-card">
      <template #header><b>修改密码</b></template>
      <el-form :model="pwd" label-width="88px">
        <el-form-item label="原密码">
          <el-input v-model="pwd.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwd.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="warning" :loading="changing" @click="changePassword">修改密码</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const user = ref(auth.user)
const saving = ref(false)
const changing = ref(false)
const form = reactive({ nickname: '', phone: '', bio: '' })
const pwd = reactive({ old_password: '', new_password: '' })

async function load() {
  const me = await authApi.me()
  auth.user = me
  localStorage.setItem('user', JSON.stringify(me))
  user.value = me
  const profile = await authApi.profile()
  Object.assign(form, {
    nickname: profile.nickname || '',
    phone: profile.phone || '',
    bio: profile.bio || '',
  })
}

async function saveProfile() {
  saving.value = true
  try {
    await authApi.updateProfile({ nickname: form.nickname, phone: form.phone, bio: form.bio })
    ElMessage.success('已保存')
  } finally {
    saving.value = false
  }
}

async function changePassword() {
  if (pwd.new_password.length < 6) return ElMessage.warning('新密码至少 6 位')
  changing.value = true
  try {
    await authApi.changePassword({ old_password: pwd.old_password, new_password: pwd.new_password })
    ElMessage.success('密码已修改')
    pwd.old_password = ''
    pwd.new_password = ''
  } finally {
    changing.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.profile-page { max-width: 560px; }
.profile-card { margin-bottom: 16px; }
</style>
