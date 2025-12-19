<template>
  <div class="asset-dependencies-tab">
    <div class="tab-header mb-3">
      <Button 
        :label="t('assetDependencies.addDependency')" 
        icon="pi pi-plus" 
        @click="showAddDialog = true"
        v-if="canWrite"
      />
    </div>

    <TabView>
      <TabPanel>
        <template #header>
          <span style="display: flex; align-items: center; gap: 0.4em;">
            <i class="pi pi-arrow-right"></i> {{ t('assetDependencies.dependencies') }} ({{ dependencies.length }})
          </span>
        </template>
        <DependenciesTable 
          :dependencies="dependencies"
          :loading="loadingDependencies"
          :canWrite="canWrite"
          @delete="handleDelete"
        />
      </TabPanel>
      <TabPanel>
        <template #header>
          <span style="display: flex; align-items: center; gap: 0.4em;">
            <i class="pi pi-arrow-left"></i> {{ t('assetDependencies.dependents') }} ({{ dependents.length }})
          </span>
        </template>
        <DependenciesTable 
          :dependencies="dependents"
          :loading="loadingDependents"
          :canWrite="canWrite"
          @delete="handleDelete"
          :isDependents="true"
        />
      </TabPanel>
    </TabView>

    <!-- Add Dependency Dialog -->
    <Dialog 
      v-model:visible="showAddDialog" 
      :header="t('assetDependencies.addDependency')" 
      modal 
      :closable="true" 
      :dismissableMask="true"
      :style="{ width: '600px' }"
      :contentStyle="{ overflow: 'visible' }"
      :baseZIndex="10000"
    >
      <AssetDependencyForm 
        :assetId="assetId"
        @submit="handleAdd"
        @cancel="showAddDialog = false"
      />
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import Dialog from 'primevue/dialog'
import DependenciesTable from './components/DependenciesTable.vue'
import AssetDependencyForm from './components/AssetDependencyForm.vue'
import api from '@/api/api'

const props = defineProps({
  assetId: { type: [String, Number], required: true },
  canWrite: { type: Boolean, default: false }
})

const emit = defineEmits(['updated'])
const { t } = useI18n()
const toast = useToast()

const dependencies = ref([])
const dependents = ref([])
const loadingDependencies = ref(false)
const loadingDependents = ref(false)
const showAddDialog = ref(false)

async function fetchDependencies() {
  loadingDependencies.value = true
  try {
    const res = await api.getDependenciesForAsset(props.assetId)
    const deps = res.data || []
    
    // Carica lo stato delle connessioni per ogni dipendenza
    for (const dep of deps) {
      try {
        const connStatusRes = await api.get(`/asset-dependencies/${dep.id}/connection-status`)
        dep.connection_status = connStatusRes.data
      } catch (err) {
        // Se l'endpoint non esiste ancora, usa il servizio alternativo
        dep.connection_status = { has_connection: false, status: 'logical_only' }
      }
    }
    
    dependencies.value = deps
  } catch (error) {
    console.error('Error fetching dependencies:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: t('assetDependencies.errorLoading') })
  } finally {
    loadingDependencies.value = false
  }
}

async function fetchDependents() {
  loadingDependents.value = true
  try {
    const res = await api.getDependentsOfAsset(props.assetId)
    const deps = res.data || []
    
    // Carica lo stato delle connessioni per ogni dipendenza
    for (const dep of deps) {
      try {
        const connStatusRes = await api.get(`/asset-dependencies/${dep.id}/connection-status`)
        dep.connection_status = connStatusRes.data
      } catch (err) {
        // Se l'endpoint non esiste ancora, usa il servizio alternativo
        dep.connection_status = { has_connection: false, status: 'logical_only' }
      }
    }
    
    dependents.value = deps
  } catch (error) {
    console.error('Error fetching dependents:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: t('assetDependencies.errorLoading') })
  } finally {
    loadingDependents.value = false
  }
}


async function handleAdd(dependencyData) {
  try {
    await api.createAssetDependency(dependencyData)
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('assetDependencies.dependencyAdded') })
    showAddDialog.value = false
    await Promise.all([fetchDependencies(), fetchDependents()])
    emit('updated')
  } catch (error) {
    console.error('Error adding dependency:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: error.response?.data?.detail || t('assetDependencies.errorAdding') })
  }
}

async function handleDelete(dependencyId) {
  try {
    await api.deleteAssetDependency(dependencyId)
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('assetDependencies.dependencyDeleted') })
    await Promise.all([fetchDependencies(), fetchDependents()])
    emit('updated')
  } catch (error) {
    console.error('Error deleting dependency:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: error.response?.data?.detail || t('assetDependencies.errorDeleting') })
  }
}

onMounted(async () => {
  await Promise.all([fetchDependencies(), fetchDependents()])
})

watch(() => props.assetId, async (newId, oldId) => {
  if (newId !== oldId) {
    await Promise.all([fetchDependencies(), fetchDependents()])
  }
})
</script>

<style scoped>
.asset-dependencies-tab {
  padding: 1rem 0;
}

.tab-header {
  display: flex;
  justify-content: flex-end;
}
</style>

