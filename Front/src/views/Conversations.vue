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
              <!-- 用户消息：真实展示引用的图片 / 文档 -->
              <div v-if="m.role === 'user' && (m.refs?.length || m.attachment)" class="user-attachments">
                <div v-for="(r, ri) in (m.refs || [])" :key="'r' + ri" class="user-ref">
                  <img v-if="r.preview_url" :src="r.preview_url" class="user-ref-img" :alt="r.name" />
                  <span v-else class="user-ref-doc"><el-icon><Document /></el-icon> {{ r.name }}</span>
                </div>
                <span v-if="m.attachment" class="user-ref-doc">
                  <el-icon><Paperclip /></el-icon> {{ m.attachment.name }}
                </span>
              </div>
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
                  <img :src="img.url || img" class="gen-img" alt="生成图片" />
                  <a class="download-btn" @click="downloadImage(img)">
                    下载
                  </a>
                </div>
              </div>

              <!-- 文件转换结果：预览前两行 + 下载按钮 -->
              <div v-if="m.files?.length" class="msg-files">
                <div v-for="(f, fi) in m.files" :key="fi" class="file-card">
                  <div class="file-head">
                    <el-icon><Document /></el-icon>
                    <span class="file-name">{{ f.filename }}</span>
                    <a class="download-btn" @click="downloadFile(f)">
                      下载
                    </a>
                  </div>
                  <div v-if="f.preview" class="file-preview">{{ f.preview }}</div>
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
            <!-- @ 引用的文件 tag（背景色标识） -->
            <div v-if="mentionRefs.length" class="mention-tags">
              <span v-for="(r, ri) in mentionRefs" :key="ri" class="mention-tag">
                <el-icon><Document /></el-icon> {{ r.name }}
                <span class="close" @click="mentionRefs.splice(ri, 1)">×</span>
              </span>
            </div>
            <el-input
              v-model="input"
              type="textarea"
              :rows="3"
              :autosize="{ minRows: 3, maxRows: 8 }"
              placeholder="给 Easy WorkBuddy 发送消息，输入「@ + 空格」可引用资料库文件"
              class="msg-textarea"
              @input="onInput"
              @keydown="onTextareaKeydown"
            />
            <!-- @ 引用资料库文件悬浮列表 -->
            <div v-if="mentionVisible" class="mention-list">
              <div v-for="(d, i) in mentionDocs" :key="d.id" class="mention-item"
                :class="{ active: i === mentionIndex }" @mousedown.prevent="selectMention(d)">
                <el-icon><Document /></el-icon>
                <span class="m-name">{{ d.original_name }}</span>
                <span class="m-type">{{ d.file_type }}</span>
              </div>
              <div v-if="!mentionDocs.length" class="mention-empty">资料库暂无文件</div>
            </div>
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
                <el-tooltip content="上传文件，可附带发送给 Agent" placement="top">
                  <span class="tool-chip" @click="triggerFile">
                    <el-icon><Upload /></el-icon> 上传文件
                  </span>
                </el-tooltip>
                <input ref="fileInput" type="file" hidden @change="onFileChange" />
              </div>
              <button v-if="!sending" class="send-btn" :class="{ disabled: !canSend }" :disabled="!canSend"
                title="发送" @click="send">
                <el-icon><Promotion /></el-icon>
              </button>
              <button v-else class="send-btn stop" title="停止生成" @click="stop">
                <el-icon><VideoPause /></el-icon>
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
const abortController = ref(null)

// @ 引用资料库文件
const mentionDocs = ref([])
const mentionVisible = ref(false)
const mentionIndex = ref(0)
const mentionRefs = ref([])

const canSend = computed(() => (!!input.value.trim() || !!attachment.value || !!mentionRefs.value.length) && !sending.value)

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
  messages.value = (data.messages || []).map((m) => {
    const msg = { role: m.role, content: m.content }
    if (m.attachments) {
      const att = typeof m.attachments === 'string' ? JSON.parse(m.attachments) : m.attachments
      if (m.role === 'assistant') {
        // AI 消息：恢复生成图片 / 转换文件下载按钮
        if (att.images?.length) msg.images = att.images
        if (att.files?.length) msg.files = att.files
      } else if (m.role === 'user') {
        // 用户消息：恢复引用文件 / 上传附件（真实展示，不显示字符串）
        if (att.refs?.length) {
          msg.refs = att.refs
          // 图片引用：异步补预览地址
          att.refs.forEach((r) => {
            if (isImageType(r.file_type)) {
              documentApi.preview(r.id)
                .then((d) => { r.preview_url = d.url })
                .catch(() => {})
            }
          })
        }
        if (att.attachment) msg.attachment = att.attachment
      }
    }
    return msg
  })
  scrollBottom(true)
}

