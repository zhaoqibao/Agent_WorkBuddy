<template>
  <div>
    <div class="page-head">
      <h2>任务</h2>
      <div class="head-right">
        <el-select v-model="wsId" placeholder="选择工作空间" style="width:180px" @change="load">
          <el-option v-for="w in workspaces" :key="w.id" :label="w.name" :value="w.id" />
        </el-select>
        <el-button type="primary" :disabled="!wsId" @click="openCreate">新建任务</el-button>
      </div>
    </div>

    <el-empty v-if="!wsId" description="请先选择工作空间" />
    <el-table v-else :data="list" style="width:100%">
      <el-table-column label="标题" min-width="220">
        <template #default="{ row }">
          <span :style="row.status === 2 ? 'text-decoration:line-through;color:var(--muted)' : ''">
            {{ row.title }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag :type="['info', 'warning', 'success'][row.status]" size="small">
            {{ ['待办', '进行中', '已完成'][row.status] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="优先级" width="100">
        <template #default="{ row }">
          <el-tag :type="['info', 'warning', 'danger'][row.priority]" size="small" effect="plain">
            {{ ['低', '中', '高'][row.priority] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="截止时间" width="160">
        <template #default="{ row }">{{ row.due_date ? row.due_date.slice(0, 10) : '—' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="toggleStatus(row)">完成</el-button>
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" plain @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑任务' : '新建任务'" width="460px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="任务标题" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" placeholder="可选" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="form.priority" style="width:100%">
            <el-option label="低" :value="0" />
            <el-option label="中" :value="1" />
            <el-option label="高" :value="2" />
          </el-select>
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker v-model="form.due_date" type="date" value-format="YYYY-MM-DD"
            style="width:100%" />
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
import { taskApi, workspaceApi } from '@/api'

const workspaces = ref([])
const wsId = ref(null)
const list = ref([])
const dialogVisible = ref(false)
const saving = ref(false)
const form = reactive({ id: null, title: '', description: '', priority: 1 })

async function loadWorkspaces() {
  workspaces.value = await workspaceApi.list()
  if (!wsId.value && workspaces.value.length) wsId.value = workspaces.value[0].id
}

async function load() {
  if (!wsId.value) return
  list.value = await taskApi.list(wsId.value)
}

function openCreate() {
  Object.assign(form, { id: null, title: '', description: '', priority: 1, due_date: null })
  dialogVisible.value = true
}

function openEdit(t) {
  Object.assign(form, {
    id: t.id,
    title: t.title,
    description: t.description || '',
    priority: t.priority,
    due_date: t.due_date ? t.due_date.slice(0, 10) : null,
  })
  dialogVisible.value = true
}

async function save() {
  if (!form.title) return ElMessage.warning('请输入标题')
  saving.value = true
  try {
    const body = { title: form.title, description: form.description, priority: form.priority }
    if (form.due_date) body.due_date = form.due_date
    if (form.id) {
      await taskApi.update(form.id, body)
    } else {
      await taskApi.create({ workspace_id: wsId.value, ...body })
    }
    dialogVisible.value = false
    ElMessage.success('已保存')
    load()
  } finally {
    saving.value = false
  }
}

async function toggleStatus(t) {
  await taskApi.update(t.id, { status: t.status === 2 ? 0 : 2 })
  load()
}

async function remove(t) {
  await ElMessageBox.confirm(`确定删除任务「${t.title}」吗？`, '提示', { type: 'warning' })
  await taskApi.remove(t.id)
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
</style>
