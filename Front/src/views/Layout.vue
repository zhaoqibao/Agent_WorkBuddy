<template>
  <el-container class="layout">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <div class="logo-mark">W</div>
        <span class="logo-text">Easy WorkBuddy</span>
      </div>
      <el-menu :default-active="active" router class="menu">
        <el-menu-item index="/workspaces"><el-icon><Folder /></el-icon><span>工作空间</span></el-menu-item>
        <el-menu-item index="/tasks"><el-icon><List /></el-icon><span>任务</span></el-menu-item>
        <el-menu-item index="/agents"><el-icon><MagicStick /></el-icon><span>Agent</span></el-menu-item>
        <el-menu-item index="/conversations"><el-icon><ChatDotRound /></el-icon><span>会话</span></el-menu-item>
        <el-menu-item index="/knowledge"><el-icon><Files /></el-icon><span>资料库</span></el-menu-item>
        <el-menu-item index="/profile"><el-icon><User /></el-icon><span>个人信息</span></el-menu-item>
      </el-menu>
      <div class="sidebar-footer">
        <span>主题切换</span>
        <el-button class="theme-btn" text @click="theme.toggle()">
          <el-icon><Sunny v-if="theme.dark" /><Moon v-else /></el-icon>
        </el-button>
        <div class="user">
          <div class="avatar">{{ (auth.user?.username || '?').slice(0, 1) }}</div>
          <span class="uname">{{ auth.user?.username || '未登录' }}</span>
          <el-button text type="danger" size="small" @click="logout">退出</el-button>
        </div>
      </div>
    </el-aside>
    <el-main class="main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const theme = useThemeStore()
const active = computed(() => route.path)

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout { height: 100vh; background: var(--bg); }
.sidebar { background: var(--card-bg); border-right: 1px solid var(--border); display: flex; flex-direction: column; }
.logo { display: flex; align-items: center; gap: 10px; padding: 20px 18px; }
.logo-mark { width: 34px; height: 34px; border-radius: 10px; background: linear-gradient(135deg, #409eff, #7c4dff);
  color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 18px; }
.logo-text { font-weight: 700; font-size: 16px; }
.menu { flex: 1; border-right: none; padding: 8px 12px; background: transparent; }
.menu :deep(.el-menu-item) { border-radius: 10px; margin-bottom: 4px; height: 44px; }
.menu :deep(.el-menu-item.is-active) { background: var(--primary-soft); color: var(--primary); font-weight: 600; }
.menu :deep(.el-menu-item:hover) { background: var(--hover-bg); }
.sidebar-footer { padding: 14px 16px; border-top: 1px solid var(--border); }
.theme-btn { font-size: 14px; height: 34px; padding: 0 12px; display: inline-flex; align-items: center; gap: 5px; color: var(--text); }
.theme-btn .el-icon { font-size: 16px; }
.user { display: flex; align-items: center; gap: 8px; margin-top: 8px; }
.avatar { width: 30px; height: 30px; border-radius: 50%; background: var(--primary); color: #fff;
  display: flex; align-items: center; justify-content: center; font-weight: 600; }
.uname { flex: 1; font-size: 13px; color: var(--muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.main { padding: 20px; background: var(--bg); overflow-y: auto; }
</style>