function triggerFile() {
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

// ---------- @ 引用资料库文件 ----------
async function openMention() {
  try {
    mentionDocs.value = await documentApi.list()
    mentionVisible.value = mentionDocs.value.length > 0
    mentionIndex.value = 0
  } catch {
    mentionVisible.value = false
  }
}

function onInput() {
  // 输入「@ + 空格」时打开引用列表；否则关闭
  if (input.value.endsWith('@ ')) {
    openMention()
  } else if (mentionVisible.value) {
    mentionVisible.value = false
  }
}

function isImageType(t) {
  return ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'].includes((t || '').toLowerCase())
}

async function selectMention(d) {
  // 移除「@ 」触发符，引用内容以 tag 形式显示（不插入纯文本）
  input.value = input.value.replace(/@\s*$/, '')
  const ref = { id: d.id, name: d.original_name, file_type: d.file_type }
  // 图片引用：拉取预览地址，便于用户对话框真实展示
  if (isImageType(d.file_type)) {
    try {
      const data = await documentApi.preview(d.id)
      ref.preview_url = data.url
    } catch { /* 忽略预览失败 */ }
  }
  mentionRefs.value.push(ref)
  mentionVisible.value = false
  mentionIndex.value = 0
}

function onTextareaKeydown(e) {
  if (mentionVisible.value && mentionDocs.value.length) {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      mentionIndex.value = (mentionIndex.value + 1) % mentionDocs.value.length
      return
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      mentionIndex.value = (mentionIndex.value - 1 + mentionDocs.value.length) % mentionDocs.value.length
      return
    }
    if (e.key === 'Enter') {
      e.preventDefault()
      selectMention(mentionDocs.value[mentionIndex.value])
      return
    }
    if (e.key === 'Escape') {
      mentionVisible.value = false
      return
    }
  }
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
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
  // AI 回复开头常带换行，去掉开头空白，避免气泡顶部留白
  if (m.role === 'assistant') t = t.replace(/^\s+/, '')
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
    } else if (evt.data?.key) {
      if (!msg.files) msg.files = []
      msg.files.push(evt.data)
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
  // 附件/开关信息（传给后端：持久化 + 给 LLM 的提示），content 只存纯文本
  const attachInfo = {
    refs: [...mentionRefs.value].map((r) => ({ id: r.id, name: r.name, file_type: r.file_type })),
    attachment: attachment.value ? { name: attachment.value.name, id: attachment.value.id } : null,
    web_search: webSearch.value,
    deep_think: deepThink.value,
  }
  messages.value.push({
    role: 'user',
    content: text,
    refs: [...mentionRefs.value],
    attachment: attachment.value ? { ...attachment.value } : null,
  })
  input.value = ''
  attachment.value = null
  mentionRefs.value = []
  mentionVisible.value = false
  sending.value = true
  abortController.value = new AbortController()
  const assistantMsg = reactive({ role: 'assistant', content: '', typing: true, tools: [], images: [] })
  messages.value.push(assistantMsg)
  scrollBottom(true)

  try {
    const resp = await streamChat(
      currentId.value,
      { content: text, attachments: attachInfo },
      abortController.value.signal
    )
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
  } catch (e) {
    // 用户手动终止
    if (e.name === 'AbortError') {
      assistantMsg.typing = false
      if (!assistantMsg.content) assistantMsg.content = '（已手动停止生成）'
    } else {
      assistantMsg.typing = false
      if (!assistantMsg.content) assistantMsg.content = '请求异常，请稍后重试'
    }
  } finally {
    sending.value = false
    abortController.value = null
    assistantMsg.typing = false
    scrollBottom(true)
  }
}

function stop() {
  abortController.value?.abort()
}

async function downloadFile(f) {
  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch(
      `/api/documents/download?key=${encodeURIComponent(f.key)}&filename=${encodeURIComponent(f.filename)}`,
      { headers: { Authorization: `Bearer ${token}` } }
    )
    if (!resp.ok) throw new Error('下载失败')
    const blob = await resp.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = f.filename || 'download'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('下载失败')
  }
}

