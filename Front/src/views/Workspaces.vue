<template>
  <div>
    <div class="page-head">
      <h2>工作空间</h2>
      <el-button type="primary" @click="openCreate">新建空间</el-button>
    </div>

    <el-row :gutter="16">
      <el-col v-for="ws in list" :key="ws.id" :span="8">
        <el-card class="ws-card" shadow="hover">
          <div class="ws-title">
            <span class="name">{{ ws.name }}</span>
            <el-tag v-if="ws.is_default" size="small" type="success">默认</el-tag>
          </div>
          <p class="ws-desc">{{ ws.description || '暂无描述' }}</p>
          <div class="ws-actions">
            <el-button size="small" @click="openEdit(ws)">编辑</el-button>
            <el-button size="small" type="success" plain @click="setDefault(ws)">
              设为默认
            </el-button>
            <el-button size="small" type="danger" plain @click="remove(ws)">删除</el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8" v-if="!list.length">
        <el-empty description="还没有工作空间，点击右上角新建" />
      </el-col>
    </el-row>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑空间' : '新建空间'" width="440px">
      <el-form :model="form" label-width="72px">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="空间名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" placeholder="可选" />
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
import { workspaceApi } from '@/api'

const list = ref([])
const dialogVisible = ref(false)
const saving = ref(false)
const form = reactive({ id: null, name: '', description: '' })

async function load() {
  list.value = await workspaceApi.list()
}

function openCreate() {
  Object.assign(form, { id: null, name: '', description: '' })
  dialogVisible.value = true
}

function openEdit(ws) {
  Object.assign(form, { id: ws.id, name: ws.name, description: ws.description || '' })
  dialogVisible.value = true
}

async function save() {
  if (!form.name) return ElMessage.warning('请输入名称')
  saving.value = true
  try {
    if (form.id) {
      await workspaceApi.update(form.id, { name: form.name, description: form.description })
    } else {
      await workspaceApi.create({ name: form.name, description: form.description })
    }
    dialogVisible.value = false
    ElMessage.success('已保存')
    load()
  } finally {
    saving.value = false
  }
}

async function setDefault(ws) {
  await workspaceApi.update(ws.id, { is_default: true })
  ElMessage.success('已设为默认')
  load()
}

async function remove(ws) {
  await ElMessageBox.confirm(`确定删除空间「${ws.name}」吗？`, '提示', { type: 'warning' })
  await workspaceApi.remove(ws.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>

<style scoped>
.page-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.ws-card { margin-bottom: 16px; }
.ws-title { display: flex; align-items: center; gap: 8px; }
.ws-title .name { font-weight: 600; font-size: 16px; }
.ws-desc { color: var(--muted); min-height: 40px; }
.ws-actions { margin-top: 8px; }
</style>
