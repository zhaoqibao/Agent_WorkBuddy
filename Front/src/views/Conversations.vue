<template>
  <div class="conv-page">
    <div class="conv-side">
      <div class="side-head">
        <el-button type="primary" class="new-btn" :disabled="!store.activeId" @click="openCreate">
          新建会话
        </el-button>
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
            <div class="msg-body">
              <div v-if="m.tools?.length && !m.images?.length" class="tool-badges">
                <span v-for="(t, ti) in m.tools" :key="ti" class="tool-badge">
                  {{ t.status === 'running' ? '🔧 调用' : '✅' }} {{ t.name }}
                </span>
              </div>
              <div class="bubble" v-if="displayText(m)">{{ displayText(m) }}</div>
              <div class="bubble typing" v-else-if="m.typing"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>

              <!-- 图片生成结果：悬挂展示 + 下载 -->
              <div v-if="m.images?.length" class="msg-images">
                <div v-for="(img, ii) in m.images" :key="ii" class="img-card">
                  <img :src="img" class="gen-img" alt="生成图片" />
                  <a class="download-btn" :href="img" download="image.png" target="_blank">
                    <el-icon><Download /></el-icon> 下载
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 底部输入区：固定不被消息撑走 -->
        <div class="chat-input">
          <div class="input-box">
            <div v-if="attachment" class="attach-chip">
              <el-icon><Paperclip /></el-icon>
              <span class="name">{{ attachment.name }}</span>
              <span class="close" @click="attachment = null">×</span>
            </div>
            <el-input
              v-model="input"
              type="textarea"
              :rows="3"
              :autosize="{ minRows: 3, maxRows: 8 }"
              placeholder="给 Easy WorkBuddy 发送消息"
              class="msg-textarea"
              @keydown.enter.exact.prevent="send"
            />
            <div class="input-toolbar">
              <div class="left-tools">
                <el-tooltip content="让 Agent 逐步、深入地推理后再回答" placement="top">
                  <span class="tool-chip" :class="{ active: deepThink }" @click="deepThink = !deepThink">
                    <el-icon><MagicStick /></el-icon> 深度思考
                  </span>
                </el-tooltip>
                <el-tooltip content="优先使用搜索/新闻工具获取实时信息" placement="top">
                  <span class="tool-chip" :class="{ active: webSearch }" @click="webSearch = !webSearch">
                    <el-icon><Search /></el-icon> 智能搜索
                  </span>
                </el-tooltip>
                <el-tooltip content="上传文档到资料库，可附带发送给 Agent" placement="top">
                  <span class="tool-chip" :class="{ disabled: !wsId }" @click="triggerFile">
                    <el-icon><Upload /></el-icon> 上传文档
                  </span>
                </el-tooltip>
                <input ref="fileInput" type="file" hidden
                  accept=".docx,.xlsx,.pdf,.txt,.md,.csv" @change="onFileChange" />
              </div>
              <button class="send-btn" :class="{ disabled: !canSend }" :disabled="!canSend" @click="send">
                <el-icon><Promotion /></el-icon>
              </button>
            </div>
          </div>
          <div class="input-hint">
            <span class="hint-label">可用工具</span>
            <span class="hint-tag">天气查询</span>
            <span class="hint-tag">新闻搜索</span>
            <span class="hint-tag">文档读取</span>
            <span class="hint-tag">文档转换</span>
            <span class="hint-tag">图片识别</span>
            <span class="hint-tag">图片生成</span>
          </div>
        </div>
      </template>
      <el-empty v-else description="选择或新建一个会话开始对话" />
    </div>

    <!-- 新建会话 -->
    <el-dialog v-model="createVisible" title="新建会话" width="440px">
      <el-form label-width="72px">
        <el-form-item label="标题">
          <el-input v-model="createForm.title" placeholder="可选，默认用 Agent 名" />
        </el-form-item>
        <el-form-item label="Agent">
          <el-select v-model="createForm.agent_id" placeholder="选择 Agent" clearable style="width:100%">
            <el-option v-for="a in agents" :key="a.id" :label="a.name" :value="a.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" @click="doCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { agentApi, conversationApi, documentApi, streamChat } from '@/api'
import { useWorkspaceStore } from '@/stores/workspace'

const store = useWorkspaceStore()
const agents = ref([])
const list = ref([])
const currentId = ref(null)
const messages = ref([])
const input = ref('')
const sending = ref(false)
const chatBox = ref(null)
const createVisible = ref(false)
const createForm = reactive({ title: '', agent_id: null })

const deepThink = ref(false)
const webSearch = ref(false)
const attachment = ref(null)
const fileInput = ref(null)

const canSend = computed(() => (!!input.value.trim() || !!attachment.value) && !sending.value)

async function loadAgents() {
  agents.value = await agentApi.list()
}

async function load() {
  if (!store.activeId) return
  list.value = await conversationApi.list(store.activeId)
  // 按更新时间降序，最近的会话排在最前
  list.value.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
}

function openCreate() {
  createForm.title = ''
  createForm.agent_id = null
  createVisible.value = true
}

