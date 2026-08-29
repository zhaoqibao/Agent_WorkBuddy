<template>
  <div>
    <div class="page-head">
      <h2>Agent 智能体</h2>
      <el-button type="primary" @click="openCreate">新建 Agent</el-button>
    </div>

    <el-row :gutter="16">
      <el-col v-for="a in list" :key="a.id" :span="8">
        <el-card class="agent-card" shadow="hover">
          <div class="agent-head">
            <div class="agent-avatar">{{ a.name.slice(0, 1) }}</div>
            <div class="agent-title">
              <div class="name">{{ a.name }}</div>
              <div class="model">{{ a.model || '默认模型' }}</div>
            </div>
          </div>
          <p class="agent-desc">{{ a.description || '暂无描述' }}</p>
          <div class="agent-tools">
            <el-tag v-for="t in (a.tools || [])" :key="t" size="small" effect="plain" class="tool-tag">
              {{ toolLabel(t) }}
            </el-tag>
            <span v-if="!(a.tools || []).length" class="no-tool">未启用工具</span>
          </div>
          <div class="agent-actions">
            <el-button size="small" @click="openEdit(a)">编辑</el-button>
            <el-button size="small" type="danger" plain @click="remove(a)">删除</el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8" v-if="!list.length">
        <el-empty description="还没有 Agent，点击右上角新建" />
      </el-col>
    </el-row>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑 Agent' : '新建 Agent'" width="520px">
      <el-form :model="form" label-width="84px">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="如：万能助手" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" placeholder="一句话描述这个 Agent" />
        </el-form-item>
        <el-form-item label="系统提示词">
          <el-input v-model="form.system_prompt" type="textarea" :rows="4"
            placeholder="定义 Agent 的角色与行为，如：你是一个乐于助人的助手…" />
        </el-form-item>
        <el-form-item label="模型">
          <el-input v-model="form.model" placeholder="留空则使用默认模型" />
        </el-form-item>
        <el-form-item label="启用工具">
          <el-checkbox-group v-model="form.tools">
            <el-checkbox v-for="t in toolOptions" :key="t.value" :value="t.value">{{ t.label }}</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { agentApi } from '@/api'

const toolOptions = [
  { value: 'get_weather', label: '天气查询' },
  { value: 'get_news', label: '实时新闻' },
  { value: 'read_document', label: '文档读取' },
  { value: 'convert_document', label: '文档格式转换' },
  { value: 'recognize_image', label: '图片识别' },
  { value: 'generate_image', label: '图片生成' },
]
const toolMap = Object.fromEntries(toolOptions.map((t) => [t.value, t.label]))
const toolLabel = (v) => toolMap[v] || v

const list = ref([])
const dialogVisible = ref(false)
const saving = ref(false)
const form = reactive({ id: null, name: '', description: '', system_prompt: '', model: '', tools: [] })

async function load() {
  list.value = await agentApi.list()
}

function openCreate() {
  Object.assign(form, { id: null, name: '', description: '', system_prompt: '', model: '', tools: [] })
  dialogVisible.value = true
}

function openEdit(a) {
  Object.assign(form, {
    id: a.id,
    name: a.name,
    description: a.description || '',
    system_prompt: a.system_prompt || '',
    model: a.model || '',
    tools: a.tools ? [...a.tools] : [],
  })
  dialogVisible.value = true
}

async function save() {
  if (!form.name) return ElMessage.warning('请输入名称')
  saving.value = true
  try {
    const body = {
      name: form.name,
      description: form.description,
      system_prompt: form.system_prompt,
      model: form.model || null,
      tools: form.tools,
    }
    if (form.id) {
      await agentApi.update(form.id, body)
    } else {
      await agentApi.create(body)
    }
    dialogVisible.value = false
    ElMessage.success('已保存')
    load()
  } finally {
    saving.value = false
  }
}

async function remove(a) {
  await ElMessageBox.confirm(`确定删除 Agent「${a.name}」吗？`, '提示', { type: 'warning' })
  await agentApi.remove(a.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>

<style scoped>
.page-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.agent-card { margin-bottom: 16px; border-radius: 16px; }
.agent-head { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.agent-avatar { width: 44px; height: 44px; border-radius: 12px; background: var(--primary);
  color: #fff; display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 600; }
.agent-title .name { font-weight: 600; font-size: 16px; }
.agent-title .model { font-size: 12px; color: var(--muted); }
.agent-desc { color: var(--muted); min-height: 40px; }
.agent-tools { display: flex; flex-wrap: wrap; gap: 6px; min-height: 28px; margin-bottom: 12px; }
.no-tool { font-size: 12px; color: var(--muted); }
.agent-actions { display: flex; gap: 8px; }
</style>
