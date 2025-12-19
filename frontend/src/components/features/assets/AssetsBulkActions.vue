<template>
  <Dialog :visible="visible" @update:visible="$emit('update:visible', $event)" :header="t('common.actions.bulkEdit')" :modal="true" :style="{ width: '40vw' }">
    <div class="p-fluid">
      <div class="p-field">
        <label for="field">{{ t('assets.strings.chooseField') }}</label>
        <Dropdown v-model="bulkField" :options="bulkFieldOptions" optionLabel="label" optionValue="value" :placeholder="t('assets.strings.chooseField')" />
      </div>
      
      <!-- Status -->
      <div class="p-field" v-if="bulkField === 'status_id'">
        <label>{{ t('common.fields.status') }}</label>
        <Dropdown v-model="bulkValue" :options="assetStatusOptions" optionLabel="name" optionValue="id" :placeholder="t('assets.status')" />
      </div>
      
      <!-- Site -->
      <div class="p-field" v-if="bulkField === 'site_id'">
        <label>{{ t('common.fields.site') }}</label>
        <Dropdown v-model="bulkValue" :options="sites" optionLabel="name" optionValue="id" :placeholder="t('common.fields.site')" />
      </div>
      
      <!-- Asset Type -->
      <div class="p-field" v-if="bulkField === 'asset_type_id'">
        <label>{{ t('assets.fields.type') }}</label>
        <Dropdown v-model="bulkValue" :options="assetTypes" optionLabel="name" optionValue="id" :placeholder="t('assets.fields.type')" />
      </div>
      
      <!-- Area -->
      <div class="p-field" v-if="bulkField === 'area_id'">
        <label>{{ t('assets.fields.area') }}</label>
        <Dropdown v-model="bulkValue" :options="areas" optionLabel="name" optionValue="id" :placeholder="t('assets.fields.area')" showClear />
      </div>
      
      <!-- Location -->
      <div class="p-field" v-if="bulkField === 'location_id'">
        <label>{{ t('assets.fields.location') }}</label>
        <Dropdown v-model="bulkValue" :options="locations" optionLabel="name" optionValue="id" :placeholder="t('assets.fields.location')" showClear />
      </div>
      
      <!-- Manufacturer -->
      <div class="p-field" v-if="bulkField === 'manufacturer_id'">
        <label>{{ t('assets.fields.manufacturer') }}</label>
        <Dropdown v-model="bulkValue" :options="manufacturers" optionLabel="name" optionValue="id" :placeholder="t('assets.fields.manufacturer')" />
      </div>
      
      <!-- VLAN -->
      <div class="p-field" v-if="bulkField === 'vlan'">
        <label for="bulk_vlan">{{ t('assets.fields.vlan') }}</label>
        <InputText id="bulk_vlan" v-model="bulkValue" />
      </div>
      
      <!-- Business Criticality -->
      <div class="p-field" v-if="bulkField === 'business_criticality'">
        <label>{{ t('assets.fields.businessCriticality') }}</label>
        <Dropdown
          v-model="bulkValue"
          :options="businessCriticalityOptions"
          optionLabel="label"
          optionValue="value"
          :placeholder="t('assets.fields.businessCriticality')"
          showClear
        />
      </div>
      
      <!-- Altri campi generici -->
      <div class="p-field" v-if="bulkField && !['status_id','site_id','area_id','asset_type_id','location_id','manufacturer_id','vlan','business_criticality'].includes(bulkField)">
        <label for="bulk_generic">{{ t('assets.value') }}</label>
        <InputText id="bulk_generic" v-model="bulkValue" />
      </div>
      
      <div class="p-field">
        <Button :label="t('common.actions.confirm')" icon="pi pi-check" class="p-button-success" :disabled="!bulkField || bulkValue === null || bulkValue === ''" @click="onBulkUpdate" />
        <Button :label="t('common.actions.cancel')" icon="pi pi-times" class="p-button-text" @click="close" />
      </div>
    </div>
  </Dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'

const props = defineProps({
  visible: { type: Boolean, default: false },
  assetStatusOptions: { type: Array, default: () => [] },
  sites: { type: Array, default: () => [] },
  assetTypes: { type: Array, default: () => [] },
  areas: { type: Array, default: () => [] },
  locations: { type: Array, default: () => [] },
  manufacturers: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:visible', 'bulkUpdate'])

const { t } = useI18n()

const bulkField = ref(null)
const bulkValue = ref(null)

const bulkFieldOptions = [
  { label: t('common.fields.status'), value: 'status_id' },
  { label: t('common.fields.site'), value: 'site_id' },
  { label: t('common.fields.area'), value: 'area_id' },
  { label: t('common.fields.location'), value: 'location_id' },
  { label: t('common.fields.type'), value: 'asset_type_id' },
  { label: t('common.fields.manufacturer'), value: 'manufacturer_id' },
  { label: t('assets.fields.vlan'), value: 'vlan' },
  { label: t('assets.fields.businessCriticality'), value: 'business_criticality' }
]

const businessCriticalityOptions = [
  { label: t('assets.strings.businessCriticalityLow'), value: 'low' },
  { label: t('assets.strings.businessCriticalityMedium'), value: 'medium' },
  { label: t('assets.strings.businessCriticalityHigh'), value: 'high' },
  { label: t('assets.strings.businessCriticalityCritical'), value: 'critical' }
]

// Reset form quando si apre/chiude il dialog
watch(() => props.visible, (newVisible) => {
  if (!newVisible) {
    bulkField.value = null
    bulkValue.value = null
  }
})

function onBulkUpdate() {
  if (!bulkField.value || bulkValue.value === null || bulkValue.value === '') return
  
  emit('bulkUpdate', {
    field: bulkField.value,
    value: bulkValue.value
  })
  
  close()
}

function close() {
  emit('update:visible', false)
}
</script> 