<template>
  <div class="node-wrap" :style="styleObj" @mousedown.stop.prevent="startDrag" @touchstart.stop.prevent="startTouch">
    <component :is="nodeComponent" :node="node" :state="state" @select="onClick" @change="onChildChange" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeUnmount } from 'vue'
import StartNode from './StartNode.vue'
import EndNode from './EndNode.vue'
import TextInputNode from './TextInputNode.vue'
import NumberInputNode from './NumberInputNode.vue'
import ChatboxNode from './ChatboxNode.vue'
import CheckboxNode from './CheckboxNode.vue'
import DelayTimerNode from './DelayTimerNode.vue'
import IfConditionNode from './IfConditionNode.vue'
import LLMAnswerNode from './LLMAnswerNode.vue'
import LLMFileProductionNode from './LLMFileProductionNode.vue'

const props = defineProps<{ node: any; state?: string; style?: any }>()
const emit = defineEmits(['select','moved'])

const mapping: Record<string, any> = {
  'Start': StartNode,
  'END': EndNode,
  'TEXT INPUT': TextInputNode,
  'NUMBER INPUT': NumberInputNode,
  'CHATBOX': ChatboxNode,
  'CHECKBOX': CheckboxNode,
  'DELAYTIMER': DelayTimerNode,
  'IFCONDITION': IfConditionNode,
  'LLM_Answer': LLMAnswerNode,
  'LLM_FileProduction': LLMFileProductionNode,
}

const node = props.node
const pos = ref({ x: node.x || 0, y: node.y || 0 })
const dragging = ref(false)
let start = { x: 0, y: 0, ox: 0, oy: 0 }

const styleObj = computed(() => ({ left: (node.x || pos.value.x) + 'px', top: (node.y || pos.value.y) + 'px', position: 'absolute', cursor: dragging.value ? 'grabbing' : 'grab' }))

const nodeComponent = computed(() => mapping[node.type] || StartNode)

function onClick(payload?: any) { emit('select', node) }

function onChildChange(updated: any) {
  // child emits change with node; ensure parent knows
  emit('moved', updated || node)
}

function startDrag(e: MouseEvent) {
  dragging.value = true
  start.x = e.clientX
  start.y = e.clientY
  start.ox = node.x || 0
  start.oy = node.y || 0
  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}

function onMove(e: MouseEvent) {
  if (!dragging.value) return
  const nx = start.ox + (e.clientX - start.x)
  const ny = start.oy + (e.clientY - start.y)
  pos.value.x = nx
  pos.value.y = ny
  node.x = Math.round(nx)
  node.y = Math.round(ny)
  emit('moved', node)
}

function onUp() {
  if (!dragging.value) return
  dragging.value = false
  window.removeEventListener('mousemove', onMove)
  window.removeEventListener('mouseup', onUp)
  emit('moved', node)
}

function startTouch(e: TouchEvent) {
  const t = e.touches[0]
  dragging.value = true
  start.x = t.clientX
  start.y = t.clientY
  start.ox = node.x || 0
  start.oy = node.y || 0
  window.addEventListener('touchmove', onTouchMove)
  window.addEventListener('touchend', onTouchEnd)
}

function onTouchMove(e: TouchEvent) {
  if (!dragging.value) return
  const t = e.touches[0]
  const nx = start.ox + (t.clientX - start.x)
  const ny = start.oy + (t.clientY - start.y)
  pos.value.x = nx
  pos.value.y = ny
  node.x = Math.round(nx)
  node.y = Math.round(ny)
  emit('moved', node)
}

function onTouchEnd() {
  dragging.value = false
  window.removeEventListener('touchmove', onTouchMove)
  window.removeEventListener('touchend', onTouchEnd)
  emit('moved', node)
}

onBeforeUnmount(() => {
  window.removeEventListener('mousemove', onMove)
  window.removeEventListener('mouseup', onUp)
  window.removeEventListener('touchmove', onTouchMove)
  window.removeEventListener('touchend', onTouchEnd)
})
</script>

<style scoped>
.node-wrap { width:160px; height:72px; user-select:none }
</style>
