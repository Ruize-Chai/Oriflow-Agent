<template>
  <svg class="edge-container" :width="canvasWidth" :height="canvasHeight">
    <defs>
      <marker id="arrowhead-active" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
        <polygon points="0 0, 10 3, 0 6" fill="var(--accent-glow)" />
      </marker>
      <marker id="arrowhead-idle" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
        <polygon points="0 0, 10 3, 0 6" fill="rgba(100,116,139,0.3)" />
      </marker>
    </defs>
    <g v-for="edge in edges" :key="edge.id">
      <path
        :d="computePath(edge.from, edge.to)"
        :class="['edge-path', { active: isEdgeActive(edge) }]"
        :marker-end="isEdgeActive(edge) ? 'url(#arrowhead-active)' : 'url(#arrowhead-idle)'"
      />
    </g>
  </svg>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'

interface Edge {
  id: string | number
  from: number // node id
  to: number   // node id
}

interface Node {
  id: number
  x: number
  y: number
}

const props = defineProps<{
  nodes?: Node[]
  edges?: Edge[]
  activeEdges?: (string | number)[]
}>()

const canvasWidth = ref(0)
const canvasHeight = ref(0)

onMounted(() => {
  const container = document.querySelector('.canvas')
  if (container) {
    canvasWidth.value = container.clientWidth
    canvasHeight.value = container.clientHeight
  }
  window.addEventListener('resize', updateCanvasDimensions)
})

function updateCanvasDimensions() {
  const container = document.querySelector('.canvas')
  if (container) {
    canvasWidth.value = container.clientWidth
    canvasHeight.value = container.clientHeight
  }
}

// 计算贝塞尔曲线路径
function computePath(fromNodeId: number, toNodeId: number): string {
  const fromNode = props.nodes?.find(n => n.id === fromNodeId)
  const toNode = props.nodes?.find(n => n.id === toNodeId)

  if (!fromNode || !toNode) return ''

  // 节点中心点（加上节点宽高的一半）
  const x1 = fromNode.x + 80
  const y1 = fromNode.y + 36
  const x2 = toNode.x + 80
  const y2 = toNode.y + 36

  // 计算控制点（控制贝塞尔曲线的弧度）
  const dx = (x2 - x1) * 0.35
  const cp1x = x1 + dx
  const cp1y = y1
  const cp2x = x2 - dx
  const cp2y = y2

  return `M ${x1} ${y1} C ${cp1x} ${cp1y} ${cp2x} ${cp2y} ${x2} ${y2}`
}

function isEdgeActive(edge: Edge): boolean {
  return props.activeEdges?.includes(edge.id) || false
}

const edges = computed(() => props.edges || [])
</script>

<style scoped>
.edge-container {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.edge-path {
  stroke: rgba(100, 116, 139, 0.3);
  stroke-width: 2;
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
  transition: stroke 0.3s, filter 0.3s;
}

.edge-path.active {
  stroke: var(--accent-glow);
  stroke-width: 2.5;
  filter: drop-shadow(0 0 8px rgba(0, 212, 255, 0.5));
  stroke-dasharray: 8, 4;
  animation: flow 3s linear infinite;
}

.edge-path:hover {
  stroke: rgba(0, 212, 255, 0.6);
  stroke-width: 2.5;
}

@keyframes flow {
  0% {
    stroke-dashoffset: 1000;
  }
  100% {
    stroke-dashoffset: 0;
  }
}
</style>
