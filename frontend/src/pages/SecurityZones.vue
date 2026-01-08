<template>
  <div class="security-zones-page">
    <div class="page-header">
      <h1>{{ t('isa62443.securityZones.title') }}</h1>
      <div class="header-actions">
        <Button 
          v-if="canWrite('security_zones')"
          :label="t('isa62443.securityZones.createZone')" 
          icon="pi pi-plus" 
          @click="showCreateDialog = true"
        />
      </div>
    </div>

    <DataTable 
      :value="zones" 
      :loading="loading"
      :emptyMessage="t('isa62443.securityZones.noZones')"
      :paginator="true"
      :rows="20"
      class="p-datatable-sm"
    >
      <Column field="name" :header="t('common.fields.name')" sortable>
        <template #body="{ data }">
          <a 
            @click="goToZone(data.id)" 
            class="zone-link"
          >
            {{ data.name }}
          </a>
        </template>
      </Column>
      <Column field="zone_type" :header="t('isa62443.securityZones.zoneType')" sortable />
      <Column :header="t('isa62443.securityZones.securityLevel')">
        <template #body="{ data }">
          <div class="flex align-items-center gap-2">
            <span>SL-{{ data.security_level_target || '-' }}</span>
            <Tag 
              v-if="data.security_level_achieved"
              :value="`SL-A: ${data.security_level_achieved}`"
              :severity="getSLAseverity(data.security_level_achieved, data.security_level_target)"
            />
          </div>
        </template>
      </Column>
      <Column field="compliance_status" :header="t('isa62443.compliance.status')" sortable>
        <template #body="{ data }">
          <Tag 
            :value="getComplianceLabel(data.compliance_status)" 
            :severity="getComplianceSeverity(data.compliance_status)" 
          />
        </template>
      </Column>
      <Column :header="t('common.strings.actions')">
        <template #body="{ data }">
          <div class="flex gap-2">
            <Button 
              v-if="canWrite('security_zones')"
              icon="pi pi-pencil" 
              class="p-button-rounded p-button-text" 
              @click="editZone(data)" 
              :title="t('common.actions.edit')"
              v-tooltip.top="t('common.actions.edit')"
            />
            <Button 
              v-if="canDelete('security_zones')"
              icon="pi pi-trash" 
              class="p-button-rounded p-button-text p-button-danger" 
              @click="deleteZone(data.id)" 
              :title="t('common.actions.delete')"
              v-tooltip.top="t('common.actions.delete')"
            />
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- Create/Edit Dialog -->
    <Dialog 
      :visible="showDialog" 
      @update:visible="(val) => { if (!val) closeDialog() }"
      :header="showEditDialog ? t('isa62443.securityZones.editZone') : t('isa62443.securityZones.createZone')" 
      modal 
      :closable="true" 
      :dismissableMask="true"
      style="width: 700px"
    >
      <SecurityZoneForm 
        v-if="showCreateDialog || showEditDialog"
        :zone="editingZone"
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
import { useRouter } from 'vue-router'
import { usePermissions } from '@/composables/usePermissions'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Dialog from 'primevue/dialog'
import SecurityZoneForm from '../components/features/isa62443/SecurityZoneForm.vue'
import api from '@/api/api'

const { t } = useI18n()
const toast = useToast()
const router = useRouter()
const { canWrite, canDelete } = usePermissions()

const zones = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const editingZone = ref(null)

const showDialog = computed(() => showCreateDialog.value || showEditDialog.value)

const goToZone = (zoneId) => {
  router.push(`/security-zones/${zoneId}`)
}

const getSLAseverity = (achieved, target) => {
  if (!achieved || !target) return 'info'
  if (achieved >= target) return 'success'
  if (achieved >= target - 1) return 'warning'
  return 'danger'
}

const getComplianceLabel = (status) => {
  const labels = {
    'compliant': t('isa62443.compliance.compliant'),
    'non_compliant': t('isa62443.compliance.nonCompliant'),
    'partial': t('isa62443.compliance.partial'),
    'not_assessed': t('isa62443.compliance.notAssessed')
  }
  return labels[status] || status
}

const getComplianceSeverity = (status) => {
  const severityMap = {
    'compliant': 'success',
    'non_compliant': 'danger',
    'partial': 'warning',
    'not_assessed': 'info'
  }
  return severityMap[status] || null
}

async function fetchZones() {
  loading.value = true
  try {
    const res = await api.getSecurityZones()
    zones.value = res.data || []
  } catch (error) {
    console.error('Error fetching zones:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: t('isa62443.securityZones.errorLoading') })
  } finally {
    loading.value = false
  }
}

function editZone(zone) {
  editingZone.value = zone
  showEditDialog.value = true
}

function closeDialog() {
  showCreateDialog.value = false
  showEditDialog.value = false
  editingZone.value = null
}

async function handleSubmit(zoneData) {
  try {
    if (editingZone.value) {
      await api.updateSecurityZone(editingZone.value.id, zoneData)
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('isa62443.securityZones.zoneUpdated') })
    } else {
      await api.createSecurityZone(zoneData)
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('isa62443.securityZones.zoneCreated') })
    }
    closeDialog()
    await fetchZones()
  } catch (error) {
    console.error('Error saving zone:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: error.response?.data?.detail || t('isa62443.securityZones.errorSaving') })
  }
}

async function deleteZone(zoneId) {
  if (!confirm(t('isa62443.securityZones.confirmDelete'))) return
  
  try {
    await api.deleteSecurityZone(zoneId)
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('isa62443.securityZones.zoneDeleted') })
    await fetchZones()
  } catch (error) {
    console.error('Error deleting zone:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: error.response?.data?.detail || t('isa62443.securityZones.errorDeleting') })
  }
}

onMounted(async () => {
  await fetchZones()
})
</script>

<style scoped>
.security-zones-page {
  padding: 1.5rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.zone-link {
  color: var(--primary-color);
  cursor: pointer;
  text-decoration: none;
}

.zone-link:hover {
  text-decoration: underline;
}
</style>

