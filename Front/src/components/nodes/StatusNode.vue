<template>
  <div :class="['status-node', statusClass]">
    <div class="header">
      <div class="type">{{ node.type }}</div>
      <div class="state">{{ displayState }}</div>
    </div>
    <div class="body">#{{ node.id }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ node: any; state?: string }>()

const mapState = (s?: string) => {
  if (!s) return 'idle'
  const up = s.toUpperCase()
  if (up === 'ACTIVE') return 'running'
  if (up === 'OUTPUT' || up === 'SUCCESS' || up === 'DONE') return 'success'
  if (up === 'TEXT INPUT' || up === 'NUMBER INPUT' || up === 'CHECKBOX' || up === 'WAITING') return 'waiting'
  if (up === 'ERROR' || up === 'FAILED') return 'error'
  return 'idle'
}

const statusClass = computed(() => mapState(props.state))
const displayState = computed(() => props.state || 'IDLE')
</script>

<style scoped>
.status-node { width:160px; height:72px; padding:8px; border-radius:8px; color:#e6eef8; background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.03); display:flex; flex-direction:column; justify-content:space-between }
.status-node .header { display:flex; justify-content:space-between; font-size:12px; opacity:0.9 }
.status-node .body { font-weight:600 }

.status-node.idle { box-shadow:none; opacity:0.9 }
.status-node.running { border-color: rgba(34,211,238,0.25); box-shadow: 0 6px 18px rgba(6,182,212,0.08); }
.status-node.waiting { animation: pulse-amber 2s infinite; border-color: rgba(255,184,77,0.18) }
.status-node.success { border-color: rgba(16,185,129,0.16); box-shadow: 0 8px 24px rgba(16,185,129,0.05) }
.status-node.error { border-color: rgba(239,68,68,0.22); box-shadow: 0 6px 18px rgba(239,68,68,0.06) }

@keyframes pulse-amber{0%{box-shadow:0 0 0 0 rgba(255,184,77,0.06)}50%{box-shadow:0 0 22px 6px rgba(255,184,77,0.04)}100%{box-shadow:0 0 0 0 rgba(255,184,77,0)}}
</style>
