<template>
  <div class="toolbox">
    <h4>Nodes</h4>
    <ul>
      <li v-for="t in types" :key="t" draggable @dragstart="onDragStart($event, t)">{{ t }}</li>
    </ul>
  </div>
</template>

<script setup lang="ts">
const types = [
  'Start','END','TEXT INPUT','NUMBER INPUT','CHATBOX','CHECKBOX','DELAYTIMER','IFCONDITION','LLM_Answer','LLM_FileProduction'
]

function onDragStart(e: DragEvent, t: string) {
  e.dataTransfer?.setData('application/node-type', t)
}
</script>

<style scoped>
.toolbox { width:240px; padding:12px; background:rgba(255,255,255,0.02); border-right:1px solid rgba(255,255,255,0.03) }
.toolbox h4 { color:#9fb0ff; margin:0 0 8px 0 }
.toolbox ul { list-style:none; padding:0; margin:0 }
.toolbox li { padding:8px; margin-bottom:6px; background:rgba(255,255,255,0.02); border-radius:6px; cursor:grab }
</style>
