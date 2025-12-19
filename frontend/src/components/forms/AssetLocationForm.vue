<template>
  <Card class="mb-4">
    <template #title>
      <div class="flex align-items-center">
        <i class="pi pi-map-marker mr-2"></i>
        {{ t('assets.strings.positionInfo') }}
      </div>
    </template>
    <template #content>
      <div class="grid">
        <div class="col-12 md:col-4">
          <div class="p-field">
            <label for="site_id">{{ t('common.fields.site') }} <span class="required">*</span></label>
            <Dropdown 
              id="site_id" 
              v-model="form.site_id" 
              :options="sites" 
              optionLabel="name" 
              optionValue="id" 
              :class="{ 'p-invalid': errors.site_id }"
              class="w-full"
              required 
              @change="onSiteChange"
            />
            <small v-if="errors.site_id" class="p-error">{{ errors.site_id }}</small>
          </div>
        </div>

        <div class="col-12 md:col-4">
          <div class="p-field">
            <label for="area_id">{{ t('areas.title') }}</label>
            <Dropdown 
              id="area_id" 
              v-model="form.area_id" 
              :options="filteredAreas" 
              optionLabel="name" 
              optionValue="id" 
              :disabled="!form.site_id"
              :placeholder="t('common.selectArea')"
              :class="{ 'p-invalid': errors.area_id }"
              class="w-full"
              @change="onAreaChange"
            />
            <small v-if="errors.area_id" class="p-error">{{ errors.area_id }}</small>
          </div>
        </div>

        <div class="col-12 md:col-4">
          <div class="p-field">
            <label for="location_id">{{ t('assets.fields.location') }}</label>
            <Dropdown 
              id="location_id" 
              v-model="form.location_id" 
              :options="filteredLocations" 
              optionLabel="name" 
              optionValue="id" 
              :disabled="!form.site_id"
              :placeholder="t('common.strings.select')"
              :class="{ 'p-invalid': errors.location_id }"
              class="w-full"
            />
            <small v-if="errors.location_id" class="p-error">{{ errors.location_id }}</small>
          </div>
        </div>

        <!-- DEPRECATED: security_zone_id field removed. Use IEC 62443 tab in Asset Detail to manage zone memberships with roles -->
      </div>
    </template>
  </Card>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Card from 'primevue/card'
import Dropdown from 'primevue/dropdown'

const props = defineProps({
  form: { type: Object, required: true },
  errors: { type: Object, default: () => ({}) },
  sites: { type: Array, required: true },
  allLocations: { type: Array, default: () => [] },
  allAreas: { type: Array, default: () => [] },
  securityZones: { type: Array, default: () => [] }
})

const emit = defineEmits(['site-change', 'area-change'])

const { t } = useI18n()

const filteredAreas = computed(() =>
  props.allAreas.filter(area => area.site_id === props.form.site_id)
)

const filteredLocations = computed(() => {
  let locations = props.allLocations.filter(loc => loc.site_id === props.form.site_id)
  
  // Se è selezionata un'area, filtra le location per area
  if (props.form.area_id) {
    locations = locations.filter(loc => loc.area_id === props.form.area_id)
  }
  
  return locations
})

const filteredSecurityZones = computed(() => {
  // Filtra le security zones per il sito selezionato
  if (props.form.site_id && props.securityZones) {
    return props.securityZones.filter(zone => 
      !zone.site_id || zone.site_id === props.form.site_id
    )
  }
  return props.securityZones || []
})

function onSiteChange() {
  // Reset area e location quando cambia il sito
  props.form.area_id = null
  props.form.location_id = null
  emit('site-change', props.form.site_id)
}

function onAreaChange() {
  // Reset location quando cambia l'area
  props.form.location_id = null
  emit('area-change', props.form.area_id)
}
</script>

<style scoped>
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
}
</style> 