async function doCreate() {
  const body = { workspace_id: store.activeId, agent_id: createForm.agent_id || null }
  if (createForm.title) body.title = createForm.title
  const c = await conversationApi.create(body)
  createVisible.value = false
  list.value.unshift(c)
  openConversation(c)
}

async function openConversation(c) {
  currentId.value = c.id
  const data = await conversationApi.detail(c.id)
  messages.value = (data.messages || []).map((m) => ({ role: m.role, content: m.content }))
  scrollBottom(true)
}

function triggerFile() {
  if (!store.activeId) return ElMessage.warning('请先到「工作空间」页激活一个空间')
  fileInput.value?.click()
}

async function onFileChange(e) {
  const f = e.target.files?.[0]
  if (!f) return
  try {
    const fd = new FormData()
    fd.append('file', f)
    if (store.activeId) fd.append('workspace_id', store.activeId)
    const doc = await documentApi.upload(fd)
    attachment.value = { name: doc.original_name, id: doc.id }
    ElMessage.success('文件已上传，可附带发送')
  } catch {
    ElMessage.error('上传失败')
  } finally {
    e.target.value = ''
  }
}

function buildContent(text) {
  const prefixes = []
  if (webSearch.value) prefixes.push('[请优先使用搜索/新闻工具获取实时信息]')
  if (deepThink.value) prefixes.push('[请逐步、深入地思考后回答]')
  if (attachment.value) {
    prefixes.push(`[用户上传了附件：${attachment.value.name}，document_id=${attachment.value.id}]`)
  }
  return prefixes.length ? prefixes.join('\n') + '\n\n' + text : text
}

// 展示文本：若消息附带图片，则过滤掉 URL/base64 地址，只保留描述文本
function displayText(m) {
  let t = m.content || ''
  if (m.images?.length) {
    t = t.replace(/https?:\/\/[^\s"'<>]+/g, '')
    t = t.replace(/data:image\/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=]+/g, '')
    t = t.replace(/!\[[^\]]*\]\([^)]*\)/g, '')
    t = t.replace(/\n{3,}/g, '\n\n').trim()
  }
  return t
}

