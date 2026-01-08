<template>
  <div class="evidence-list">
    <div class="flex justify-content-between align-items-center mb-3">
      <h4>
        <i class="pi pi-file mr-2"></i>
        {{ t('isa62443.evidence.title') }}
      </h4>
      <Button 
        v-if="canWrite"
        :label="t('isa62443.evidence.addEvidence')" 
        icon="pi pi-plus" 
        size="small"
        @click="showAddDialog = true"
      />
    </div>
    
    <div v-if="loading" class="text-center p-4">
      <ProgressSpinner />
    </div>
    
    <div v-else-if="evidences.length === 0" class="text-center p-4 text-600">
      <i class="pi pi-info-circle text-2xl mb-2"></i>
      <p>{{ t('isa62443.evidence.noEvidence') }}</p>
    </div>
    
    <DataTable 
      v-else
      :value="evidences" 
      class="p-datatable-sm"
      :paginator="evidences.length > 10"
      :rows="10"
    >
      <Column field="description" :header="t('isa62443.evidence.description')" sortable>
        <template #body="{ data }">
          <div class="evidence-description">
            {{ data.description }}
            <span v-if="data.type" class="text-600 text-sm ml-2">({{ data.type }})</span>
          </div>
        </template>
      </Column>
      
      <Column field="source" :header="t('isa62443.evidence.source')" sortable>
        <template #body="{ data }">
          <Tag 
            :value="getSourceLabel(data.source)" 
            :severity="getSourceSeverity(data.source)" 
          />
        </template>
      </Column>
      
      <Column field="confidence" :header="t('isa62443.evidence.confidence')" sortable>
        <template #body="{ data }">
          <span v-if="data.confidence !== null && data.confidence !== undefined">
            <ProgressBar :value="data.confidence * 100" :showValue="false" class="evidence-confidence-bar" />
            <span class="ml-2">{{ Math.round(data.confidence * 100) }}%</span>
          </span>
          <span v-else class="text-600">-</span>
        </template>
      </Column>
      
      <Column :header="t('common.strings.actions')" v-if="canWrite">
        <template #body="{ data }">
          <Button 
            icon="pi pi-pencil" 
            class="p-button-text p-button-sm"
            @click="editEvidence(data)"
            :title="t('isa62443.evidence.editEvidence')"
          />
          <Button 
            icon="pi pi-trash" 
            class="p-button-text p-button-sm p-button-danger"
            @click="deleteEvidence(data)"
            :title="t('isa62443.evidence.deleteEvidence')"
          />
        </template>
      </Column>
    </DataTable>
    
    <!-- Dialog Add/Edit Evidence -->
    <Dialog 
      v-model:visible="showAddDialog" 
      :header="editingEvidence ? t('isa62443.evidence.editEvidence') : t('isa62443.evidence.addEvidence')"
      :modal="true"
      :style="{ width: '600px' }"
    >
      <div class="field mb-3">
        <label class="mb-2">{{ t('isa62443.evidence.source') }} *</label>
        <Dropdown 
          v-model="form.source" 
          :options="sourceOptions"
          optionLabel="label"
          optionValue="value"
          class="w-full"
          :disabled="!!editingEvidence"
        />
      </div>
      
      <div class="field mb-3">
        <label class="mb-2">{{ t('isa62443.evidence.type') }}</label>
        <InputText 
          v-model="form.type" 
          class="w-full"
          :placeholder="t('isa62443.evidence.typePlaceholder')"
        />
      </div>
      
      <div class="field mb-3">
        <label class="mb-2">{{ t('isa62443.evidence.description') }} *</label>
        <Textarea 
          v-model="form.description" 
          class="w-full"
          :rows="4"
          :placeholder="t('isa62443.evidence.descriptionPlaceholder')"
        />
      </div>
      
      <div class="field mb-3">
        <label class="mb-2">{{ t('isa62443.evidence.confidence') }}</label>
        <div class="flex align-items-center gap-3">
          <InputNumber 
            v-model="form.confidence" 
            :min="0" 
            :max="1" 
            :step="0.1" 
            :showButtons="true"
            :minFractionDigits="1"
            :maxFractionDigits="2"
            class="flex-1"
          />
          <span class="text-600 text-sm">{{ t('isa62443.evidence.confidenceHint') }}</span>
        </div>
      </div>
      
      <template #footer>
        <Button 
          :label="t('common.actions.cancel')" 
          icon="pi pi-times" 
          @click="showAddDialog = false" 
          class="p-button-text"
        />
        <Button 
          :label="t('common.actions.save')" 
          icon="pi pi-check" 
          @click="saveEvidence" 
          :disabled="!form.source || !form.description"
        />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import InputNumber from 'primevue/inputnumber'
import Tag from 'primevue/tag'
import ProgressBar from 'primevue/progressbar'
import ProgressSpinner from 'primevue/progressspinner'
import api from '@/api/api'

const props = defineProps({
  srAssessmentId: { type: String, required: false },
  zoneId: { type: String, required: false },
  capabilityId: { type: String, required: false },
  assetId: { type: String, required: false },
  canWrite: { type: Boolean, default: true }
})

