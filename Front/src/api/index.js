import request from '@/utils/request'

export const authApi = {
  register: (body) => request.post('/api/auth/register', body),
  login: (body) => request.post('/api/auth/login', body),
  me: () => request.get('/api/auth/me'),
  profile: () => request.get('/api/auth/profile'),
  updateProfile: (body) => request.put('/api/auth/profile', body),
  changePassword: (body) => request.put('/api/auth/password', body),
}

export const agentApi = {
  list: (workspaceId) => request.get('/api/agents', { params: { workspace_id: workspaceId } }),
  create: (body) => request.post('/api/agents', body),
  update: (id, body) => request.put(`/api/agents/${id}`, body),
  remove: (id) => request.delete(`/api/agents/${id}`),
}

export const workspaceApi = {
  list: () => request.get('/api/workspaces'),
  create: (body) => request.post('/api/workspaces', body),
  update: (id, body) => request.put(`/api/workspaces/${id}`, body),
  remove: (id) => request.delete(`/api/workspaces/${id}`),
}

export const taskApi = {
  list: (workspaceId) => request.get('/api/tasks', { params: { workspace_id: workspaceId } }),
  create: (body) => request.post('/api/tasks', body),
  update: (id, body) => request.put(`/api/tasks/${id}`, body),
  remove: (id) => request.delete(`/api/tasks/${id}`),
}

export const conversationApi = {
  list: (workspaceId) => request.get('/api/conversations', { params: { workspace_id: workspaceId } }),
  create: (body) => request.post('/api/conversations', body),
  detail: (id) => request.get(`/api/conversations/${id}`),
  remove: (id) => request.delete(`/api/conversations/${id}`),
  send: (id, body) => request.post(`/api/conversations/${id}/messages`, body),
}

export const knowledgeApi = {
  list: (workspaceId) => request.get('/api/knowledge', { params: { workspace_id: workspaceId } }),
  create: (body) => request.post('/api/knowledge', body),
  remove: (id) => request.delete(`/api/knowledge/${id}`),
}

export const documentApi = {
  list: (knowledgeDocId) =>
    request.get('/api/documents', { params: { knowledge_doc_id: knowledgeDocId } }),
  upload: (formData) => request.post('/api/documents/upload', formData),
  preview: (id) => request.get(`/api/documents/${id}/preview`),
}

// 流式对话（SSE）：返回 fetch Response，调用方用 ReadableStream 解析
export function streamChat(convId, content) {
  const token = localStorage.getItem('access_token')
  return fetch(`/api/conversations/${convId}/messages/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ content }),
  })
}