function handleEvent(evt, msg) {
  if (evt.type === 'token') {
    msg.typing = false
    msg.content += evt.content
  } else if (evt.type === 'tool') {
    msg.tools.push({ name: evt.name, status: 'running' })
  } else if (evt.type === 'tool_result') {
    const t = msg.tools.find((x) => x.name === evt.name && x.status === 'running')
    if (t) t.status = 'done'
    if (evt.data?.image) {
      if (!msg.images) msg.images = []
      msg.images.push(evt.data.image)
    } else if (evt.name === 'generate_image' && evt.result) {
      // 兼容旧后端：从文本结果解析图片 URL
      const m = evt.result.match(/https?:\/\/[^\s"']+/)
      if (m) {
        if (!msg.images) msg.images = []
        msg.images.push(m[0])
      }
    }
  } else if (evt.type === 'done') {
    msg.typing = false
    if (evt.content) msg.content = evt.content
  } else if (evt.type === 'error') {
    msg.typing = false
    if (!msg.content) msg.content = `⚠️ ${evt.message}`
  }
  scrollBottom()
}

async function send() {
  const text = input.value.trim()
  if (!canSend.value) return
  const content = buildContent(text)
  messages.value.push({ role: 'user', content: text || `[附件] ${attachment.value?.name}` })
  input.value = ''
  attachment.value = null
  sending.value = true
  const assistantMsg = reactive({ role: 'assistant', content: '', typing: true, tools: [], images: [] })
  messages.value.push(assistantMsg)
  scrollBottom(true)

  try {
    const resp = await streamChat(currentId.value, content)
    if (!resp.ok) {
      assistantMsg.typing = false
      assistantMsg.content = '请求失败，请稍后重试'
      return
    }
    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop()
      for (const part of parts) {
        const line = part.trim()
        if (!line.startsWith('data:')) continue
        try { handleEvent(JSON.parse(line.slice(5).trim()), assistantMsg) } catch { /* ignore */ }
      }
    }
  } finally {
    sending.value = false
    assistantMsg.typing = false
    scrollBottom(true)
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

// 智能滚动：仅当用户接近底部时才跟随滚动，避免流式输出时页面抖动
let scrollRaf = null
function scrollBottom(force = false) {
  if (scrollRaf) return
  scrollRaf = requestAnimationFrame(() => {
    scrollRaf = null
    const el = chatBox.value
    if (!el) return
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80
    if (force || nearBottom) {
      el.scrollTop = el.scrollHeight
    }
  })
}

onMounted(async () => {
  await store.load()
  await loadAgents()
  await load()
  // 自动恢复最近的会话历史
  if (!currentId.value && list.value.length) {
    await openConversation(list.value[0])
  }
})
</script>

<style scoped>
.conv-page { display: flex; height: calc(100vh - 40px); gap: 16px; }
.conv-side { width: 260px; display: flex; flex-direction: column; }
.side-head { padding: 4px 0 12px; display: flex; flex-direction: column; gap: 8px; }
.conv-list { flex: 1; overflow-y: auto; }
.conv-item { display: flex; justify-content: space-between; align-items: center; padding: 12px 14px;
  border-radius: 12px; cursor: pointer; margin-bottom: 4px; }
.conv-item:hover { background: var(--hover-bg); }
.conv-item.active { background: var(--active-bg); }
.conv-title { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.conv-main { flex: 1; display: flex; flex-direction: column; min-height: 0; }
.chat-box { flex: 1; overflow-y: auto; padding: 20px; min-height: 0; }
.msg { display: flex; margin-bottom: 16px; }
.msg.user { justify-content: flex-end; }
.msg-body { max-width: 76%; display: flex; flex-direction: column; align-items: flex-start; }
.msg.user .msg-body { align-items: flex-end; }
.bubble { padding: 12px 16px; border-radius: 16px; background: var(--bubble-bg); line-height: 1.7;
  white-space: pre-wrap; word-break: break-word; }
.msg.user .bubble { background: var(--primary); color: #fff; border-bottom-right-radius: 4px; }
.msg.assistant .bubble { border-bottom-left-radius: 4px; }
.tool-badges { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.tool-badge { font-size: 12px; padding: 4px 10px; border-radius: 999px; background: var(--tool-bg); color: var(--tool-text); }

/* 生成图片卡片 + 下载 */
.msg-images { display: flex; flex-direction: column; gap: 10px; margin-top: 8px; }
.img-card { border-radius: 14px; overflow: hidden; border: 1px solid var(--border); background: var(--card-bg); }
.gen-img { display: block; width: 100%; max-width: 360px; height: auto; }
.download-btn { display: inline-flex; align-items: center; gap: 4px; padding: 6px 12px; margin: 8px;
  border-radius: 8px; background: var(--primary); color: #fff; font-size: 13px; text-decoration: none; }
.download-btn:hover { opacity: 0.9; }

/* ===== 输入区：圆角高级感卡片，固定在底部 ===== */
.chat-input { padding: 8px 20px 16px; flex-shrink: 0; }
.input-box {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 22px;
  padding: 12px 16px 10px;
  box-shadow: var(--shadow);
  transition: border-color 0.2s, box-shadow 0.2s;
}
.input-box:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-soft), var(--shadow);
}
html.dark .input-box {
  border-color: #383d4a;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.45);
  background: #1d2029;
}
html.dark .input-box:focus-within {
  border-color: #5b8dff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.15), 0 4px 24px rgba(0, 0, 0, 0.45);
}
.attach-chip { display: inline-flex; align-items: center; gap: 6px; padding: 5px 10px;
  background: var(--primary-soft); color: var(--primary); border-radius: 999px;
  font-size: 13px; margin-bottom: 8px; }
.attach-chip .name { max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.attach-chip .close { cursor: pointer; opacity: 0.6; font-size: 16px; line-height: 1; padding: 0 2px; }
.attach-chip .close:hover { opacity: 1; }

/* textarea 透明无边框，融入卡片 */
.msg-textarea :deep(.el-textarea__inner) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 4px 2px;
  resize: none;
  color: var(--text);
}
.msg-textarea :deep(.el-textarea__inner::placeholder) { color: var(--muted); }

.input-toolbar { display: flex; justify-content: space-between; align-items: center; margin-top: 8px; }
.left-tools { display: flex; gap: 8px; flex-wrap: wrap; }
.tool-chip { display: inline-flex; align-items: center; gap: 4px; padding: 6px 12px;
  border-radius: 999px; background: var(--bg-soft); color: var(--text); cursor: pointer;
  font-size: 13px; border: 1px solid transparent; user-select: none; transition: all 0.2s; }
.tool-chip:hover { background: var(--hover-bg); }
.tool-chip.active { background: var(--primary-soft); color: var(--primary); border-color: var(--primary); }
.tool-chip.disabled { opacity: 0.5; cursor: not-allowed; }

.send-btn { width: 40px; height: 40px; border-radius: 50%; border: none; cursor: pointer;
  display: flex; align-items: center; justify-content: center; color: #fff;
  background: linear-gradient(135deg, #409eff, #7c4dff); font-size: 18px;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.35); transition: all 0.2s; }
.send-btn:hover:not(.disabled) { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(64, 158, 255, 0.5); }
.send-btn.disabled { opacity: 0.5; cursor: not-allowed; box-shadow: none; }

/* 可用工具 tag：靠左对齐 */
.input-hint { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-top: 10px;
  justify-content: flex-start; }
.hint-label { font-size: 12px; color: var(--muted); }
.hint-tag { font-size: 11px; padding: 2px 10px; border-radius: 999px; background: var(--bg-soft);
  color: var(--muted); border: 1px solid var(--border); }

.typing { display: inline-flex; gap: 4px; padding: 16px; }
.dot { width: 7px; height: 7px; border-radius: 50%; background: var(--muted); animation: blink 1.2s infinite; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0%, 80%, 100% { opacity: 0.3; } 40% { opacity: 1; } }
</style>
