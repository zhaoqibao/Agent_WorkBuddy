import { defineStore } from 'pinia'
import { taskApi } from '@/api'

export const useTaskStore = defineStore('task', {
  state: () => ({
    urgentCount: 0,
  }),
  actions: {
    async refresh(workspaceId) {
      try {
        const data = await taskApi.stats(workspaceId)
        this.urgentCount = data.urgent_count || 0
      } catch {
        /* 忽略统计失败 */
      }
    },
  },
})
