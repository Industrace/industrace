<template>
  <div class="asset-security-tab">
    <!-- Tab Rischio Completo -->
    <AssetDetailRiskTab ref="riskTabRef" :assetId="assetId" />

    <!-- Vulnerabilità (separata) -->
    <div class="vulnerabilities-section mt-4">
      <h3 class="mb-3">{{ t('assets.tabs.vulnerabilities') }}</h3>
      <AssetDetailVulnerabilitiesTab :assetId="assetId" :canWrite="canWrite" @updated="$emit('updated')" />
    </div>

    <!-- Conformità IEC 62443 (collassabile) -->
    <Accordion class="mt-4">
      <AccordionTab :header="t('assets.compliance.iec62443')">
        <div class="compliance-placeholder p-4 text-center text-600">
          <i class="pi pi-shield" style="font-size: 2rem; color: var(--text-color-secondary);"></i>
          <p class="mt-3">{{ t('assets.compliance.comingSoon') }}</p>
        </div>
      </AccordionTab>
    </Accordion>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Accordion from 'primevue/accordion'
import AccordionTab from 'primevue/accordiontab'
import AssetDetailVulnerabilitiesTab from '../tabs/AssetDetailVulnerabilitiesTab.vue'
import AssetDetailRiskTab from '../tabs/AssetDetailRiskTab.vue'

const props = defineProps({
  assetId: { type: [String, Number], required: true },
  canWrite: { type: Function, default: () => false }
})

const emit = defineEmits(['updated'])

const { t } = useI18n()

const riskTabRef = ref(null)
</script>

<style scoped>
.asset-security-tab {
  max-width: 1200px;
}

.vulnerabilities-section {
  background: var(--surface-card);
  padding: 1.5rem;
  border-radius: 8px;
}

.compliance-placeholder {
  min-height: 200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}
</style>

