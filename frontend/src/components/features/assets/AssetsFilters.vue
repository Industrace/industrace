<template>
  <div class="filters-container">
    <!-- Filtri base sempre visibili -->
    <div class="filters-base">
      <Dropdown 
        id="filter_status"
        v-model="filters.status_id.value" 
        :options="assetStatusOptions" 
        optionLabel="name" 
        optionValue="id" 
        :placeholder="t('assets.strings.filterbyStatus')" 
        showClear 
        style="min-width: 150px" 
      />
      <Dropdown 
        id="filter_site"
        v-model="filters.site_id.value" 
        :options="sites" 
        optionLabel="name" 
        optionValue="id" 
        :placeholder="t('assets.strings.filterbySite')" 
        showClear 
        style="min-width: 150px" 
      />
      <Dropdown 
        id="filter_area"
        v-model="filters.area_id.value" 
        :options="areas" 
        optionLabel="name" 
        optionValue="id" 
        :placeholder="t('assets.strings.filterbyArea')" 
        showClear 
        style="min-width: 150px" 
      />
      <Button 
        icon="pi pi-filter" 
        :label="showAdvanced ? t('common.actions.hide') : t('assets.strings.advancedFilters')"
        severity="help"
        @click="showAdvanced = !showAdvanced"
      />
    </div>

    <!-- Filtri avanzati (espandibili) -->
    <div v-show="showAdvanced" class="filters-advanced">
      <div class="advanced-filters-content">
        <div class="filter-group">
          <label for="filter_location">{{ t('locations.fields.name') }}</label>
          <Dropdown
            id="filter_location"
            v-model="filters.location_id.value"
            :options="locations"
            optionLabel="name"
            optionValue="id"
            :placeholder="t('assets.strings.filterbyLocation')"
            showClear
            style="min-width: 200px"
          />
        </div>

        <div class="filter-group">
          <label for="filter_business_criticality">{{ t('assets.fields.businessCriticality') }}</label>
          <Dropdown
            id="filter_business_criticality"
            v-model="filters.business_criticality.value"
            :options="businessCriticalityOptions"
            optionLabel="label"
            optionValue="value"
            :placeholder="t('assets.fields.businessCriticality')"
            showClear
            style="min-width: 200px"
          />
        </div>

        <div class="filter-group">
          <label for="filter_risk_score">{{ t('assets.fields.riskScore') }}</label>
          <div class="risk-score-range">
            <InputNumber 
              id="filter_risk_score_min" 
              v-model="filters.risk_score_min.value" 
              :placeholder="t('assets.strings.riskScoreMin')" 
              :min="0" 
              :max="10" 
              mode="decimal" 
              style="width: 100px" 
            />
            <span class="range-separator">-</span>
            <InputNumber 
              id="filter_risk_score_max" 
              v-model="filters.risk_score_max.value" 
              :placeholder="t('assets.strings.riskScoreMax')" 
              :min="0" 
              :max="10" 
              mode="decimal" 
              style="width: 100px" 
            />
          </div>
        </div>

        <div class="filter-group">
          <div class="checkbox-filter">
            <Checkbox 
              id="filter_has_critical_vulns" 
              v-model="filters.has_critical_vulns.value" 
              :binary="true"
            />
            <label for="filter_has_critical_vulns" class="checkbox-label">
              {{ t('assets.filters.hasCriticalVulns') }}
            </label>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import InputNumber from 'primevue/inputnumber'
import Checkbox from 'primevue/checkbox'

const props = defineProps({
  filters: { type: Object, required: true },
  assetStatusOptions: { type: Array, default: () => [] },
  sites: { type: Array, default: () => [] },
  areas: { type: Array, default: () => [] },
  locations: { type: Array, default: () => [] }
})

const { t } = useI18n()

const showAdvanced = ref(false)

// Mostra i filtri avanzati se il filtro has_critical_vulns è attivo
import { watch } from 'vue'
watch(() => props.filters.has_critical_vulns?.value, (newValue) => {
  if (newValue) {
    showAdvanced.value = true
  }
}, { immediate: true })

const businessCriticalityOptions = [
  { label: t('assets.strings.businessCriticalityLow'), value: 'low' },
  { label: t('assets.strings.businessCriticalityMedium'), value: 'medium' },
  { label: t('assets.strings.businessCriticalityHigh'), value: 'high' },
  { label: t('assets.strings.businessCriticalityCritical'), value: 'critical' }
]
</script>

<style scoped>
.filters-container {
  margin-bottom: 1.5rem;
}

.filters-base {
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
}

.filters-advanced {
  margin-top: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 0.5rem;
  border: 1px solid #dee2e6;
}

.advanced-filters-content {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
  align-items: flex-end;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #495057;
}

.risk-score-range {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.range-separator {
  color: #6c757d;
  font-weight: 500;
}

.checkbox-filter {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.checkbox-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #495057;
  cursor: pointer;
  margin: 0;
}

@media (max-width: 768px) {
  .filters-base {
    flex-direction: column;
    align-items: stretch;
  }

  .filters-base > * {
    width: 100%;
  }

  .advanced-filters-content {
    flex-direction: column;
  }

  .filter-group {
    width: 100%;
  }
}
</style>