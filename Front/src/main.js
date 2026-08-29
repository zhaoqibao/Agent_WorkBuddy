import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import { useThemeStore } from './stores/theme'
import './style.css'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(ElementPlus)
for (const [key, comp] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, comp)
}

// 初始化主题（浅色/深色）
useThemeStore(pinia).init()

app.mount('#app')