function downloadImage(img) {
  // 新格式（{key, url}）用后端下载接口；旧格式（纯 URL）直接 fetch 下载
  if (img && typeof img === 'object' && img.key) {
    downloadFile({ key: img.key, filename: 'image.png' })
    return
  }
  const url = typeof img === 'string' ? img : img?.url
  if (!url) return
  fetch(url)
    .then((r) => r.blob())
    .then((blob) => {
      const objectUrl = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = objectUrl
      a.download = 'image.png'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(objectUrl)
    })
    .catch(() => ElMessage.error('下载失败'))
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

/* 用户消息：引用文件真实展示 */
.user-attachments { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; margin-bottom: 6px; }
.user-ref-img { display: block; max-width: 240px; max-height: 180px; border-radius: 12px; border: 1px solid var(--border); }
.user-ref-doc { display: inline-flex; align-items: center; gap: 6px; padding: 5px 10px; border-radius: 10px;
  background: var(--hover-bg); font-size: 13px; color: var(--text); max-width: 240px; }
.user-ref-doc .el-icon { color: var(--primary); }

/* 生成图片卡片 + 下载 */
.msg-images { display: flex; flex-direction: column; gap: 10px; margin-top: 8px; }
.img-card { border-radius: 14px; overflow: hidden; border: 1px solid var(--border); background: var(--card-bg); }
.gen-img { display: block; width: 100%; max-width: 360px; height: auto; }
.download-btn { cursor: pointer; display: inline-flex; justify-content: center; align-items: center; gap: 4px; padding: 6px 12px; margin: 8px;
  border-radius: 8px; background: var(--primary); color: #fff; font-size: 13px; text-decoration: none; }
.download-btn:hover { opacity: 0.9; }

/* 文件转换结果卡片 */
.msg-files { display: flex; flex-direction: column; gap: 10px; margin-top: 8px; }
.file-card { border-radius: 12px; border: 1px solid var(--border); background: var(--card-bg); padding: 10px 12px; }
.file-head { display: flex; align-items: center; gap: 8px; }
.file-head .el-icon { color: var(--primary); }
.file-name { flex: 1; font-weight: 600; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-card .download-btn { margin: 0; }
.file-preview { margin-top: 8px; font-size: 12px; color: var(--muted); font-family: monospace;
  background: var(--hover-bg); border-radius: 8px; padding: 8px 10px; white-space: pre-wrap;
  max-height: 60px; overflow: hidden; }

/* ===== 输入区：圆角高级感卡片，固定在底部 ===== */
.chat-input { padding: 8px 20px 16px; flex-shrink: 0; }
.input-box {
  position: relative;
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
/* @ 引用文件悬浮列表 */
.mention-list { position: absolute; left: 16px; right: 16px; bottom: 60px; z-index: 20;
  max-height: 240px; overflow-y: auto; background: var(--card-bg); border: 1px solid var(--border);
  border-radius: 12px; box-shadow: var(--shadow); padding: 6px; }
.mention-item { display: flex; align-items: center; gap: 8px; padding: 8px 10px; border-radius: 8px;
  cursor: pointer; font-size: 13px; }
.mention-item.active { background: var(--primary-soft); color: var(--primary); }
.mention-item:hover { background: var(--hover-bg); }
.mention-item .el-icon { flex-shrink: 0; }
.mention-item .m-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mention-item .m-type { font-size: 11px; color: var(--muted); }
.mention-empty { padding: 12px; text-align: center; color: var(--muted); font-size: 13px; }
.attach-chip { display: inline-flex; align-items: center; gap: 6px; padding: 5px 10px;
  background: var(--primary-soft); color: var(--primary); border-radius: 999px;
  font-size: 13px; margin-bottom: 8px; }
.attach-chip .name { max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.attach-chip .close { cursor: pointer; opacity: 0.6; font-size: 16px; line-height: 1; padding: 0 2px; }
.attach-chip .close:hover { opacity: 1; }

/* @ 引用文件 tag */
.mention-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.mention-tag { display: inline-flex; align-items: center; gap: 5px; padding: 4px 10px;
  background: rgba(124, 77, 255, 0.14); color: #7c4dff; border: 1px solid rgba(124, 77, 255, 0.3);
  border-radius: 999px; font-size: 13px; }
.mention-tag .close { cursor: pointer; opacity: 0.6; font-size: 15px; line-height: 1; padding: 0 2px; }
.mention-tag .close:hover { opacity: 1; }

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
.send-btn.stop { background: linear-gradient(135deg, #f56c6c, #ff4d4f); box-shadow: 0 4px 12px rgba(245, 108, 108, 0.35); }
.send-btn.stop:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(245, 108, 108, 0.5); }

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
