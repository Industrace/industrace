
<template>
  <div v-if="sites.length && manufacturers.length && assetTypes.length && assetStatusOptions.length">
    <BaseForm 
      :is-submitting="isSubmitting"
      :is-valid="isValid"
      :errors="errors"
      @submit="handleSubmit"
      @cancel="$emit('cancel')"
    >
      <!-- Basic Information -->
      <AssetBasicInfoForm 
        :form="form"
        :errors="errors"
        :assetTypes="assetTypes"
        :manufacturers="manufacturers"
        :assetStatusOptions="assetStatusOptions"
      />

      <!-- Location -->
      <AssetLocationForm 
        :form="form"
        :errors="errors"
        :sites="sites"
        :allLocations="allLocations"
        :allAreas="allAreas"
        :securityZones="securityZones"
      />

      <!-- Technical Details -->
      <AssetTechnicalDetailsForm 
        :form="form"
      />

      <!-- Network Connection -->
      <Card class="mb-4">
        <template #title>
          <div class="flex align-items-center">
            <i class="pi pi-wifi mr-2"></i>
            {{ t('assets.strings.networkConnection') }}
          </div>
        </template>
        <template #content>
          <AssetInterfacesForm
            v-model:interfaces="form.interfaces"
            :editable="true"
            :asset-id="form.id || props.asset?.id"
            :tenant-id="form.tenant_id || props.asset?.tenant_id"
          />
        </template>
      </Card>

      <!-- Access and Security -->
      <AssetSecurityForm 
        :form="form"
      />

      <!-- Dates and Notes -->
      <AssetDatesForm 
        :form="form"
      />
    </BaseForm>
  </div>
  <div v-else class="p-4 text-center text-muted">
    Loading data...
  </div>
</template>

