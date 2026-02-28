<template>
  <div class="chatbox-root">
    <!-- Header -->
    <div class="chatbox-header">
      <span class="title">Conversation Log</span>
      <button v-if="messages.length > 0" class="clear-btn" @click="clearHistory" title="Clear all messages">
        <svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 6.4L17.6 5 12 10.6 6.4 5 5 6.4 10.6 12 5 17.6 6.4 19 12 13.4 17.6 19 19 17.6 13.4 12z"/></svg>
      </button>
    </div>

    <!-- Messages -->
    <div class="messages" ref="listRef">
      <div v-if="messages.length === 0" class="empty-state">
        <div class="icon">💬</div>
        <p>No messages yet</p>
        <small>Workflow outputs will appear here</small>
      </div>

      <div v-for="(m, idx) in messages" :key="idx" :class="['msg', `role-${m.role}`]">
        <div v-if="m.role === 'system'" class="system-line">
          <span class="badge">{{ m.meta?.badge || 'SYSTEM' }}</span>
          <span class="text">{{ m.content }}</span>
        </div>
        <div v-else>
          <div class="bubble" :class="{ loading: m.meta?.loading }">
            <div v-html="renderMarkdown(m.content)"></div>
            <div v-if="m.meta?.loading" class="spinner"></div>
          </div>

          <!-- File Card -->
          <div v-if="m.meta && m.meta.content_type === 'file_link'" class="file-card">
            <div class="file-info">
              <svg class="icon" viewBox="0 0 24 24">
                <path fill="currentColor" d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zM13 3.5L18.5 9H14a1 1 0 0 1-1-1V3.5z"/>
              </svg>
              <div class="meta">
                <div class="filename">{{ m.meta.filename || 'file' }}</div>
                <div v-if="m.meta.size" class="size">{{ formatFileSize(m.meta.size) }}</div>
              </div>
            </div>
            <button class="btn" @click="downloadFile(m.meta)">📥 Download</button>
          </div>
        </div>

        <div v-if="m.timestamp" class="timestamp">{{ formatTime(m.timestamp) }}</div>
      </div>
    </div>

    <!-- Input Area -->
    <div v-if="showInput" class="input-area">
      <el-input
        v-model="inputText"
        placeholder="Type your response..."
        @keydown.enter="submitInput"
        clearable
      />
      <el-button type="primary" :loading="submitting" @click="submitInput">Send</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

const md = new MarkdownIt({
  highlight: function (str: string, lang: string) {
    try {
      if (lang && hljs.getLanguage(lang)) {
        return '<pre class="hljs"><code>' + hljs.highlight(str, { language: lang }).value + '</code></pre>'
      }
    } catch (__) {}
    return '<pre class="hljs"><code>' + md.utils.escapeHtml(str) + '</code></pre>'
  }
})

const props = defineProps<{ initial?: Array<any>; showInput?: boolean }>()
const emit = defineEmits(['submit'])

const messages = ref<Array<any>>(props.initial || [])
const inputText = ref('')
const showInput = props.showInput ?? false
const listRef = ref<HTMLElement | null>(null)
const submitting = ref(false)

function renderMarkdown(mdText: string) {
  return md.render(mdText || '')
}

