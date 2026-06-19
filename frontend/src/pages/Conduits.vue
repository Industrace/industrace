<template>
  <div class="conduits-page">
    <div class="page-header">
      <h1>{{ t('isa62443.conduits.title') }}</h1>
      <div class="header-actions">
        <Button 
          :label="t('isa62443.conduits.createConduit')" 
          icon="pi pi-plus" 
          @click="showCreateDialog = true"
        />
      </div>
    </div>

    <DataTable 
      :value="conduits" 
      :loading="loading"
      :emptyMessage="t('isa62443.conduits.noConduits')"
      :paginator="true"
      :rows="20"
      class="p-datatable-sm"
    >
      <Column field="name" :header="t('common.fields.name')" sortable />
      <Column :header="t('isa62443.conduits.fromZone')" sortable sortField="from_zone_id">
        <template #body="{ data }">
          {{ getZoneName(data.from_zone_id) }}
        </template>
      </Column>
      <Column :header="t('isa62443.conduits.toZone')" sortable sortField="to_zone_id">
        <template #body="{ data }">
          {{ getZoneName(data.to_zone_id) }}
        </template>
      </Column>
      <Column field="conduit_type" :header="t('isa62443.conduits.conduitType')" sortable />
      <Column :header="t('isa62443.securityZones.securityLevel')">
        <template #body="{ data }">
          <div class="flex flex-column gap-1">
            <span>SL-T: {{ data.security_level_target || '-' }}</span>
            <span v-if="data.security_level_achieved">
              SL-A: {{ data.security_level_achieved }}
              <Tag
                v-if="data.sl_achieved_source === 'preliminary'"
                :value="t('isa62443.conduits.slAchievedPreliminary')"
                severity="warning"
                class="ml-1"
              />
            </span>
          </div>
        </template>
      </Column>
      <Column :header="t('common.strings.actions')">
        <template #body="{ data }">
          <div class="flex gap-2">
            <Button 
              icon="pi pi-pencil" 
              class="p-button-rounded p-button-text" 
              @click="editConduit(data)" 
            />
            <Button 
              icon="pi pi-trash" 
              class="p-button-rounded p-button-text p-button-danger" 
              @click="deleteConduit(data.id)" 
            />
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- Create/Edit Dialog -->
    <Dialog 
      :visible="showDialog" 
      @update:visible="(val) => { if (!val) closeDialog() }"
      :header="showEditDialog ? t('isa62443.conduits.editConduit') : t('isa62443.conduits.createConduit')" 
      modal 
      :closable="true" 
      :dismissableMask="true"
      style="width: 800px"
    >
      <ConduitForm 
        v-if="showCreateDialog || showEditDialog"
        :conduit="editingConduit"
        :zones="zones"
        @submit="handleSubmit"
        @cancel="closeDialog"
      />
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import Tag from 'primevue/tag'
import ConduitForm from '../components/features/isa62443/ConduitForm.vue'
import api from '@/api/api'

const { t } = useI18n()
const toast = useToast()

const conduits = ref([])
const zones = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const editingConduit = ref(null)

const showDialog = computed(() => showCreateDialog.value || showEditDialog.value)

const getZoneName = (zoneId) => {
  const zone = zones.value.find(z => z.id === zoneId)
  return zone ? zone.name : '-'
}

async function fetchConduits() {
  loading.value = true
  try {
    const res = await api.getConduits()
    conduits.value = res.data || []
  } catch (error) {
    console.error('Error fetching conduits:', error)
    toast.add({ severity: 'error', summary: t('common.messages.error'), detail: t('isa62443.conduits.errorLoading') })
  } finally {
    loading.value = false
  }
}

async function fetchZones() {
  try {
    const res = await api.getSecurityZones()
    zones.value = res.data || []
  } catch (error) {
    console.error('Error fetching zones:', error)
  }
}

function editConduit(conduit) {
  editingConduit.value = conduit
  showEditDialog.value = true
}

function closeDialog() {
  showCreateDialog.value = false
  showEditDialog.value = false
  editingConduit.value = null
}

async function handleSubmit(conduitData) {
  try {
    if (editingConduit.value) {
      await api.updateConduit(editingConduit.value.id, conduitData)
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('isa62443.conduits.conduitUpdated') })
    } else {
      await api.createConduit(conduitData)
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('isa62443.conduits.conduitCreated') })
    }
    closeDialog()
    await fetchConduits()
  } catch (error) {
    console.error('Error saving conduit:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: error.response?.data?.detail || t('isa62443.conduits.errorSaving') })
  }
}

async function deleteConduit(conduitId) {
  if (!confirm(t('isa62443.conduits.confirmDelete'))) return
  
  try {
    await api.deleteConduit(conduitId)
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('isa62443.conduits.conduitDeleted') })
    await fetchConduits()
  } catch (error) {
    console.error('Error deleting conduit:', error)
    toast.add({ severity: 'error', summary: t('common.messages.error'), detail: error.response?.data?.detail || t('isa62443.conduits.errorDeleting') })
  }
}

onMounted(async () => {
  await Promise.all([fetchConduits(), fetchZones()])
})
</script>

<style scoped>
.conduits-page {
  padding: 1.5rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}
</style>

