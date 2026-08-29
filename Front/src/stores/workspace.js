import { defineStore } from 'pinia'
import { workspaceApi } from '@/api'

const KEY = 'ewb-active-workspace'

export const useWorkspaceStore = defineStore('workspace', {
  state: () => ({
    list: [],
    activeId: Number(localStorage.getItem(KEY)) || null,
  }),
  getters: {
    activeWorkspace: (state) => state.list.find((w) => w.id === state.activeId) || null,
  },
  actions: {
    async load() {
      this.list = await workspaceApi.list()
      // 激活的空间被删除时回退到第一个
      if (this.activeId && !this.list.some((w) => w.id === this.activeId)) {
        this.activeId = this.list.length ? this.list[0].id : null
      }
      // 未激活时默认激活第一个
      if (!this.activeId && this.list.length) {
        this.activeId = this.list[0].id
      }
      this.persist()
    },
    setActive(id) {
      this.activeId = id
      this.persist()
    },
    persist() {
      if (this.activeId) localStorage.setItem(KEY, String(this.activeId))
      else localStorage.removeItem(KEY)
    },
  },
})