function formatTime(timestamp: number | Date): string {
  const date = typeof timestamp === 'number' ? new Date(timestamp) : timestamp
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${hours}:${minutes}`
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

function appendMessage(msg: { role: string; content: string; meta?: any; timestamp?: Date }) {
  messages.value.push({
    ...msg,
    timestamp: msg.timestamp || new Date()
  })
  // auto scroll
  setTimeout(() => {
    if (listRef.value) {
      listRef.value.scrollTop = listRef.value.scrollHeight
    }
  }, 60)
}

function appendSystemMessage(content: string, badge?: string) {
  appendMessage({
    role: 'system',
    content,
    meta: { badge: badge || 'SYSTEM' }
  })
}

function appendLoadingMessage(role: string = 'ai') {
  appendMessage({
    role,
    content: 'Processing...',
    meta: { loading: true }
  })
}

function downloadFile(meta: any) {
  if (!meta) return
  const filename = meta.filename || meta.path || 'file'

  const endpoints = [
    `/api/files/${filename}`,
    `/filebase/${filename}`,
    `/FileBase/${filename}`,
  ]

  let attemptCount = 0

  const tryNextEndpoint = () => {
    if (attemptCount >= endpoints.length) {
      window.alert(`Unable to download file: ${filename}\n\nTry copying the filename and accessing it manually.`)
      navigator.clipboard.writeText(filename)
      return
    }

    const url = endpoints[attemptCount]
    attemptCount++

    fetch(url)
      .then(async r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        const blob = await r.blob()
        const downloadUrl = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = downloadUrl
        a.download = filename
        a.click()
        URL.revokeObjectURL(downloadUrl)
      })
      .catch(() => {
        tryNextEndpoint()
      })
  }

  tryNextEndpoint()
}

async function submitInput() {
  if (!inputText.value.trim() || submitting.value) return

  const text = inputText.value
  inputText.value = ''
  submitting.value = true

  try {
    await emit('submit', text)
  } finally {
    submitting.value = false
  }
}

function clearHistory() {
  if (window.confirm('Clear all messages?')) {
    messages.value = []
  }
}

// Expose methods
defineExpose({
  appendMessage,
  appendSystemMessage,
  appendLoadingMessage,
  clearHistory,
  messages
})
</script>

<style scoped>
.chatbox-root {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: transparent;
}

.chatbox-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.02);
}

.chatbox-header .title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-light);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.clear-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  width: 24px;
  height: 24px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}

.clear-btn:hover {
  color: var(--text-light);
}

.clear-btn svg {
  width: 16px;
  height: 16px;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  text-align: center;
}

.empty-state .icon {
  font-size: 48px;
  margin-bottom: 8px;
  opacity: 0.4;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

.empty-state small {
  font-size: 12px;
  opacity: 0.6;
  margin-top: 4px;
}

.msg {
  display: flex;
  flex-direction: column;
  margin-bottom: 4px;
  animation: fade-in 0.3s ease-out;
}

.msg.role-user {
  align-items: flex-end;
}

.msg.role-ai {
  align-items: flex-start;
}

.msg.role-system {
  align-items: center;
  margin: 8px 0;
}

.system-line {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 0;
  justify-content: center;
}

.system-line .badge {
  display: inline-block;
  padding: 2px 8px;
  background: rgba(100, 116, 139, 0.3);
  border-radius: 3px;
  font-size: 10px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.system-line .text {
  color: var(--text-muted);
  font-size: 12px;
}

.bubble {
  max-width: 75%;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-light);
  word-break: break-word;
  line-height: 1.5;
  position: relative;
}

.msg.role-user .bubble {
  background: linear-gradient(135deg, #0373d9, #0399d8);
  color: #fff;
  border-radius: 12px 12px 2px 12px;
}

.msg.role-ai .bubble {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px 12px 12px 2px;
}

.bubble.loading {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 32px;
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-top-color: var(--accent-glow);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg) }
}

.file-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 8px;
  padding: 10px 12px;
  background: rgba(100, 116, 139, 0.1);
  border: 1px solid rgba(100, 116, 139, 0.2);
  border-radius: 8px;
  max-width: 75%;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.file-info .icon {
  width: 24px;
  height: 24px;
  color: var(--accent-glow);
  flex-shrink: 0;
}

.file-info .meta {
  min-width: 0;
}

.file-info .filename {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-light);
  word-break: break-all;
}

.file-info .size {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}

.btn {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: var(--accent-glow);
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  transition: all 0.2s;
}

.btn:hover {
  background: rgba(0, 212, 255, 0.1);
  border-color: var(--accent-glow);
}

.timestamp {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 2px;
  text-align: right;
}

.msg.role-user .timestamp {
  text-align: right;
}

.msg.role-ai .timestamp {
  text-align: left;
}

.input-area {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.02);
}

.input-area :deep(.el-input) {
  flex: 1;
}

@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Scrollbar styling */
.messages::-webkit-scrollbar {
  width: 6px;
}

.messages::-webkit-scrollbar-track {
  background: transparent;
}

.messages::-webkit-scrollbar-thumb {
  background: rgba(100, 116, 139, 0.3);
  border-radius: 3px;
}

.messages::-webkit-scrollbar-thumb:hover {
  background: rgba(100, 116, 139, 0.5);
}
</style>

