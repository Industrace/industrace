<template>
  <div class="asset-relations-tab">
    <!-- Grafico Relazioni (sempre visibile, grande) -->
    <div class="relations-graph-section card p-4 mb-4">
      <h3 class="mt-0 mb-3">{{ t('assets.relations.graphTitle') }}</h3>
      <div class="graph-placeholder">
        <p class="text-center text-600">
          <i class="pi pi-sitemap" style="font-size: 3rem; color: var(--text-color-secondary);"></i>
        </p>
        <p class="text-center text-600">{{ t('assets.relations.graphPlaceholder') }}</p>
        <p class="text-center text-sm text-500">{{ t('assets.relations.graphComingSoon') }}</p>
      </div>
    </div>

    <!-- Riepilogo Relazioni -->
    <div class="relations-summary card p-4 mb-4">
      <div class="grid">
        <div class="col-12 md:col-3">
          <div class="summary-card">
            <label class="text-600 text-sm">{{ t('assets.relations.dependsOn') }}</label>
            <div class="summary-value">{{ dependenciesCount }}</div>
          </div>
        </div>
        <div class="col-12 md:col-3">
          <div class="summary-card">
            <label class="text-600 text-sm">{{ t('assets.relations.dependents') }}</label>
            <div class="summary-value">{{ dependentsCount }}</div>
          </div>
        </div>
        <div class="col-12 md:col-3">
          <div class="summary-card">
            <label class="text-600 text-sm">{{ t('assets.relations.networkConnections') }}</label>
            <div class="summary-value">{{ connectionsCount }}</div>
          </div>
        </div>
        <div class="col-12 md:col-3">
          <div class="summary-card">
            <label class="text-600 text-sm">{{ t('assets.relations.communications') }}</label>
            <div class="summary-value">{{ communicationsCount }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Dipendenze (default espanso) -->
    <Accordion :activeIndex="[0]" class="mb-4">
      <AccordionTab :header="t('assets.tabs.dependencies')">
        <AssetDetailDependenciesTab :assetId="assetId" :canWrite="canWrite" @updated="$emit('updated')" />
      </AccordionTab>
    </Accordion>

    <!-- Connessioni di Rete (collassabile) -->
    <Accordion class="mb-4">
      <AccordionTab :header="t('assets.tabs.connections')">
        <AssetDetailConnectionsTab :assetId="assetId" :assetInterfaces="asset?.interfaces || []" />
      </AccordionTab>
    </Accordion>

    <!-- Comunicazioni (collassabile) -->
    <Accordion>
      <AccordionTab :header="t('assets.tabs.communications')">
        <AssetDetailCommunicationsTab :assetId="assetId" />
      </AccordionTab>
    </Accordion>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import Accordion from 'primevue/accordion'
import AccordionTab from 'primevue/accordiontab'
import AssetDetailDependenciesTab from '../tabs/AssetDetailDependenciesTab.vue'
import AssetDetailConnectionsTab from '../tabs/AssetDetailConnectionsTab.vue'
import AssetDetailCommunicationsTab from '../tabs/AssetDetailCommunicationsTab.vue'
import api from '../../../../api/api'

const props = defineProps({
  asset: { type: Object, required: true },
  assetId: { type: [String, Number], required: true },
  canWrite: { type: Function, required: true }
})

const emit = defineEmits(['updated'])

const { t } = useI18n()

const dependenciesCount = ref(0)
const dependentsCount = ref(0)
const connectionsCount = ref(0)
const communicationsCount = ref(0)

async function loadCounts() {
  try {
    // TODO: Caricare conteggi reali
    const [depsRes, depsRevRes] = await Promise.all([
      api.getAssetDependencies(props.assetId),
      api.getAssetDependents(props.assetId)
    ])
    dependenciesCount.value = depsRes.data?.length || 0
    dependentsCount.value = depsRevRes.data?.length || 0
    connectionsCount.value = props.asset?.interfaces?.length || 0
    // TODO: Caricare comunicazioni
    communicationsCount.value = 0
  } catch (e) {
    console.error('Error loading relation counts:', e)
  }
}

onMounted(() => {
  loadCounts()
})
</script>

<style scoped>
.asset-relations-tab {
  max-width: 1200px;
}

.graph-placeholder {
  min-height: 400px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 3rem;
  background: var(--surface-50);
  border-radius: 8px;
  border: 2px dashed var(--surface-border);
}

.summary-card {
  text-align: center;
  padding: 1rem;
}

.summary-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--primary-color);
  margin-top: 0.5rem;
}
</style>

