<template>
  <div class="asset-overview-tab">
    <!-- Alert Banner - Risponde: "Questa risorsa rappresenta un problema?" -->
    <AssetAlertBanner
      :totalRiskScore="totalRiskScore"
      :baseRiskScore="baseRiskScore"
      :riskFromDependencies="riskFromDependencies"
    />

    <!-- Status Dashboard -->
    <div class="status-dashboard card p-4 mb-4">
      <div class="flex align-items-center gap-3 flex-wrap">
        <div class="status-item">
          <label class="text-600 text-sm">{{ t('assets.fields.status') }}:</label>
          <Tag :value="getStatusLabel(asset.status)" :severity="getStatusSeverity(asset.status)" class="ml-2" />
        </div>
        <div class="status-item">
          <label class="text-600 text-sm">{{ t('assets.fields.businessCriticality') }}:</label>
          <Tag :value="getBusinessCriticalityLabel(asset.business_criticality)" :severity="getCriticalitySeverity(asset.business_criticality)" class="ml-2" />
        </div>
      </div>
    </div>

    <!-- Riepilogo Rischio -->
    <div class="risk-summary card p-4 mb-4">
      <div class="flex align-items-center justify-content-between mb-3">
        <h3 class="m-0">{{ t('assets.riskBreakdown.totalRiskScore') }}</h3>
        <Tag 
          :value="totalRiskScore?.toFixed(2) || 'N/A'" 
          :severity="getRiskSeverity(totalRiskScore)" 
          class="text-xl p-3 risk-score-badge" 
        />
      </div>
      <div class="risk-breakdown">
        <div class="flex justify-content-between align-items-center mb-2">
          <span class="text-600">{{ t('assets.riskBreakdown.baseRiskScore') }}:</span>
          <span class="font-medium">{{ baseRiskScore?.toFixed(2) || '0.00' }}</span>
        </div>
        <div class="flex justify-content-between align-items-center">
          <span class="text-600">{{ t('assets.riskBreakdown.riskFromDependencies') }}:</span>
          <span class="font-medium text-orange-500">+{{ riskFromDependencies?.toFixed(2) || '0.00' }}</span>
        </div>
      </div>
    </div>

    <!-- Info Principali -->
    <div class="main-info card p-4 mb-4">
      <h4 class="mt-0 mb-3">{{ t('assets.detail.mainInfo') }}</h4>
      <AssetDetailMainInfo :asset="asset" />
    </div>

    <!-- Info Tecniche (collassabile, default espanso) -->
    <Accordion :activeIndex="[0]" class="mb-4">
      <AccordionTab :header="t('assets.detail.technicalInfo')">
        <AssetDetailTechnicalInfo
          :asset="asset"
          :getRemoteAccessTypeLabel="getRemoteAccessTypeLabel"
          :getPhysicalAccessLabel="getPhysicalAccessLabel"
          :getBusinessCriticalityLabel="getBusinessCriticalityLabel"
        />
      </AccordionTab>
    </Accordion>

    <!-- Quick Actions -->
    <div class="quick-actions card p-4">
      <h4 class="mt-0 mb-3">{{ t('assets.detail.quickActions') }}</h4>
      <div class="flex gap-2 flex-wrap">
        <Button 
          :label="t('common.actions.edit')" 
          icon="pi pi-pencil" 
          @click="$emit('edit')"
          v-if="canWrite('assets')"
        />
        <Button 
          :label="t('common.actions.print')" 
          icon="pi pi-print" 
          @click="$emit('print')"
        />
        <Button 
          :label="asset.description ? t('assets.notes.editNote') : t('assets.notes.addNote')" 
          icon="pi pi-sticky-note" 
          @click="$emit('add-note')"
          v-if="canWrite('assets')"
        />
        <Button 
          :label="t('assets.tabs.dependencies')" 
          icon="pi pi-sitemap" 
          @click="navigateToRelations"
          outlined
        />
        <Button 
          :label="t('assets.tabs.vulnerabilities')" 
          icon="pi pi-shield" 
          @click="navigateToSecurity"
          outlined
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Accordion from 'primevue/accordion'
import AccordionTab from 'primevue/accordiontab'
import AssetDetailMainInfo from '../AssetDetailMainInfo.vue'
import AssetDetailTechnicalInfo from '../AssetDetailTechnicalInfo.vue'
import AssetAlertBanner from '../components/AssetAlertBanner.vue'
import { getRiskSeverity } from '@/composables/useRiskLabels'

const props = defineProps({
  asset: { type: Object, required: true },
  riskBreakdown: { type: Object, default: null },
  totalRiskScore: { type: Number, default: null },
  riskFromDependencies: { type: Number, default: null },
  getRemoteAccessTypeLabel: { type: Function, required: true },
  getPhysicalAccessLabel: { type: Function, required: true },
  getBusinessCriticalityLabel: { type: Function, required: true },
  canWrite: { type: Function, required: true }
})

const emit = defineEmits(['edit', 'print', 'add-note'])

const { t } = useI18n()
const router = useRouter()

const baseRiskScore = computed(() => {
  if (!props.riskBreakdown) return 0.0
  return props.riskBreakdown.final_score || 0.0
})

function getStatusSeverity(status) {
  if (status === 'active') return 'success'
  if (status === 'maintenance') return 'warning'
  return 'secondary'
}

function getStatusLabel(status) {
  return t(`assets.status.${status}`) || status
}

function getCriticalitySeverity(criticality) {
  if (criticality === 'high') return 'danger'
  if (criticality === 'medium') return 'warning'
  return 'info'
}

function navigateToRelations() {
  // Cambia tab a Relazioni (index 1)
  const event = new CustomEvent('navigate-tab', { detail: { index: 1 } })
  window.dispatchEvent(event)
}

function navigateToSecurity() {
  // Cambia tab a Sicurezza (index 2)
  const event = new CustomEvent('navigate-tab', { detail: { index: 2 } })
  window.dispatchEvent(event)
}
</script>

<style scoped>
.asset-overview-tab {
  max-width: 1200px;
}

.status-dashboard {
  background: var(--surface-card);
}

.status-item {
  display: flex;
  align-items: center;
}

.risk-summary {
  background: var(--surface-card);
}

.risk-score-badge {
  font-size: 1.5rem;
  font-weight: 700;
}

.risk-breakdown {
  padding-top: 1rem;
  border-top: 1px solid var(--surface-border);
}

.main-info {
  background: var(--surface-card);
}

.quick-actions {
  background: var(--surface-card);
}
</style>

