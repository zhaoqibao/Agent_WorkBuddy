<template>
  <el-container style="height:100vh">
    <el-aside width="200px" style="background:#fff;border-right:1px solid #eee">
      <div class="logo">Easy WorkBuddy</div>
      <el-menu :default-active="active" router>
        <el-menu-item index="/workspaces"><el-icon><Folder /></el-icon>工作空间</el-menu-item>
        <el-menu-item index="/tasks"><el-icon><List /></el-icon>任务</el-menu-item>
        <el-menu-item index="/conversations"><el-icon><ChatDotRound /></el-icon>会话</el-menu-item>
        <el-menu-item index="/knowledge"><el-icon><Files /></el-icon>资料库</el-menu-item>
        <el-menu-item index="/profile"><el-icon><User /></el-icon>个人信息</el-menu-item>
      </el-menu>
      <div class="footer">
        <span>{{ auth.user?.username || '未登录' }}</span>
        <el-button text type="danger" @click="logout">退出</el-button>
      </div>
    </el-aside>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const active = computed(() => route.path)

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.logo { font-weight:600; padding:16px; border-bottom:1px solid #eee; }
.footer { position:absolute; bottom:12px; width:200px; padding:0 16px; display:flex; justify-content:space-between; align-items:center; }
</style>
