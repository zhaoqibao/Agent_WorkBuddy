import { defineStore } from 'pinia'

const STORAGE_KEY = 'ewb-theme'

export const useThemeStore = defineStore('theme', {
  state: () => ({
    dark: localStorage.getItem(STORAGE_KEY) === 'dark',
  }),
  actions: {
    apply() {
      document.documentElement.classList.toggle('dark', this.dark)
    },
    toggle() {
      this.dark = !this.dark
      localStorage.setItem(STORAGE_KEY, this.dark ? 'dark' : 'light')
      this.apply()
    },
    init() {
      // 默认跟随系统，未设置过时用系统偏好
      if (localStorage.getItem(STORAGE_KEY) === null) {
        this.dark = window.matchMedia('(prefers-color-scheme: dark)').matches
      }
      this.apply()
    },
  },
})
