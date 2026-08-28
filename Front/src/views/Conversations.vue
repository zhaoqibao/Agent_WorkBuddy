<template>
  <div class="conv-page">
    <div class="conv-side">
      <div class="side-head">
        <el-select v-model="wsId" placeholder="选择空间" style="width:100%" @change="load">
          <el-option v-for="w in workspaces" :key="w.id" :label="w.name" :value="w.id" />
        </el-select>
        <el-button type="primary" style="width:100%;margin-top:8px" :disabled="!wsId"
          @click="createConversation">新建会话</el-button>
      </div>
      <div class="conv-list">
        <div v-for="c in list" :key="c.id" class="conv-item" :class="{ active: c.id === currentId }"
          @click="openConversation(c)">
          <span class="conv-title">{{ c.title }}</span>
          <el-button link type="danger" size="small" @click.stop="remove(c)">删除</el-button>
        </div>
        <el-empty v-if="!list.length" description="暂无会话" :image-size="60" />
      </div>
    </div>

    <div class="conv-main">
      <template v-if="currentId">
        <div class="chat-box" ref="chatBox">
          <div v-for="(m, i) in messages" :key="i" class="msg" :class="m.role">
            <div class="bubble">{{ m.content }}</div>
          </div>
          <div v-if="sending" class="msg assistant"><div class="bubble">思考中…</div></div>
        </div>
        <div class="chat-input">
          <el-input v-model="input" type="textarea" :rows="3" placeholder="输入消息，回车发送（Shift+回车换行）"
            @keydown.enter.exact.prevent="send" />
          <el-button type="primary" :loading="sending" @click="send" style="margin-top:8px">
            发送
          </el-button>
        </div>
      </template>
      <el-empty v-else description="选择或新建一个会话开始对话" />
    </div>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { conversationApi, workspaceApi } from '@/api'

const workspaces = ref([])
const wsId = ref(null)
const list = ref([])
const currentId = ref(null)
const messages = ref([])
const input = ref('')
const sending = ref(false)
const chatBox = ref(null)

async function loadWorkspaces() {
  workspaces.value = await workspaceApi.list()
  if (!wsId.value && workspaces.value.length) wsId.value = workspaces.value[0].id
}

async function load() {
  if (!wsId.value) return
  list.value = await conversationApi.list(wsId.value)
}

async function createConversation() {
  const c = await conversationApi.create({ workspace_id: wsId.value, title: '新会话' })
  list.value.unshift(c)
  openConversation(c)
}

async function openConversation(c) {
  currentId.value = c.id
  const data = await conversationApi.detail(c.id)
  messages.value = data.messages || []
  scrollBottom()
}

async function send() {
  const text = input.value.trim()
  if (!text) return
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  sending.value = true
  scrollBottom()
  try {
    const res = await conversationApi.send(currentId.value, { content: text })
    messages.value.push({ role: 'assistant', content: res.content })
  } finally {
    sending.value = false
    scrollBottom()
  }
}

async function remove(c) {
  await ElMessageBox.confirm(`确定删除会话「${c.title}」吗？`, '提示', { type: 'warning' })
  await conversationApi.remove(c.id)
  if (currentId.value === c.id) {
    currentId.value = null
    messages.value = []
  }
  ElMessage.success('已删除')
  load()
}

async function scrollBottom() {
  await nextTick()
  if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight
}

onMounted(async () => {
  await loadWorkspaces()
  await load()
})
</script>

<style scoped>
.conv-page { display: flex; height: calc(100vh - 40px); gap: 12px; }
.conv-side { width: 260px; border-right: 1px solid #eee; display: flex; flex-direction: column; }
.side-head { padding: 8px; }
.conv-list { flex: 1; overflow-y: auto; padding: 8px; }
.conv-item { display: flex; justify-content: space-between; align-items: center; padding: 10px;
  border-radius: 6px; cursor: pointer; }
.conv-item:hover { background: #f5f7fa; }
.conv-item.active { background: #ecf5ff; }
.conv-title { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.conv-main { flex: 1; display: flex; flex-direction: column; }
.chat-box { flex: 1; overflow-y: auto; padding: 16px; }
.msg { display: flex; margin-bottom: 12px; }
.msg.user { justify-content: flex-end; }
.bubble { max-width: 70%; padding: 10px 14px; border-radius: 10px; background: #f0f2f5; line-height: 1.6; }
.msg.user .bubble { background: #409eff; color: #fff; }
.chat-input { padding: 12px; border-top: 1px solid #eee; }
</style>
