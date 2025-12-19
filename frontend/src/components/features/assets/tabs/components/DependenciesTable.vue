<template>
  <DataTable 
    :value="dependencies" 
    :loading="loading"
    :emptyMessage="t('assetDependencies.noDependencies')"
    class="p-datatable-sm"
  >
    <Column :header="isDependents ? t('assetDependencies.dependentAsset') : t('assetDependencies.dependencyAsset')">
      <template #body="{ data }">
        <a @click="$router.push(`/assets/${isDependents ? data.dependent_asset_id : data.dependency_asset_id}`)" class="asset-link">
          {{ isDependents ? data.dependent_asset?.name : data.dependency_asset?.name }}
        </a>
      </template>
    </Column>
    <Column field="dependency_type" :header="t('assetDependencies.dependencyType')">
      <template #body="{ data }">
        {{ getTypeLabel(data.dependency_type) }}
      </template>
    </Column>
    <Column field="criticality" :header="t('assetDependencies.criticality')">
      <template #body="{ data }">
        <Tag :value="getCriticalityLabel(data.criticality)" :severity="getCriticalitySeverity(data.criticality)" />
      </template>
    </Column>
    <Column field="confidence" :header="t('assetDependencies.confidence')">
      <template #body="{ data }">
        <Tag 
          :value="getConfidenceLabel(data.confidence || 'medium')" 
          :severity="getConfidenceSeverity(data.confidence || 'medium')" 
        />
      </template>
    </Column>
    <Column field="source" :header="t('assetDependencies.source')">
      <template #body="{ data }">
        <span v-if="data.source" class="source-badge">
          <i :class="getSourceIcon(data.source)" class="mr-1"></i>
          {{ getSourceLabel(data.source) }}
        </span>
        <span v-else class="p-text-secondary">-</span>
      </template>
    </Column>
    <Column field="description" :header="t('assetDependencies.description')" />
    <Column :header="t('assetDependencies.hasConnection')" style="width: 140px">
      <template #body="{ data }">
        <div v-if="data.connection_status?.has_connection" class="flex align-items-center gap-2">
          <Tag 
            :value="t('assetDependencies.hasConnection')"
            severity="success"
            icon="pi pi-link"
          />
          <Button 
            v-if="data.connection_status?.connection_id"
            icon="pi pi-external-link" 
            class="p-button-rounded p-button-text p-button-sm"
            @click="$router.push(`/assets/${$route.params.id}?tab=connections`)"
            v-tooltip.top="t('assetDependencies.viewConnection')"
          />
        </div>
        <Tag 
          v-else
          :value="t('assetDependencies.noConnection')"
          severity="info"
          icon="pi pi-info-circle"
        />
      </template>
    </Column>
    <Column v-if="canWrite" :header="t('common.strings.actions')">
      <template #body="{ data }">
        <Button 
          icon="pi pi-trash" 
          class="p-button-rounded p-button-text p-button-danger" 
          @click="$emit('delete', data.id)" 
        />
      </template>
    </Column>
  </DataTable>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Tooltip from 'primevue/tooltip'

const props = defineProps({
  dependencies: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  canWrite: { type: Boolean, default: false },
  isDependents: { type: Boolean, default: false }
})

const emit = defineEmits(['delete'])
const { t } = useI18n()
const router = useRouter()

const getTypeLabel = (type) => {
  return t(`assetDependencies.types.${type}`) || type
}

const getCriticalityLabel = (criticality) => {
  return t(`assetDependencies.criticalities.${criticality}`) || criticality
}

const getCriticalitySeverity = (criticality) => {
  const severityMap = {
    'low': 'success',
    'medium': 'info',
    'high': 'warning',
    'critical': 'danger'
  }
  return severityMap[criticality] || null
}

const getConfidenceLabel = (confidence) => {
  return t(`assetDependencies.confidences.${confidence}`) || confidence
}

const getConfidenceSeverity = (confidence) => {
  const severityMap = {
    'low': 'warning',      // Giallo per ipotesi
    'medium': 'info',      // Blu per probabile
    'high': 'success'      // Verde per certo
  }
  return severityMap[confidence] || 'info'
}

const getSourceLabel = (source) => {
  return t(`assetDependencies.sources.${source}`) || source
}

const getSourceIcon = (source) => {
  const iconMap = {
    'manual': 'pi pi-pencil',
    'assessment': 'pi pi-chart-line',
    'import': 'pi pi-download',
    'template': 'pi pi-file'
  }
  return iconMap[source] || 'pi pi-circle'
}
</script>

<style scoped>
.asset-link {
  color: var(--primary-color);
  cursor: pointer;
  text-decoration: none;
}

.asset-link:hover {
  text-decoration: underline;
}

.source-badge {
  display: inline-flex;
  align-items: center;
  font-size: 0.875rem;
}
</style>

