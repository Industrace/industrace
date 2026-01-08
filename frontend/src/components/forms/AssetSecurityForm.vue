<template>
  <Card class="mb-4">
    <template #title>
      <div class="flex align-items-center">
        <i class="pi pi-shield mr-2"></i>
        {{ t('assets.strings.securityInfo') }}
      </div>
    </template>
    <template #content>
      <div class="grid">
        <div class="col-12 md:col-6">
          <div class="p-field">
            <label for="remote_access">{{ t('assets.fields.remoteAccess') }}</label>
            <Dropdown 
              id="remote_access" 
              v-model="form.remote_access_type" 
              :options="remoteAccessOptions" 
              optionLabel="label" 
              optionValue="value"
              :placeholder="t('common.strings.select')"
              class="w-full"
            />
          </div>
        </div>

        <div class="col-12 md:col-6">
          <div class="p-field">
            <label for="physical_access_ease">{{ t('assets.fields.physicalAccessEase') }}</label>
            <Dropdown 
              id="physical_access_ease" 
              v-model="form.physical_access_ease" 
              :options="physicalAccessOptions" 
              optionLabel="label" 
              optionValue="value"
              :placeholder="t('common.strings.select')"
              class="w-full"
            >
              <template #value="slotProps">
                <span v-if="slotProps.value">
                  {{ getPhysicalAccessLabel(slotProps.value) }}
                </span>
                <span v-else>{{ t('common.strings.select') }}</span>
              </template>
              <template #option="slotProps">
                <div class="flex align-items-center justify-content-between w-full">
                  <span>{{ slotProps.option.label }}</span>
                  <i 
                    v-if="slotProps.option.tooltip"
                    class="pi pi-info-circle text-500 ml-2"
                    v-tooltip.top="slotProps.option.tooltip"
                  ></i>
                </div>
              </template>
            </Dropdown>
          </div>
        </div>

        <div class="col-12 md:col-6">
          <div class="p-field">
            <label for="business_criticality">{{ t('assets.fields.businessCriticality') }}</label>
            <Dropdown
              id="business_criticality"
              v-model="form.business_criticality"
              :options="businessCriticalityOptions"
              optionLabel="label"
              optionValue="value"
              :placeholder="t('common.strings.select')"
              class="w-full"
            />
          </div>
        </div>
      </div>
    </template>
  </Card>
</template>

<script setup>
import { watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Card from 'primevue/card'
import Dropdown from 'primevue/dropdown'

const props = defineProps({
  form: { type: Object, required: true }
})

const { t } = useI18n()

// Sincronizza remote_access con remote_access_type
watch(() => props.form.remote_access_type, (newValue) => {
  if (props.form) {
    props.form.remote_access = newValue !== 'none' && newValue !== null
  }
}, { immediate: true })

const remoteAccessOptions = [
  { label: t('assets.strings.remoteAccessNone'), value: 'none' },
  { label: t('assets.strings.remoteAccessAttended'), value: 'attended' },
  { label: t('assets.strings.remoteAccessUnattended'), value: 'unattended' }
]

const physicalAccessOptions = [
  { 
    label: t('assets.strings.physicalAccessUnrestricted'), 
    value: 'unrestricted',
    tooltip: t('assets.strings.physicalAccessUnrestrictedTooltip')
  },
  { 
    label: t('assets.strings.physicalAccessControlled'), 
    value: 'controlled',
    tooltip: t('assets.strings.physicalAccessControlledTooltip')
  },
  { 
    label: t('assets.strings.physicalAccessRestricted'), 
    value: 'restricted',
    tooltip: t('assets.strings.physicalAccessRestrictedTooltip')
  }
]

function getPhysicalAccessLabel(value) {
  const option = physicalAccessOptions.find(opt => opt.value === value)
  return option ? option.label : value
}

const businessCriticalityOptions = [
  { label: t('assets.strings.businessCriticalityLow'), value: 'low' },
  { label: t('assets.strings.businessCriticalityMedium'), value: 'medium' },
  { label: t('assets.strings.businessCriticalityHigh'), value: 'high' },
  { label: t('assets.strings.businessCriticalityCritical'), value: 'critical' }
]
</script>

<style scoped>
.p-field {
  margin-bottom: 1rem;
}

.p-field label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}
</style> 