<script setup>
import { watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import { useForm } from '../../composables/useForm'
import BaseForm from '../base/BaseForm.vue'
import Card from 'primevue/card'
import AssetInterfacesForm from './AssetInterfacesForm.vue'
import AssetBasicInfoForm from './AssetBasicInfoForm.vue'
import AssetLocationForm from './AssetLocationForm.vue'
import AssetTechnicalDetailsForm from './AssetTechnicalDetailsForm.vue'
import AssetSecurityForm from './AssetSecurityForm.vue'
import AssetDatesForm from './AssetDatesForm.vue'

const { t } = useI18n()
const toast = useToast()

const props = defineProps({
  asset: {
    type: Object,
    default: null
  },
  sites: {
    type: Array,
    required: true
  },
  assetTypes: {
    type: Array,
    required: true
  },
  allLocations: {
    type: Array,
    default: () => [],
    required: true
  },
  allAreas: {
    type: Array,
    default: () => [],
    required: true
  },
  manufacturers: {
    type: Array,
    required: true 
  },
  assetStatusOptions: {
    type: Array,
    required: true
  },
  securityZones: {
    type: Array,
    default: () => []
  }
})



const emit = defineEmits(['submit', 'cancel'])

// Use the useForm composable
const {
  form,
  errors,
  isSubmitting,
  isValid,
  submit,
  setForm
} = useForm({
  name: '',
  site_id: null,
  location_id: null,
  manufacturer_id: null,
  asset_type_id: null,
  status_id: null,
  security_zone_id: null,
  tag: '',
  serial_number: '',
  ip_address: '',
  vlan: '',
  logical_port: '',
  physical_plug_label: '',
  firmware_version: '',
  impact_value: 1,
  purdue_level: 0.0,
  exposure_level: 'none',
  update_status: 'manual',
  risk_score: 0,
  remote_access: false,
  remote_access_type: 'none',
  last_update_date: null,
  physical_access_ease: 'internal',
  installation_date: null,
  business_criticality: 'low',
  description: '',
  interfaces: props.asset?.interfaces ? [...props.asset.interfaces] : [],
  protocols: [] 
})


watch(() => props.asset, (newAsset) => {
  if (newAsset) {
    const formData = {
      ...newAsset,
      site_id: newAsset.site_id || (newAsset.site && newAsset.site.id) || null,
      location_id: newAsset.location_id || (newAsset.location && newAsset.location.id) || null,
      manufacturer_id: newAsset.manufacturer_id || (newAsset.manufacturer && newAsset.manufacturer.id) || null,
      asset_type_id: newAsset.asset_type_id || (newAsset.asset_type && newAsset.asset_type.id) || null,
      status_id: newAsset.status_id || (newAsset.status && newAsset.status.id) || null,
      security_zone_id: newAsset.security_zone_id || (newAsset.security_zone && newAsset.security_zone.id) || null,
      remote_access: newAsset.remote_access ?? false,
      remote_access_type: newAsset.remote_access_type ?? 'none',
      last_update_date: newAsset.last_update_date ?? null,
      physical_access_ease: newAsset.physical_access_ease ?? 'internal',
      installation_date: newAsset.installation_date ?? null,
      business_criticality: newAsset.business_criticality ?? 'low',
      description: typeof newAsset.description === 'string' ? newAsset.description : '',
      protocols: newAsset.protocols || []
    };
    setForm(formData);
  }
}, { immediate: true })

async function handleSubmit() {
  // console.log('handleSubmit chiamato')
  
  // Custom validation before calling submit
  const validationErrors = validateAssetData(form.value)
  if (validationErrors.length > 0) {
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: t('common.messages.requiredFieldsMissing', { fields: validationErrors.join('\n') }),
      life: 5000
    })
    return
  }

      // console.log('Form data:', form.value)

  // Force asset_id e tenant_id on all interfaces
  if (Array.isArray(form.value.interfaces)) {
    const assetId = form.value.id || props.asset?.id
    const tenantId = form.value.tenant_id || props.asset?.tenant_id
    form.value.interfaces = form.value.interfaces.map(i => ({
      ...i,
      asset_id: assetId,
      tenant_id: tenantId
    }))
  }

  await submit(async (formData) => {
    // console.log('Submit callback chiamato con:', formData)
    
    // Format data fields as YYYY-MM-DD or ISO
    const formatDate = (d) => {
      if (!d) return null
      if (typeof d === 'string' && d.length === 10) return d
      const dateObj = new Date(d)
      if (isNaN(dateObj)) return null
      return dateObj.toISOString().slice(0, 10)
    }
    const formatDateTime = (d) => {
      if (!d) return null
      const dateObj = new Date(d)
      if (isNaN(dateObj)) return null
      return dateObj.toISOString()
    }
    const dataWithFormattedDates = {
      ...formData,
      installation_date: formatDate(formData.installation_date),
      last_update_date: formatDateTime(formData.last_update_date)
    }
    // console.log('Dati finali da inviare:', dataWithFormattedDates)
    emit('submit', dataWithFormattedDates)
  }, {
    successMessage: props.asset ? null : t('assets.messages.created'), // Non mostrare toast per update
    errorContext: t('assets.messages.saveError')
  })
}

// Function to validate asset data
function validateAssetData(assetData) {
  const errors = []
  
  // Required fields
  const requiredFields = [
    { field: 'name', label: t('common.fields.name') },
    { field: 'site_id', label: t('common.fields.site') },
    { field: 'asset_type_id', label: t('common.fields.type') },
    { field: 'status_id', label: t('common.fields.status') },
    { field: 'manufacturer_id', label: t('common.fields.manufacturer') }
  ]
  
  requiredFields.forEach(({ field, label }) => {
    if (!assetData[field] || assetData[field] === '' || assetData[field] === null) {
      errors.push(t('common.messages.required', { field: label }))
    }
  })
  
  return errors
}


</script>

<style scoped>
.p-card {
  background: var(--surface-card);
  border: 1px solid var(--surface-border);
  border-radius: 8px;
}

.p-card .p-card-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--text-color);
}

.required {
  color: #dc3545;
  font-weight: bold;
}

.p-field {
  margin-bottom: 1rem;
}

.p-field label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.p-invalid {
  border-color: #dc3545 !important;
}

.p-error {
  color: #dc3545;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

/* Responsive adjustments */
@media screen and (max-width: 768px) {
  .p-field {
    margin-bottom: 1.5rem;
  }
  
  .grid > .col-12 {
    padding: 0.5rem;
  }
}
</style>
