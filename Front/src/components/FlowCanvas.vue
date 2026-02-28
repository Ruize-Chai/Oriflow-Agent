<template>
  <div class="canvas" ref="root" @dragover.prevent @drop="onDrop">
    <div class="grid" />
    <EdgeRenderer :nodes="internalNodes" :edges="edges" :activeEdges="activeEdgeIds" />
    <div class="nodes">
      <NodeRenderer v-for="n in internalNodes" :key="n.id" :node="n" :state="nodeStates[n.id]" :style="nodeStyle(n)" @select="select" @moved="onNodeMoved" @delete="onNodeDelete" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import NodeRenderer from './nodes/NodeRenderer.vue'
import EdgeRenderer from './EdgeRenderer.vue'

const props = defineProps<{ nodes?: any[]; nodeStates?: Record<number,string> }>()
const emit = defineEmits(['add','select','update:nodes'])
const root = ref<HTMLElement | null>(null)
const internalNodes = ref<any[]>(props.nodes ? JSON.parse(JSON.stringify(props.nodes)) : [])
const nodeStates = props.nodeStates || {}

// 从节点的listen和outputs字段推导边信息
const edges = computed(() => {
  const edgeList: any[] = []
  internalNodes.value.forEach(node => {
    if (node.outputs && Array.isArray(node.outputs)) {
      node.outputs.forEach((targetId: any, idx: number) => {
        if (targetId !== null && targetId !== undefined) {
          edgeList.push({
            id: `${node.id}->${targetId}-${idx}`,
            from: node.id,
            to: targetId
          })
        }
      })
    }
  })
  return edgeList
})

// 如果目标节点处于RUNNING或ACTIVE状态，则边处于active
const activeEdgeIds = computed(() => {
  return edges.value
    .filter(e => {
      const targetState = nodeStates[e.to]
      return targetState && ['RUNNING', 'ACTIVE'].includes(targetState.toUpperCase())
    })
    .map(e => e.id)
})

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

function onNodeDelete(nodeId: number) {
  const idx = internalNodes.value.findIndex((n: any) => n.id === nodeId)
  if (idx !== -1) {
    internalNodes.value.splice(idx, 1)
    emit('update:nodes', internalNodes.value)
  }
}

defineExpose({ internalNodes })
</script>

<style scoped>
.canvas { position:relative; flex:1; overflow:hidden; background: linear-gradient(180deg,#071022 0%, #071428 100%); user-select:none; -webkit-user-select:none }
.grid { position:absolute; inset:0; background-image: radial-gradient(rgba(255,255,255,0.02) 1px, transparent 1px); background-size: 20px 20px }
.nodes { position:relative }
</style>
