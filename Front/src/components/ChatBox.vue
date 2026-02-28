<template>
  <div class="chatbox-root">
    <div class="messages" ref="listRef">
      <div v-for="(m, idx) in messages" :key="idx" :class="['msg', m.role==='user'? 'user':'ai']">
        <div class="bubble" v-html="renderMarkdown(m.content)"></div>
        <div v-if="m.meta && m.meta.content_type === 'file_link'" class="file-card">
          <div class="file-info">
            <svg class="icon" viewBox="0 0 24 24"><path fill="currentColor" d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zM13 3.5L18.5 9H14a1 1 0 0 1-1-1V3.5z"/></svg>
            <div class="meta">{{ m.meta.filename || 'file' }}</div>
          </div>
          <button class="btn" @click="downloadFile(m.meta)">Download</button>
        </div>
      </div>
    </div>
    <div class="compose" v-if="showInput">
      <el-input v-model="inputText" placeholder="Type response..."/>
      <el-button @click="submitInput">Send</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import type { ChatboxOutputPayload } from '../api/oriflow'

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

const props = defineProps<{ initial?: Array<{ role: string; content: string; meta?: any }>; showInput?: boolean }>()
const emit = defineEmits(['submit'])

const messages = ref<Array<{ role: string; content: string; meta?: any }>>(props.initial || [])
const inputText = ref('')
const showInput = props.showInput ?? false
const listRef = ref<HTMLElement | null>(null)

function renderMarkdown(mdText: string) {
  return md.render(mdText || '')
}

function appendMessage(msg: { role: string; content: string; meta?: any }) {
  messages.value.push(msg)
  // auto scroll
  setTimeout(() => {
    if (listRef.value) listRef.value.scrollTop = listRef.value.scrollHeight
  }, 60)
}

function downloadFile(meta: any) {
  if (!meta) return
  const filename = meta.filename || meta.path
  // attempt to fetch from FileBase folder
  fetch(`/FileBase/${filename}`)
    .then(async r => {
      if (!r.ok) throw new Error('fetch failed')
      const blob = await r.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
    })
    .catch(() => {
      navigator.clipboard.writeText(filename || '')
      // fallback: copy filename
      window.alert('无法直接下载；文件名已复制到剪贴板：' + (filename || ''))
    })
}

function submitInput() {
  if (!inputText.value) return
  emit('submit', inputText.value)
  inputText.value = ''
}

// expose functions
defineExpose({ appendMessage })
</script>

<style scoped>
.chatbox-root { display:flex; flex-direction:column; height:100%; background:transparent }
.messages { flex:1; overflow:auto; padding:12px }
.msg { margin:8px 0; display:flex; flex-direction:column }
.msg.user { align-items:flex-end }
.msg.ai { align-items:flex-start }
.bubble { max-width:78%; padding:10px 12px; border-radius:8px; background:rgba(255,255,255,0.04); color:#e6eef8 }
.msg.user .bubble { background:#0366d6 }
.file-card { margin-top:8px; display:flex; align-items:center; gap:8px }
.file-info { display:flex; align-items:center; gap:8px }
.file-info .icon { width:20px; height:20px; color:#9fb0ff }
.btn { background:transparent; border:1px solid rgba(255,255,255,0.06); color:#cfe4ff; padding:6px 10px; border-radius:6px }
.compose { display:flex; gap:8px; padding:8px; border-top:1px solid rgba(255,255,255,0.03) }
</style>

