<template>
  <div class="security-zone-form">
    <div class="p-fluid">
      <div class="field">
        <label>{{ t('common.fields.name') }} *</label>
        <InputText 
          v-model="formData.name" 
          :placeholder="t('isa62443.securityZones.namePlaceholder')"
          required
        />
      </div>
      <div class="field">
        <label>{{ t('common.fields.description') }}</label>
        <Textarea 
          v-model="formData.description" 
          :rows="3"
          :placeholder="t('isa62443.securityZones.descriptionPlaceholder')"
        />
      </div>
      <div class="field">
        <label>{{ t('isa62443.securityZones.site') }}</label>
        <Dropdown
          v-model="formData.site_id"
          :options="sites"
          optionLabel="name"
          optionValue="id"
          :placeholder="t('isa62443.securityZones.selectSite')"
          filter
        />
      </div>
      <div class="field">
        <label>{{ t('isa62443.securityZones.zoneType') }}</label>
        <Dropdown
          v-model="formData.zone_type"
          :options="zoneTypeOptions"
          optionLabel="label"
          optionValue="value"
          :placeholder="t('isa62443.securityZones.selectZoneType')"
        />
      </div>
      <div class="field">
        <label>{{ t('isa62443.securityZones.securityLevelTarget') }} (SL-T)</label>
        <InputNumber 
          v-model="formData.security_level_target" 
          :min="1" 
          :max="4"
          :showButtons="true"
          class="w-full"
        />
      </div>
      <div class="field-checkbox">
        <Checkbox 
          v-model="formData.is_dmz" 
          :binary="true"
          inputId="is_dmz"
        />
        <label for="is_dmz" class="ml-2">{{ t('isa62443.securityZones.isDMZ') }}</label>
      </div>
      <div class="field-checkbox">
        <Checkbox 
          v-model="formData.is_air_gapped" 
          :binary="true"
          inputId="is_air_gapped"
        />
        <label for="is_air_gapped" class="ml-2">{{ t('isa62443.securityZones.isAirGapped') }}</label>
      </div>
      <div class="field">
        <label>{{ t('isa62443.securityZones.networkSegment') }}</label>
        <InputText 
          v-model="formData.network_segment" 
          :placeholder="t('isa62443.securityZones.networkSegmentPlaceholder')"
        />
      </div>
      <div class="flex justify-content-end gap-2 mt-3">
        <Button 
          :label="t('common.actions.save')" 
          icon="pi pi-check" 
          @click="handleSubmit"
          :loading="saving"
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
import { ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Dropdown from 'primevue/dropdown'
import InputNumber from 'primevue/inputnumber'
import Checkbox from 'primevue/checkbox'
import Button from 'primevue/button'
import api from '@/api/api'

const props = defineProps({
  zone: { type: Object, default: null }
})

const emit = defineEmits(['submit', 'cancel'])
const { t } = useI18n()

const formData = ref({
  name: '',
  description: '',
  site_id: null,
  zone_type: null,
  security_level_target: null,
  is_dmz: false,
  is_air_gapped: false,
  network_segment: ''
})

const sites = ref([])
const saving = ref(false)

const zoneTypeOptions = [
  { label: t('isa62443.securityZones.zoneTypes.control'), value: 'control' },
  { label: t('isa62443.securityZones.zoneTypes.supervisory'), value: 'supervisory' },
  { label: t('isa62443.securityZones.zoneTypes.enterprise'), value: 'enterprise' },
  { label: t('isa62443.securityZones.zoneTypes.dmz'), value: 'dmz' },
  { label: t('isa62443.securityZones.zoneTypes.other'), value: 'other' }
]

watch(() => props.zone, (newZone) => {
  if (newZone) {
    formData.value = {
      name: newZone.name || '',
      description: newZone.description || '',
      site_id: newZone.site_id || null,
      zone_type: newZone.zone_type || null,
      security_level_target: newZone.security_level_target || null,
      is_dmz: newZone.is_dmz || false,
      is_air_gapped: newZone.is_air_gapped || false,
      network_segment: newZone.network_segment || ''
    }
  } else {
    formData.value = {
      name: '',
      description: '',
      site_id: null,
      zone_type: null,
      security_level_target: null,
      is_dmz: false,
      is_air_gapped: false,
      network_segment: ''
    }
  }
}, { immediate: true })

async function fetchSites() {
  try {
    const res = await api.getSites()
    sites.value = res.data || []
  } catch (error) {
    console.error('Error fetching sites:', error)
  }
}

function handleSubmit() {
  if (!formData.value.name) {
    return
  }
  emit('submit', { ...formData.value })
}

onMounted(async () => {
  await fetchSites()
})
</script>

<style scoped>
.w-full {
  width: 100%;
}
</style>

