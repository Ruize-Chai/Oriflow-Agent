<template>
  <div class="canvas" ref="root" @dragover.prevent @drop="onDrop">
    <div class="grid" />
    <div class="nodes">
      <NodeRenderer v-for="n in internalNodes" :key="n.id" :node="n" :state="nodeStates[n.id]" :style="nodeStyle(n)" @select="select" @moved="onNodeMoved" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import NodeRenderer from './nodes/NodeRenderer.vue'
const props = defineProps<{ nodes?: any[]; nodeStates?: Record<number,string> }>()
const emit = defineEmits(['add','select','update:nodes'])
const root = ref<HTMLElement | null>(null)
const internalNodes = ref<any[]>(props.nodes ? JSON.parse(JSON.stringify(props.nodes)) : [])
const nodeStates = props.nodeStates || {}

watch(() => props.nodes, (v) => { if (v) internalNodes.value = JSON.parse(JSON.stringify(v)) }, { deep: true })

function onDrop(e: DragEvent) {
  const t = e.dataTransfer?.getData('application/node-type')
  if (!t || !root.value) return
  const rect = root.value.getBoundingClientRect()
  const x = Math.round(e.clientX - rect.left)
  const y = Math.round(e.clientY - rect.top)
  const id = Date.now() % 100000
  const newNode = { id, type: t, x, y, params: {} }
  internalNodes.value.push(newNode)
  emit('add', newNode)
  emit('update:nodes', internalNodes.value)
}

function select(n: any) { emit('select', n) }

function nodeStyle(n: any) {
  return { left: (n.x || 0) + 'px', top: (n.y || 0) + 'px', position: 'absolute' }
}

function onNodeMoved(node: any) {
  const idx = internalNodes.value.findIndex((x: any) => x.id === node.id)
  if (idx !== -1) internalNodes.value.splice(idx, 1, node)
  emit('update:nodes', internalNodes.value)
}

defineExpose({ internalNodes })
</script>

<style scoped>
.canvas { position:relative; flex:1; overflow:hidden; background: linear-gradient(180deg,#071022 0%, #071428 100%); }
.grid { position:absolute; inset:0; background-image: radial-gradient(rgba(255,255,255,0.02) 1px, transparent 1px); background-size: 20px 20px }
.nodes { position:relative }
.node { position:absolute; width:160px; height:72px; border-radius:8px; background:rgba(255,255,255,0.03); color:#e6eef8; padding:8px; box-shadow: 0 6px 18px rgba(2,6,23,0.6) }
.node .title { font-weight:600 }
.node .id { font-size:12px; opacity:0.6 }
</style>
