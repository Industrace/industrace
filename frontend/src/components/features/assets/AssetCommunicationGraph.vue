<!--
  - AssetCommunicationGraph.vue
  - Componente per il grafico delle comunicazioni degli asset
  - Utilizza i componenti PrimeVue per la gestione del form
-->
<template>
  <div class="asset-comm-graph">
    <div class="graph-controls mb-2">
      <Button icon="pi pi-plus" size="small" @click="zoomIn" title="Zoom in" />
      <Button icon="pi pi-minus" size="small" @click="zoomOut" title="Zoom out" />
      <Button icon="pi pi-refresh" size="small" @click="resetView" title="Reset view" />
      <Button icon="pi pi-arrows-alt" size="small" @click="fitToScreen" title="Fit to screen" />
    </div>
    <div ref="networkContainer" class="network-container"></div>
    <div v-if="!nodes.length || !edges.length" class="placeholder">
      <span>{{ t('assetCommunications.noGraphData') }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import { Network } from 'vis-network'
import Button from 'primevue/button'
const props = defineProps({
  type: { type: String, default: 'physical' },
  nodes: { type: Array, default: () => [] },
  edges: { type: Array, default: () => [] }
})
const { t } = useI18n()
const networkContainer = ref(null)
let networkInstance = null

function renderNetwork() {
  const nodes = Array.isArray(props.nodes) ? props.nodes : (props.nodes?.value || [])
  const edges = Array.isArray(props.edges) ? props.edges : (props.edges?.value || [])
  if (!networkContainer.value || !Network) return
  const data = { nodes, edges }
  const options = {
    nodes: { shape: 'dot', size: 18, font: { size: 14 } },
    edges: { color: props.type === 'physical' ? '#2196f3' : '#43a047', width: 2, smooth: { type: 'dynamic' } },
    physics: {
      enabled: true,
      barnesHut: {
        gravitationalConstant: -30000,
        springLength: 120
      }
    },
    interaction: { hover: true, tooltipDelay: 200, zoomView: false, dragView: true },
    manipulation: { enabled: false }
  }
  if (networkInstance) {
    // Rimuovi il listener passivo precedente se esiste
    if (networkContainer.value && networkInstance._passiveWheelHandler) {
      networkContainer.value.removeEventListener('wheel', networkInstance._passiveWheelHandler)
    }
    networkInstance.destroy()
  }
  networkInstance = new Network(networkContainer.value, data, options)
  
  // Aggiungi listener passivo per gestire lo zoom con la rotella
  // Nota: vis-network aggiunge internamente un listener non-passivo, ma disabilitando
  // zoomView: false evitiamo che gestisca lo zoom, e lo gestiamo noi manualmente
  if (networkContainer.value) {
    const handleWheel = (e) => {
      if (networkInstance && networkInstance.getScale) {
        // Non chiamiamo preventDefault per mantenere il listener passivo
        // Lo zoom viene gestito solo quando il mouse è sopra il container
        const scale = networkInstance.getScale()
        const delta = e.deltaY > 0 ? 0.9 : 1.1
        networkInstance.moveTo({ scale: scale * delta })
      }
    }
    
    // Aggiungi listener passivo (senza preventDefault)
    networkContainer.value.addEventListener('wheel', handleWheel, { passive: true })
    
    // Salva il riferimento per poterlo rimuovere in cleanup
    networkInstance._passiveWheelHandler = handleWheel
  }
  
  setTimeout(() => { if (networkInstance) networkInstance.fit() }, 200)
}

function zoomIn() {
  if (networkInstance) {
    const scale = networkInstance.getScale()
    networkInstance.moveTo({ scale: scale * 1.2 })
  }
}
function zoomOut() {
  if (networkInstance) {
    const scale = networkInstance.getScale()
    networkInstance.moveTo({ scale: scale / 1.2 })
  }
}
function resetView() {
  if (networkInstance) {
    networkInstance.fit()
  }
}
function fitToScreen() {
  if (networkInstance) {
    networkInstance.fit()
  }
}

watch(() => [props.nodes, props.edges], (...args) => {
  renderNetwork()
}, { deep: true })
onMounted(() => {
  renderNetwork()
})
onBeforeUnmount(() => {
  if (networkInstance) {
    // Rimuovi il listener passivo prima di distruggere l'istanza
    if (networkContainer.value && networkInstance._passiveWheelHandler) {
      networkContainer.value.removeEventListener('wheel', networkInstance._passiveWheelHandler)
    }
    networkInstance.destroy()
  }
})
</script>

<style scoped>
.asset-comm-graph {
  min-height: 300px;
  margin-bottom: 1.5em;
}
.network-container {
  width: 100%;
  height: 350px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fafbfc;
}
.placeholder {
  text-align: center;
  color: #888;
  padding: 2em 0;
}
.graph-controls {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.5em;
}
.graph-controls .p-button {
  min-width: 2rem;
}
</style>
