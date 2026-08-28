<template>
  <div>
    <div class="page-head">
      <h2>资料库</h2>
      <div class="head-right">
        <el-select v-model="wsId" placeholder="选择空间" style="width:180px" @change="load">
          <el-option v-for="w in workspaces" :key="w.id" :label="w.name" :value="w.id" />
        </el-select>
        <el-button type="primary" :disabled="!wsId" @click="openCreate">新建条目</el-button>
      </div>
    </div>

    <el-empty v-if="!wsId" description="请先选择工作空间" />
    <el-row v-else :gutter="16">
      <el-col v-for="k in list" :key="k.id" :span="12">
        <el-card class="k-card" shadow="hover">
          <div class="k-head">
            <span class="k-title">{{ k.title }}</span>
            <el-tag v-if="k.category" size="small">{{ k.category }}</el-tag>
          </div>
          <div class="k-actions">
            <el-button size="small" @click="toggleDocs(k)">文档</el-button>
            <el-upload :show-file-list="false" :http-request="(opt) => doUpload(opt, k)"
              accept=".docx,.xlsx,.pdf,.txt,.md,.csv">
              <el-button size="small" type="primary" plain>上传</el-button>
            </el-upload>
            <el-button size="small" type="danger" plain @click="remove(k)">删除</el-button>
          </div>
          <div v-if="expandedId === k.id" class="docs">
            <div v-for="d in docs[k.id]" :key="d.id" class="doc-item">
              <span class="doc-name">{{ d.original_name }}</span>
              <span class="doc-meta">{{ (d.file_size / 1024).toFixed(1) }} KB</span>
            </div>
            <el-empty v-if="!docs[k.id]?.length" description="暂无文档" :image-size="50" />
          </div>
        </el-card>
      </el-col>
      <el-col :span="12" v-if="!list.length">
        <el-empty description="还没有资料，点击右上角新建" />
      </el-col>
    </el-row>

    <el-dialog v-model="dialogVisible" title="新建资料条目" width="440px">
      <el-form :model="form" label-width="72px">
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="条目标题" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="form.category" placeholder="可选，如 FAQ / 文档" />
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
import { documentApi, knowledgeApi, workspaceApi } from '@/api'

const workspaces = ref([])
const wsId = ref(null)
const list = ref([])
const docs = ref({})
const expandedId = ref(null)
const dialogVisible = ref(false)
const saving = ref(false)
const form = reactive({ title: '', category: '' })

async function loadWorkspaces() {
  workspaces.value = await workspaceApi.list()
  if (!wsId.value && workspaces.value.length) wsId.value = workspaces.value[0].id
}

async function load() {
  if (!wsId.value) return
  list.value = await knowledgeApi.list(wsId.value)
}

function openCreate() {
  Object.assign(form, { title: '', category: '' })
  dialogVisible.value = true
}

async function save() {
  if (!form.title) return ElMessage.warning('请输入标题')
  saving.value = true
  try {
    await knowledgeApi.create({ workspace_id: wsId.value, title: form.title, category: form.category })
    dialogVisible.value = false
    ElMessage.success('已创建')
    load()
  } finally {
    saving.value = false
  }
}

async function toggleDocs(k) {
  if (expandedId.value === k.id) {
    expandedId.value = null
    return
  }
  expandedId.value = k.id
  docs.value[k.id] = await documentApi.list(k.id)
}

async function doUpload(opt, k) {
  const fd = new FormData()
  fd.append('file', opt.file)
  fd.append('workspace_id', wsId.value)
  fd.append('knowledge_doc_id', k.id)
  try {
    await documentApi.upload(fd)
    ElMessage.success('上传成功')
    if (expandedId.value === k.id) docs.value[k.id] = await documentApi.list(k.id)
  } catch {
    ElMessage.error('上传失败')
  }
}

async function remove(k) {
  await ElMessageBox.confirm(`确定删除「${k.title}」吗？`, '提示', { type: 'warning' })
  await knowledgeApi.remove(k.id)
  ElMessage.success('已删除')
  load()
}

onMounted(async () => {
  await loadWorkspaces()
  await load()
})
</script>

<style scoped>
.page-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.head-right { display: flex; gap: 12px; }
.k-card { margin-bottom: 16px; }
.k-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.k-title { font-weight: 600; font-size: 15px; }
.k-actions { display: flex; align-items: center; gap: 8px; }
.docs { margin-top: 12px; border-top: 1px dashed #eee; padding-top: 8px; }
.doc-item { display: flex; justify-content: space-between; padding: 6px 0; font-size: 13px; }
.doc-meta { color: #999; }
</style>