const emit = defineEmits(['evidence-updated'])

const { t } = useI18n()
const toast = useToast()

const loading = ref(false)
const evidences = ref([])
const showAddDialog = ref(false)
const editingEvidence = ref(null)

const form = ref({
  source: 'manual',
  type: null,
  description: '',
  confidence: null,
  sr_assessment_id: props.srAssessmentId || null,
  zone_id: props.zoneId || null,
  capability_id: props.capabilityId || null,
  asset_id: props.assetId || null
})

const sourceOptions = [
  { label: t('isa62443.evidence.sources.manual'), value: 'manual' },
  { label: t('isa62443.evidence.sources.document'), value: 'document' },
  { label: t('isa62443.evidence.sources.import'), value: 'import' },
  { label: t('isa62443.evidence.sources.probe'), value: 'probe' }
]

// Watch for prop changes to update form
watch(() => props.srAssessmentId, (newVal) => {
  if (newVal) form.value.sr_assessment_id = newVal
})

watch(() => props.zoneId, (newVal) => {
  if (newVal) form.value.zone_id = newVal
})

watch(() => props.capabilityId, (newVal) => {
  if (newVal) form.value.capability_id = newVal
})

watch(() => props.assetId, (newVal) => {
  if (newVal) form.value.asset_id = newVal
})

async function fetchEvidences() {
  loading.value = true
  try {
    const params = {}
    if (props.srAssessmentId) params.sr_assessment_id = props.srAssessmentId
    if (props.zoneId) params.zone_id = props.zoneId
    if (props.capabilityId) params.capability_id = props.capabilityId
    if (props.assetId) params.asset_id = props.assetId
    
    const res = await api.getEvidences(params)
    evidences.value = res.data || []
  } catch (error) {
    console.error('Error fetching evidences:', error)
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: t('isa62443.evidence.errorLoading'),
      life: 3000
    })
    evidences.value = []
  } finally {
    loading.value = false
  }
}

function resetForm() {
  editingEvidence.value = null
  form.value = {
    source: 'manual',
    type: null,
    description: '',
    confidence: null,
    sr_assessment_id: props.srAssessmentId || null,
    zone_id: props.zoneId || null,
    capability_id: props.capabilityId || null,
    asset_id: props.assetId || null
  }
}

async function saveEvidence() {
  if (!form.value.source || !form.value.description) {
    toast.add({
      severity: 'warn',
      summary: t('common.messages.warning'),
      detail: t('isa62443.evidence.fillRequiredFields'),
      life: 3000
    })
    return
  }

  try {
    if (editingEvidence.value) {
      await api.updateEvidence(editingEvidence.value.id, form.value)
      toast.add({
        severity: 'success',
        summary: t('common.messages.success'),
        detail: t('isa62443.evidence.evidenceUpdated'),
        life: 3000
      })
    } else {
      await api.createEvidence(form.value)
      toast.add({
        severity: 'success',
        summary: t('common.messages.success'),
        detail: t('isa62443.evidence.evidenceAdded'),
        life: 3000
      })
    }
    
    showAddDialog.value = false
    resetForm()
    await fetchEvidences()
    emit('evidence-updated')
  } catch (error) {
    console.error('Error saving evidence:', error)
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: error.response?.data?.detail || t('isa62443.evidence.errorSaving'),
      life: 3000
    })
  }
}

function editEvidence(evidence) {
  editingEvidence.value = evidence
  form.value = {
    source: evidence.source,
    type: evidence.type || null,
    description: evidence.description,
    confidence: evidence.confidence || null,
    sr_assessment_id: evidence.sr_assessment_id || props.srAssessmentId || null,
    zone_id: evidence.zone_id || props.zoneId || null,
    capability_id: evidence.capability_id || props.capabilityId || null,
    asset_id: evidence.asset_id || props.assetId || null
  }
  showAddDialog.value = true
}

async function deleteEvidence(evidence) {
  if (!confirm(t('isa62443.evidence.confirmDelete'))) {
    return
  }
  
  try {
    await api.deleteEvidence(evidence.id)
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: t('isa62443.evidence.evidenceDeleted'),
      life: 3000
    })
    await fetchEvidences()
    emit('evidence-updated')
  } catch (error) {
    console.error('Error deleting evidence:', error)
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: error.response?.data?.detail || t('isa62443.evidence.errorDeleting'),
      life: 3000
    })
  }
}

function getSourceLabel(source) {
  return sourceOptions.find(o => o.value === source)?.label || source
}

function getSourceSeverity(source) {
  const map = { 
    manual: 'info', 
    document: 'success', 
    import: 'warning', 
    probe: 'secondary' 
  }
  return map[source] || 'info'
}

onMounted(() => {
  fetchEvidences()
})

// Expose fetch function for parent components
defineExpose({
  fetchEvidences,
  refresh: fetchEvidences
})
</script>

<style scoped>
.evidence-list {
  margin-top: 1rem;
}

.evidence-description {
  word-break: break-word;
}

.evidence-confidence-bar {
  width: 100px;
  height: 0.5rem;
}

.text-sm {
  font-size: 0.875rem;
}
</style>

