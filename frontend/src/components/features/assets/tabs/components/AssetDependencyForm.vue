<template>
  <div class="asset-dependency-form">
    <div class="p-fluid">
      <div class="field">
        <label>{{ t('assetDependencies.dependencyAsset') }} *</label>
        <div v-if="loadingAssets" class="p-2 text-center">
          <i class="pi pi-spin pi-spinner"></i> {{ t('common.messages.loading') }}
        </div>
        <Dropdown
          v-else
          v-model="formData.dependency_asset_id"
          :options="availableAssets"
          optionLabel="name"
          optionValue="id"
          :placeholder="t('assetDependencies.selectAsset')"
          :emptyMessage="t('assetDependencies.noAssetsAvailable')"
          filter
          filterPlaceholder="Cerca asset..."
          showClear
          required
          class="w-full"
          appendTo="body"
          :baseZIndex="10001"
        />
        <small v-if="availableAssets.length === 0 && !loadingAssets" class="p-error">
          {{ t('assetDependencies.noAssetsAvailable') }}
        </small>
        <small v-else-if="availableAssets.length > 0" class="p-text-secondary">
          {{ availableAssets.length }} {{ t('assetDependencies.assetsAvailable') }}
        </small>
      </div>
      <div class="field">
        <label>{{ t('assetDependencies.dependencyType') }} *</label>
        <Dropdown
          v-model="formData.dependency_type"
          :options="typeOptions"
          optionLabel="label"
          optionValue="value"
          required
        />
      </div>
      <div class="field">
        <label>{{ t('assetDependencies.criticality') }} *</label>
        <Dropdown
          v-model="formData.criticality"
          :options="criticalityOptions"
          optionLabel="label"
          optionValue="value"
          required
        />
      </div>
      <div class="field">
        <label>{{ t('assetDependencies.confidence') }} *</label>
        <Dropdown
          v-model="formData.confidence"
          :options="confidenceOptions"
          optionLabel="label"
          optionValue="value"
          required
        />
        <small class="p-text-secondary">{{ t('assetDependencies.confidenceHelp') }}</small>
      </div>
      <div class="field">
        <label>{{ t('assetDependencies.source') }}</label>
        <Dropdown
          v-model="formData.source"
          :options="sourceOptions"
          optionLabel="label"
          optionValue="value"
          :showClear="true"
          :placeholder="t('assetDependencies.sourcePlaceholder')"
        />
        <small class="p-text-secondary">{{ t('assetDependencies.sourceHelp') }}</small>
      </div>
      <div class="field">
        <label>{{ t('assetDependencies.description') }}</label>
        <Textarea v-model="formData.description" :rows="3" />
      </div>
      <div class="field">
        <label>{{ t('assetDependencies.notes') }}</label>
        <Textarea v-model="formData.notes" :rows="2" />
      </div>
      <div class="field-checkbox">
        <Checkbox 
          v-model="formData.is_bidirectional" 
          :binary="true"
          inputId="is_bidirectional"
        />
        <label for="is_bidirectional" class="ml-2">{{ t('assetDependencies.isBidirectional') }}</label>
      </div>
      <div class="flex justify-content-end gap-2 mt-3">
        <Button 
          :label="t('common.actions.save')" 
          icon="pi pi-check" 
          @click="handleSubmit"
        />
        <Button 
          :label="t('common.actions.cancel')" 
          icon="pi pi-times" 
          class="p-button-secondary" 
          @click="$emit('cancel')" 
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import Checkbox from 'primevue/checkbox'
import Button from 'primevue/button'
import api from '@/api/api'

const props = defineProps({
  assetId: { type: [String, Number], required: true },
  suggestedData: { type: Object, default: null }
})

const emit = defineEmits(['submit', 'cancel'])
const { t } = useI18n()
const toast = useToast()

const formData = ref({
  dependent_asset_id: props.assetId,
  dependency_asset_id: null,
  dependency_type: 'logical',
  criticality: 'medium',
  confidence: 'medium',
  source: null,
  description: '',
  notes: '',
  is_bidirectional: false
})

const availableAssets = ref([])
const loadingAssets = ref(false)

const typeOptions = [
  { label: t('assetDependencies.types.logical'), value: 'logical' },
  { label: t('assetDependencies.types.functional'), value: 'functional' },
  { label: t('assetDependencies.types.data_flow'), value: 'data_flow' },
  { label: t('assetDependencies.types.control_flow'), value: 'control_flow' }
]

const criticalityOptions = [
  { label: t('assetDependencies.criticalities.low'), value: 'low' },
  { label: t('assetDependencies.criticalities.medium'), value: 'medium' },
  { label: t('assetDependencies.criticalities.high'), value: 'high' },
  { label: t('assetDependencies.criticalities.critical'), value: 'critical' }
]

const confidenceOptions = [
  { label: t('assetDependencies.confidences.low'), value: 'low' },
  { label: t('assetDependencies.confidences.medium'), value: 'medium' },
  { label: t('assetDependencies.confidences.high'), value: 'high' }
]

const sourceOptions = [
  { label: t('assetDependencies.sources.manual'), value: 'manual' },
  { label: t('assetDependencies.sources.assessment'), value: 'assessment' },
  { label: t('assetDependencies.sources.import'), value: 'import' },
  { label: t('assetDependencies.sources.template'), value: 'template' }
]

async function fetchAssets() {
  loadingAssets.value = true
  try {
    const res = await api.getAssets({ limit: 500 })
    
    // L'API restituisce una risposta paginata: { data: [...], total: ..., skip: ..., limit: ... }
    const assets = res.data?.data || res.data || []
    
    availableAssets.value = assets
      .filter(a => {
        const assetId = typeof props.assetId === 'string' ? props.assetId : String(props.assetId)
        const aId = typeof a.id === 'string' ? a.id : String(a.id)
        return aId !== assetId && a.deleted_at == null
      })
      .map(a => ({
        ...a,
        // Assicurati che name esista, altrimenti usa un fallback
        name: a.name || a.tag || `Asset ${a.id}`,
        // Normalizza l'ID come stringa per PrimeVue
        id: typeof a.id === 'string' ? a.id : String(a.id)
      }))
  } catch (error) {
    availableAssets.value = []
    toast.add({
      severity: 'error',
      summary: t('common.errors.error'),
      detail: t('assetDependencies.errorLoadingAssets')
    })
  } finally {
    loadingAssets.value = false
  }
}

function handleSubmit() {
  if (!formData.value.dependency_asset_id) return
  
  // Converti is_bidirectional da booleano a stringa per il backend
  const submitData = {
    ...formData.value,
    is_bidirectional: formData.value.is_bidirectional ? 'true' : 'false'
  }
  
  emit('submit', submitData)
}

onMounted(async () => {
  await fetchAssets()
  
  // Se ci sono dati suggeriti, popola il form
  if (props.suggestedData) {
    formData.value = {
      dependent_asset_id: props.assetId,
      dependency_asset_id: props.suggestedData.dependency_asset_id,
      dependency_type: props.suggestedData.dependency_type || 'logical',
      criticality: props.suggestedData.criticality || 'medium',
      confidence: props.suggestedData.confidence || 'medium',
      source: props.suggestedData.source || 'manual',
      description: props.suggestedData.description || '',
      notes: '',
      is_bidirectional: false
    }
  }
})
</script>

