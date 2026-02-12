<template>
  <div class="zone-compliance-tab">
    <!-- Livello 1: Dashboard Compatta -->
    <div v-if="currentLevel === 'dashboard'" class="compliance-dashboard">
      <Card class="mb-4">
        <template #content>
          <div class="dashboard-header">
            <h2 class="zone-name">{{ zone.name }}</h2>
            <div class="sl-summary">
              <div class="sl-item">
                <span class="sl-label">{{ t('isa62443.compliance.slTarget') }}:</span>
                <span class="sl-value">SL-{{ zone.security_level_target || '-' }}</span>
              </div>
              <div class="sl-item">
                <span class="sl-label">{{ t('isa62443.compliance.slAchieved') }}:</span>
                <span class="sl-value">SL-{{ zone.security_level_achieved || '-' }}</span>
              </div>
              <div class="sl-item">
                <span class="sl-label">{{ t('isa62443.compliance.gap') }}:</span>
                <span class="sl-value" :class="getGapClass()">
                  {{ getGap() }}
                  <i v-if="getGapValue() < 0" class="pi pi-exclamation-triangle ml-1"></i>
                </span>
              </div>
            </div>
          </div>
          
          <div class="sr-status-summary mt-4">
            <h3 class="section-title">{{ t('isa62443.compliance.srStatus') }}</h3>
            <div class="status-grid">
              <div class="status-item compliant">
                <i class="pi pi-check-circle"></i>
                <span class="status-count">{{ summary.compliant || 0 }}</span>
                <span class="status-label">{{ t('isa62443.compliance.compliant') }}</span>
              </div>
              <div class="status-item partial">
                <i class="pi pi-exclamation-circle"></i>
                <span class="status-count">{{ summary.partial || 0 }}</span>
                <span class="status-label">{{ t('isa62443.compliance.partial') }}</span>
              </div>
              <div class="status-item non-compliant">
                <i class="pi pi-times-circle"></i>
                <span class="status-count">{{ summary.non_compliant || 0 }}</span>
                <span class="status-label">{{ t('isa62443.compliance.nonCompliant') }}</span>
              </div>
              <div class="status-item not-applicable">
                <i class="pi pi-minus-circle"></i>
                <span class="status-count">{{ summary.not_applicable || 0 }}</span>
                <span class="status-label">{{ t('isa62443.compliance.notApplicable') }}</span>
              </div>
            </div>
          </div>
          
          <div class="dashboard-actions mt-4">
            <Button 
              :label="t('isa62443.compliance.reviewSecurityRequirements')"
              icon="pi pi-shield"
              @click="showFoundationRequirements"
              class="p-button-primary"
            />
          </div>
        </template>
      </Card>
    </div>

    <!-- Livello 2: Foundation Requirements -->
    <div v-if="currentLevel === 'foundation-requirements'" class="foundation-requirements">
      <div class="level-header mb-4">
        <Button 
          icon="pi pi-arrow-left" 
          label="Back" 
          class="p-button-text"
          @click="currentLevel = 'dashboard'"
        />
        <h2>{{ t('isa62443.compliance.foundationRequirements') }}</h2>
      </div>
      
      <div v-if="loadingFR" class="text-center p-4">
        <ProgressSpinner />
      </div>
      
      <div v-else-if="foundationRequirements.length === 0" class="text-center p-4">
        <p class="text-muted">{{ t('isa62443.compliance.noFoundationRequirements') }}</p>
        <p class="text-muted text-sm mt-2">{{ t('isa62443.compliance.noFoundationRequirementsDesc') }}</p>
      </div>
      
      <div v-else class="fr-grid">
        <Card 
          v-for="fr in foundationRequirements" 
          :key="fr.id"
          class="fr-card"
          :class="getFRCardClass(fr)"
          @click="selectFoundationRequirement(fr)"
        >
          <template #content>
            <div class="fr-card-content">
              <div class="fr-header">
                <h3 class="fr-id">{{ fr.requirement_id }} - {{ getFRTitle(fr.requirement_id) }}</h3>
                <div class="fr-percentage" :class="getFRPercentageClass(fr)">
                  {{ fr.compliance_percentage || 0 }}%
                </div>
              </div>
              <div v-if="getFRDescription(fr.requirement_id)" class="fr-description">
                {{ getFRDescription(fr.requirement_id) }}
              </div>
              <div v-if="getFRTypicalAssets(fr.requirement_id)" class="fr-typical-assets mt-2">
                <i class="pi pi-info-circle text-sm"></i>
                <small class="text-muted">{{ t('isa62443.compliance.typicallyInvolves') }}: {{ getFRTypicalAssets(fr.requirement_id) }}</small>
              </div>
              <div class="fr-stats">
                <span class="fr-stat">
                  <i class="pi pi-check-circle text-green-500"></i>
                  {{ fr.compliant_count || 0 }}
                </span>
                <span class="fr-stat">
                  <i class="pi pi-exclamation-circle text-orange-500"></i>
                  {{ fr.partial_count || 0 }}
                </span>
                <span class="fr-stat">
                  <i class="pi pi-times-circle text-red-500"></i>
                  {{ fr.non_compliant_count || 0 }}
                </span>
              </div>
            </div>
          </template>
        </Card>
      </div>
    </div>

    <!-- Livello 3: Security Requirements Detail -->
    <div v-if="currentLevel === 'security-requirements'" class="security-requirements-detail">
      <div class="level-header mb-4">
        <Button 
          icon="pi pi-arrow-left" 
          label="Back" 
          class="p-button-text"
          @click="currentLevel = 'foundation-requirements'"
        />
        <h2>{{ selectedFR?.requirement_id }} - {{ selectedFR?.title }}</h2>
      </div>
      
      <div v-if="loadingSR" class="text-center p-4">
        <ProgressSpinner />
      </div>
      
      <div v-else class="sr-detail-layout">
        <!-- Pannello Sinistro (Fisso) - Lista SR per selezione -->
        <div class="sr-left-panel">
          <Card>
            <template #title>
              <span class="text-sm">{{ t('isa62443.compliance.securityRequirements') }}</span>
            </template>
            <template #content>
              <div class="sr-list-container">
                <div v-if="securityRequirements.length === 0" class="sr-list-empty">
                  <i class="pi pi-info-circle text-muted"></i>
                  <p class="text-muted text-sm mt-2">{{ t('isa62443.compliance.noSecurityRequirementsForFR') }}</p>
                </div>
                <div 
                  v-for="sr in securityRequirements" 
                  :key="sr.id"
                  class="sr-list-item"
                  :class="{ 
                    'sr-list-item-active': selectedSR?.id === sr.id,
                    'sr-list-item-assessed': sr.compliance_status && sr.compliance_status !== 'not_assessed'
                  }"
                  :data-status="sr.compliance_status"
                  @click="selectSecurityRequirement(sr)"
                >
                  <div class="sr-list-item-header">
                    <div class="sr-list-item-id">{{ sr.requirement_id }}</div>
                    <div class="sr-list-item-status-badge" v-if="sr.compliance_status && sr.compliance_status !== 'not_assessed'">
                      <i :class="getComplianceStatusIcon(sr.compliance_status)" :style="{ color: getComplianceStatusColor(sr.compliance_status) }"></i>
                    </div>
                  </div>
                  <div class="sr-list-item-title">{{ sr.title }}</div>
                  <div v-if="sr.compliance_status && sr.compliance_status !== 'not_assessed'" class="sr-list-item-status-label">
                    {{ getComplianceStatusLabel(sr.compliance_status) }}
                  </div>
                </div>
              </div>
            </template>
          </Card>
        </div>

        <!-- Pannello Centrale - Nuova UX basata su Capabilities -->
        <div class="sr-center-panel" v-if="selectedSR">
          <Card>
            <template #content>
              <div v-if="loadingAssessmentData" class="text-center p-4">
                <ProgressSpinner />
                <p class="text-muted mt-2">{{ t('isa62443.compliance.loadingAssessmentData') }}</p>
              </div>
              
              <div v-else-if="assessmentData">
                <!-- A. Cosa chiede lo SR -->
                <div class="sr-description-section mb-4">
                  <div class="sr-description-header">
                    <div>
                      <h3 class="sr-description-title mb-2">{{ assessmentData.sr.requirement_id }} - {{ assessmentData.sr.title }}</h3>
                      <div class="sr-sl-info mt-2">
                        <Tag :value="`SL-${selectedSR.min_security_level || '-'}${selectedSR.max_security_level ? `-${selectedSR.max_security_level}` : '+'}`" severity="info" />
                      </div>
                    </div>
                    <div v-if="assessmentData.current_assessment" class="sr-status-badge-header">
                      <Tag 
                        :value="getComplianceStatusLabel(assessmentData.current_assessment.status)"
                        :severity="getComplianceStatusSeverity(assessmentData.current_assessment.status)"
                      />
                    </div>
                  </div>
                  <div class="sr-description mt-3">
                    <p>{{ assessmentData.sr.description || selectedSR?.requirement_text || t('isa62443.compliance.noDescription') }}</p>
                  </div>
                </div>

                <Divider />

                <!-- A. Capability richieste -->
                <div class="sr-required-capabilities mb-4">
                  <h4 class="sr-section-title mb-3">
                    <i class="pi pi-list-check mr-2"></i>
                    {{ t('isa62443.compliance.requiredCapabilities') }}
                  </h4>
                  <div class="capabilities-list">
                    <div 
                      v-for="cap in assessmentData.required_capabilities" 
                      :key="cap.capability_id"
                      class="capability-item"
                      :class="{ 'capability-primary': cap.importance === 'primary', 'capability-supporting': cap.importance === 'supporting' }"
                    >
                      <div class="capability-header">
                        <i :class="cap.importance === 'primary' ? 'pi pi-check-circle' : 'pi pi-circle'" 
                           :style="{ color: cap.importance === 'primary' ? '#28a745' : '#6c757d' }"></i>
                        <strong class="ml-2">{{ cap.name }}</strong>
                        <Tag :value="cap.importance === 'primary' ? t('isa62443.compliance.mandatory') : t('isa62443.compliance.important')" 
                             :severity="cap.importance === 'primary' ? 'success' : 'info'"
                             class="ml-2" />
                      </div>
                      <div class="capability-applies-to mt-2 text-sm text-muted">
                        <span v-if="cap.applies_to_asset">{{ t('isa62443.compliance.appliesToAsset') }}</span>
                        <span v-if="cap.applies_to_asset && cap.applies_to_conduit">, </span>
                        <span v-if="cap.applies_to_conduit">{{ t('isa62443.compliance.appliesToConduit') }}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <Divider />

                <!-- B. Cosa ESISTE nel sistema -->
                <div class="sr-available-evidence mb-4">
                  <h4 class="sr-section-title mb-3">
                    <i class="pi pi-check-square mr-2"></i>
                    {{ t('isa62443.compliance.availableEvidence') }}
                  </h4>
                  
                  <!-- Asset Evidence -->
                  <div v-if="assessmentData.available_evidence.assets.length > 0" class="evidence-section mb-3">
                    <h5 class="evidence-section-title mb-2">{{ t('isa62443.compliance.assets') }}</h5>
                    <div class="evidence-list">
                      <div 
                        v-for="assetEv in assessmentData.available_evidence.assets" 
                        :key="assetEv.asset_id"
                        class="evidence-item"
                        :class="{ 'evidence-verified': assetEv.status === 'verified', 'evidence-declared': assetEv.status === 'declared' }"
                      >
                        <div class="evidence-header">
                          <i :class="assetEv.status === 'verified' ? 'pi pi-check-circle text-green-500' : 'pi pi-info-circle text-orange-500'"></i>
                          <strong class="ml-2">{{ assetEv.asset_name }}</strong>
                          <Tag :value="assetEv.status === 'verified' ? t('isa62443.compliance.verified') : t('isa62443.compliance.declared')" 
                               :severity="assetEv.status === 'verified' ? 'success' : 'warning'"
                               class="ml-2" />
                        </div>
                        <div class="evidence-capabilities mt-2">
                          <div 
                            v-for="cap in assetEv.capabilities" 
                            :key="cap.capability.capability_id"
                            class="evidence-capability-item text-sm"
                          >
                            • {{ cap.capability.name }}: 
                            <span :class="cap.status === 'verified' ? 'text-green-500' : 'text-orange-500'">
                              {{ cap.status === 'verified' ? t('isa62443.compliance.supported') : t('isa62443.compliance.declared') }}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Conduit Evidence -->
                  <div v-if="assessmentData.available_evidence.conduits.length > 0" class="evidence-section mb-3">
                    <h5 class="evidence-section-title mb-2">{{ t('isa62443.compliance.conduits') }}</h5>
                    <div class="evidence-list">
                      <div 
                        v-for="conduitEv in assessmentData.available_evidence.conduits" 
                        :key="`${conduitEv.conduit_id}-${conduitEv.asset_id}`"
                        class="evidence-item"
                        :class="{ 'evidence-verified': conduitEv.status === 'verified', 'evidence-declared': conduitEv.status === 'declared' }"
                      >
                        <div class="evidence-header">
                          <i :class="conduitEv.status === 'verified' ? 'pi pi-check-circle text-green-500' : 'pi pi-info-circle text-orange-500'"></i>
                          <strong class="ml-2">{{ conduitEv.conduit_name }}</strong>
                          <span class="text-muted ml-2">({{ conduitEv.asset_name }}, {{ conduitEv.role }})</span>
                          <Tag :value="conduitEv.status === 'verified' ? t('isa62443.compliance.verified') : t('isa62443.compliance.declared')" 
                               :severity="conduitEv.status === 'verified' ? 'success' : 'warning'"
                               class="ml-2" />
                        </div>
                        <div class="evidence-capabilities mt-2">
                          <div 
                            v-for="cap in conduitEv.capabilities" 
                            :key="cap.capability.capability_id"
                            class="evidence-capability-item text-sm"
                          >
                            • {{ cap.capability.name }}: 
                            <span :class="cap.status === 'verified' ? 'text-green-500' : 'text-orange-500'">
                              {{ cap.status === 'verified' ? t('isa62443.compliance.supported') : t('isa62443.compliance.declared') }}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Missing Capabilities Warning -->
                  <div v-if="assessmentData.missing_capabilities.length > 0" class="missing-capabilities-warning mt-3">
                    <div 
                      v-for="missing in assessmentData.missing_capabilities" 
                      :key="missing.capability.capability_id"
                      class="missing-capability-item"
                    >
                      <i class="pi pi-exclamation-triangle text-orange-500 mr-2"></i>
                      <span class="text-muted">{{ missing.message }}</span>
                    </div>
                  </div>

                  <div v-if="assessmentData.available_evidence.assets.length === 0 && assessmentData.available_evidence.conduits.length === 0" class="text-muted mt-3">
                    <i class="pi pi-info-circle mr-2"></i>
                    {{ t('isa62443.compliance.noEvidenceAvailable') }}
                  </div>
                </div>

                <Divider />

                <!-- C. Decisione finale -->
                <div class="sr-final-assessment mb-4">
                  <h4 class="sr-section-title mb-3">
                    <i class="pi pi-clipboard mr-2"></i>
                    {{ t('isa62443.compliance.finalAssessment') }}
                  </h4>
                  
                  <div class="assessment-status-selection mt-3">
                    <label class="assessment-status-label mb-3">{{ t('isa62443.compliance.assessmentStatus') }}</label>
                    <div class="assessment-status-options">
                      <div class="assessment-status-option">
                        <RadioButton 
                          :inputId="`assessment-status-compliant`"
                          name="assessment-status"
                          value="compliant"
                          v-model="assessmentStatus"
                        />
                        <label :for="`assessment-status-compliant`" class="ml-2">
                          <i class="pi pi-check-circle text-green-500 mr-1"></i>
                          {{ t('isa62443.compliance.compliant') }}
                        </label>
                      </div>
                      <div class="assessment-status-option">
                        <RadioButton 
                          :inputId="`assessment-status-partial`"
                          name="assessment-status"
                          value="partial"
                          v-model="assessmentStatus"
                        />
                        <label :for="`assessment-status-partial`" class="ml-2">
                          <i class="pi pi-exclamation-circle text-orange-500 mr-1"></i>
                          {{ t('isa62443.compliance.partial') }}
                        </label>
                      </div>
                      <div class="assessment-status-option">
                        <RadioButton 
                          :inputId="`assessment-status-non-compliant`"
                          name="assessment-status"
                          value="non_compliant"
                          v-model="assessmentStatus"
                        />
                        <label :for="`assessment-status-non-compliant`" class="ml-2">
                          <i class="pi pi-times-circle text-red-500 mr-1"></i>
                          {{ t('isa62443.compliance.nonCompliant') }}
                        </label>
                      </div>
                      <div class="assessment-status-option">
                        <RadioButton 
                          :inputId="`assessment-status-not-applicable`"
                          name="assessment-status"
                          value="not_applicable"
                          v-model="assessmentStatus"
                        />
                        <label :for="`assessment-status-not-applicable`" class="ml-2">
                          <i class="pi pi-minus-circle text-gray-500 mr-1"></i>
                          {{ t('isa62443.compliance.notApplicable') }}
                        </label>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Giustificazione (obbligatoria se != compliant) -->
                  <div class="assessment-justification-section mt-4">
                    <label class="assessment-justification-label mb-2">
                      {{ t('isa62443.compliance.justification') }}
                      <span v-if="assessmentStatus && assessmentStatus !== 'compliant'" class="text-red-500">*</span>
                    </label>
                    <Textarea 
                      v-model="assessmentJustification"
                      :rows="6"
                      class="w-full"
                      :placeholder="t('isa62443.compliance.justificationPlaceholder')"
                    />
                    <small class="text-muted mt-2 d-block">
                      {{ t('isa62443.compliance.justificationRequired') }}
                    </small>
                  </div>

                  <!-- Evidence Section -->
                  <div class="assessment-evidence-section mt-4">
                    <EvidenceList
                      :sr-assessment-id="assessmentData?.current_assessment?.id"
                      :zone-id="zone.id"
                      :can-write="true"
                      @evidence-updated="handleEvidenceUpdated"
                    />
                  </div>

                  <!-- Save Button -->
                  <div class="assessment-actions mt-4">
                    <Button 
                      :label="t('isa62443.compliance.saveAssessment')"
                      icon="pi pi-save"
                      @click="saveAssessment"
                      :disabled="!assessmentStatus || (assessmentStatus !== 'compliant' && !assessmentJustification)"
                      class="p-button-primary"
                    />
                  </div>
                </div>
              </div>
              
              <div v-else class="text-center p-4 text-muted">
                <i class="pi pi-info-circle text-4xl mb-3"></i>
                <p>{{ t('isa62443.compliance.errorLoadingAssessmentData') }}</p>
              </div>
            </template>
          </Card>
        </div>
        <div v-else class="sr-center-panel">
          <Card>
            <template #content>
              <div class="text-center p-4 text-muted">
                <i class="pi pi-info-circle text-4xl mb-3"></i>
                <p>{{ t('isa62443.compliance.selectSR') }}</p>
              </div>
            </template>
          </Card>
        </div>

        <!-- Pannello Destro (Collassabile) -->
        <div class="sr-right-panel" v-if="selectedSR">
          <Card>
            <template #header>
              <div class="flex justify-content-between align-items-center w-full">
                <span class="font-bold">{{ t('isa62443.compliance.detailsAndEvidence') }}</span>
                <Button 
                  :icon="rightPanelCollapsed ? 'pi pi-chevron-down' : 'pi pi-chevron-up'"
                  class="p-button-text p-button-sm"
                  @click="rightPanelCollapsed = !rightPanelCollapsed"
                />
              </div>
            </template>
            <template #content v-if="!rightPanelCollapsed && selectedSR">
              <!-- Asset Coinvolti -->
              <div class="sr-detail-section">
                <h4 class="sr-detail-section-title">
                  <i class="pi pi-server mr-2"></i>
                  {{ t('isa62443.compliance.involvedAssets') }}
                </h4>
                <div v-if="selectedSRAssets.length === 0" class="text-muted">
                  {{ t('isa62443.compliance.noAssets') }}
                </div>
                <div v-else class="sr-assets-list">
                  <div 
                    v-for="asset in selectedSRAssets" 
                    :key="asset.id"
                    class="sr-asset-item"
                    @click="goToAsset(asset.id)"
                  >
                    {{ asset.name }}
                  </div>
                </div>
              </div>

              <!-- Conduits Coinvolti -->
              <div class="sr-detail-section mt-4">
                <h4 class="sr-detail-section-title">
                  <i class="pi pi-sitemap mr-2"></i>
                  {{ t('isa62443.compliance.involvedConduits') }}
                </h4>
                <div v-if="selectedSRConduits.length === 0" class="text-muted">
                  {{ t('isa62443.compliance.noConduits') }}
                </div>
                <div v-else class="sr-conduits-list">
                  <div 
                    v-for="conduit in selectedSRConduits" 
                    :key="conduit.id"
                    class="sr-conduit-item"
                    @click="goToConduit(conduit.id)"
                  >
                    {{ conduit.name }}
                  </div>
                </div>
              </div>

              <!-- Evidenze -->
              <div class="sr-detail-section mt-4">
                <h4 class="sr-detail-section-title">
                  <i class="pi pi-file mr-2"></i>
                  {{ t('isa62443.compliance.evidence') }}
                </h4>
                <div class="sr-evidence-notes">
                  <Textarea 
                    v-model="selectedSR.evidence_notes"
                    :rows="4"
                    class="w-full"
                    :placeholder="t('isa62443.compliance.evidencePlaceholder')"
                    @blur="saveEvidenceNotes"
                    v-if="selectedSR"
                  />
                </div>
              </div>
            </template>
          </Card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import Card from 'primevue/card'
import Button from 'primevue/button'
import ProgressSpinner from 'primevue/progressspinner'
import RadioButton from 'primevue/radiobutton'
import Textarea from 'primevue/textarea'
import Tag from 'primevue/tag'
import Divider from 'primevue/divider'
import api from '@/api/api'
import EvidenceList from './EvidenceList.vue'

const props = defineProps({
  zone: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['zone-updated'])

const { t } = useI18n()
const router = useRouter()
const toast = useToast()

// State
const currentLevel = ref('dashboard')
const loadingFR = ref(false)
const loadingSR = ref(false)
const loadingAssessmentData = ref(false)
const foundationRequirements = ref([])
const securityRequirements = ref([])
const selectedFR = ref(null)
const selectedSR = ref(null)
const selectedSRAssets = ref([])
const selectedSRConduits = ref([])
const rightPanelCollapsed = ref(false)
const summary = ref({
  compliant: 0,
  partial: 0,
  non_compliant: 0,
  not_applicable: 0
})

// New capability-based assessment state
const assessmentData = ref(null)
const assessmentStatus = ref(null) // 'compliant', 'partial', 'non_compliant', 'not_applicable', 'insufficient_info'
const assessmentJustification = ref('')
const selectedEvidence = ref([]) // Array of {asset_id, capability_id, comment}

// Computed
const getGap = () => {
  const target = props.zone.security_level_target
  const achieved = props.zone.security_level_achieved
  
  // Check if values are null/undefined (not if they are 0)
  if (target === null || target === undefined || achieved === null || achieved === undefined) {
    return '-'
  }
  const gap = achieved - target
  return gap >= 0 ? `+${gap}` : `${gap}`
}

const getGapValue = () => {
  const target = props.zone.security_level_target
  const achieved = props.zone.security_level_achieved
  
  // Check if values are null/undefined (not if they are 0)
  if (target === null || target === undefined || achieved === null || achieved === undefined) {
    return 0
  }
  return achieved - target
}

const getGapClass = () => {
  const gap = getGapValue()
  if (gap < 0) return 'text-orange-500'
  if (gap === 0) return 'text-green-500'
  return 'text-blue-500'
}

const getFRCardClass = (fr) => {
  const percentage = fr.compliance_percentage || 0
  if (percentage >= 80) return 'fr-card-compliant'
  if (percentage >= 50) return 'fr-card-partial'
  return 'fr-card-non-compliant'
}

const getFRPercentageClass = (fr) => {
  const percentage = fr.compliance_percentage || 0
  if (percentage >= 80) return 'text-green-500'
  if (percentage >= 50) return 'text-orange-500'
  return 'text-red-500'
}

// FR Titles, Descriptions and typical assets - helper functions
function getFRTitle(frId) {
  if (!frId) return ''
  
  const frTitles = {
    'FR1': 'Identification & Authentication',
    'FR2': 'Use Control',
    'FR3': 'System Integrity',
    'FR4': 'Data Confidentiality',
    'FR5': 'Restricted Data Flow',
    'FR6': 'Timely Response to Events',
    'FR7': 'Resource Availability'
  }
  
  // Normalize FR ID (handle "FR1", "FR 1", "fr1", etc.)
  const normalized = frId.toUpperCase().replace(/\s+/g, '')
  return frTitles[normalized] || ''
}

function getFRDescription(frId) {
  if (!frId) return null
  // Normalize FR ID (handle both "FR1" and "FR 1" formats)
  const normalizedId = frId.replace(/\s+/g, '').toUpperCase()
  const frNumber = normalizedId.replace('FR', '')
  if (frNumber && frNumber >= '1' && frNumber <= '7') {
    return t(`isa62443.compliance.fr${frNumber}.description`)
  }
  return null
}

function getFRTypicalAssets(frId) {
  if (!frId) return null
  // Normalize FR ID (handle both "FR1" and "FR 1" formats)
  const normalizedId = frId.replace(/\s+/g, '').toUpperCase()
  const frNumber = normalizedId.replace('FR', '')
  if (frNumber && frNumber >= '1' && frNumber <= '7') {
    return t(`isa62443.compliance.fr${frNumber}.typicalAssets`)
  }
  return null
}

// Compliance status helpers for visual indicators
function getComplianceStatusIcon(status) {
  const icons = {
    'compliant': 'pi pi-check-circle',
    'partial': 'pi pi-exclamation-circle',
    'non_compliant': 'pi pi-times-circle',
    'not_applicable': 'pi pi-minus-circle',
    'not_assessed': null
  }
  return icons[status] || null
}

function getComplianceStatusColor(status) {
  const colors = {
    'compliant': '#28a745', // green
    'partial': '#ffc107', // orange/yellow
    'non_compliant': '#dc3545', // red
    'not_applicable': '#6c757d', // gray
    'not_assessed': null
  }
  return colors[status] || null
}

function getComplianceStatusLabel(status) {
  const labels = {
    'compliant': t('isa62443.compliance.compliant'),
    'partial': t('isa62443.compliance.partial'),
    'non_compliant': t('isa62443.compliance.nonCompliant'),
    'not_applicable': t('isa62443.compliance.notApplicable'),
    'not_assessed': null
  }
  return labels[status] || null
}

function getComplianceStatusSeverity(status) {
  const severities = {
    'compliant': 'success',
    'partial': 'warning',
    'non_compliant': 'danger',
    'not_applicable': 'secondary',
    'not_assessed': null
  }
  return severities[status] || null
}

// Methods
async function loadSummary() {
  try {
    const res = await api.getZoneCompliance(props.zone.id)
    // Backend now returns a summary object directly, not an array
    const data = res.data || {}
    
    summary.value = {
      compliant: data.compliant || 0,
      partial: data.partial || 0,
      non_compliant: data.non_compliant || 0,
      not_applicable: data.not_applicable || 0
    }
  } catch (error) {
    console.error('Error loading compliance summary:', error)
    // Set defaults on error
    summary.value = {
      compliant: 0,
      partial: 0,
      non_compliant: 0,
      not_applicable: 0
    }
  }
}

async function showFoundationRequirements() {
  currentLevel.value = 'foundation-requirements'
  loadingFR.value = true
  foundationRequirements.value = [] // Reset
  try {
    const res = await api.getZoneFoundationRequirements(props.zone.id)
    console.log('Foundation Requirements response:', res)
    foundationRequirements.value = res.data || []
    console.log('Foundation Requirements loaded:', foundationRequirements.value.length)
    
    if (foundationRequirements.value.length === 0) {
      toast.add({
        severity: 'info',
        summary: t('common.messages.info'),
        detail: t('isa62443.compliance.noFoundationRequirements'),
        life: 3000
      })
    }
  } catch (error) {
    console.error('Error loading foundation requirements:', error)
    console.error('Error details:', error.response?.data)
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: error.response?.data?.detail || error.message || t('isa62443.compliance.errorLoadingFR')
    })
  } finally {
    loadingFR.value = false
  }
}

async function selectFoundationRequirement(fr) {
  selectedFR.value = fr
  selectedSR.value = null // Reset selected SR
  currentLevel.value = 'security-requirements'
  loadingSR.value = true
  securityRequirements.value = []
  selectedSRAssets.value = []
  selectedSRConduits.value = []
  
  try {
    console.log('Loading SRs for FR:', fr.requirement_id, 'Zone:', props.zone.id)
    const res = await api.getZoneSecurityRequirementsByFR(props.zone.id, fr.requirement_id)
    console.log('SRs response:', res.data)
    const srs = res.data || []
    
    // Sort SRs numerically by requirement_id (e.g., "SR 1.1", "SR 1.2", "SR 1.10" instead of "SR 1.1", "SR 1.10", "SR 1.2")
    const naturalSort = (a, b) => {
      const extractNumbers = (reqId) => {
        if (!reqId) return [0, 0]
        const numbers = reqId.match(/\d+/g) || []
        if (numbers.length >= 2) {
          return [parseInt(numbers[0]), parseInt(numbers[1])]
        } else if (numbers.length === 1) {
          return [parseInt(numbers[0]), 0]
        }
        return [0, 0]
      }
      
      const aNums = extractNumbers(a.requirement_id)
      const bNums = extractNumbers(b.requirement_id)
      
      // Compare first number
      if (aNums[0] !== bNums[0]) {
        return aNums[0] - bNums[0]
      }
      // Compare second number
      return aNums[1] - bNums[1]
    }
    
    securityRequirements.value = srs.sort(naturalSort)
    console.log('Loaded SRs:', securityRequirements.value.length)
    
    if (securityRequirements.value.length === 0) {
      toast.add({
        severity: 'info',
        summary: t('common.messages.info'),
        detail: t('isa62443.compliance.noSecurityRequirementsForFR'),
        life: 3000
      })
    } else {
      // Load first SR by default if available
      // Wait a bit for the UI to update
      await new Promise(resolve => setTimeout(resolve, 100))
      await selectSecurityRequirement(securityRequirements.value[0])
    }
  } catch (error) {
    console.error('Error loading security requirements:', error)
    console.error('Error details:', error.response?.data)
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: error.response?.data?.detail || error.message || t('isa62443.compliance.errorLoadingSR')
    })
  } finally {
    loadingSR.value = false
  }
}

async function selectSecurityRequirement(sr) {
  if (!sr || !sr.id) {
    console.error('Invalid SR selected:', sr)
    return
  }
  
  selectedSR.value = sr
  loadingAssessmentData.value = true
  assessmentData.value = null
  assessmentStatus.value = null
  assessmentJustification.value = ''
  selectedEvidence.value = []
  
  try {
    // Load assisted assessment data
    const res = await api.getSRAssessmentAssist(props.zone.id, sr.id)
    assessmentData.value = res.data
    
    // Set current assessment status if exists
    if (assessmentData.value.current_assessment) {
      assessmentStatus.value = assessmentData.value.current_assessment.status
      assessmentJustification.value = assessmentData.value.current_assessment.justification || ''
      
      // Build selected evidence from current assessment
      selectedEvidence.value = assessmentData.value.current_assessment.evidence.map(ev => ({
        asset_id: ev.asset_id,
        capability_id: ev.capability_id,
        comment: ev.comment || ''
      }))
    }
    
    // Also load legacy assets/conduits for backward compatibility
    try {
      const [assetsRes, conduitsRes] = await Promise.all([
        api.getSRInvolvedAssets(props.zone.id, sr.id),
        api.getSRInvolvedConduits(props.zone.id, sr.id)
      ])
      selectedSRAssets.value = assetsRes.data || []
      selectedSRConduits.value = conduitsRes.data || []
    } catch (legacyError) {
      console.warn('Error loading legacy SR details:', legacyError)
      // Non-blocking error
    }
  } catch (error) {
    console.error('Error loading SR assessment data:', error)
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: error.response?.data?.detail || error.message || t('isa62443.compliance.errorLoadingAssessmentData')
    })
    assessmentData.value = null
  } finally {
    loadingAssessmentData.value = false
  }
}

function handleEvidenceUpdated() {
  // Refresh assessment data when evidence is updated
  if (selectedSR.value) {
    selectSecurityRequirement(selectedSR.value)
  }
}

async function saveAssessment() {
  if (!assessmentStatus.value) {
    toast.add({
      severity: 'warn',
      summary: t('common.messages.warning'),
      detail: t('isa62443.compliance.selectAssessmentStatus'),
      life: 3000
    })
    return
  }
  
  if (assessmentStatus.value !== 'compliant' && !assessmentJustification.value.trim()) {
    toast.add({
      severity: 'warn',
      summary: t('common.messages.warning'),
      detail: t('isa62443.compliance.justificationRequired'),
      life: 3000
    })
    return
  }
  
  try {
    // Build evidence list from available evidence
    const evidence = []
    
    // Add asset evidence
    if (assessmentData.value?.available_evidence?.assets) {
      for (const assetEv of assessmentData.value.available_evidence.assets) {
        for (const cap of assetEv.capabilities) {
          evidence.push({
            asset_id: assetEv.asset_id,
            capability_id: cap.capability.capability_id,
            comment: ''
          })
        }
      }
    }
    
    // Add conduit evidence
    if (assessmentData.value?.available_evidence?.conduits) {
      for (const conduitEv of assessmentData.value.available_evidence.conduits) {
        for (const cap of conduitEv.capabilities) {
          evidence.push({
            asset_id: conduitEv.asset_id,
            capability_id: cap.capability.capability_id,
            comment: ''
          })
        }
      }
    }
    
    const assessmentPayload = {
      status: assessmentStatus.value,
      justification: assessmentJustification.value,
      evidence: evidence
    }
    
    const res = await api.createOrUpdateSRAssessment(props.zone.id, selectedSR.value.id, assessmentPayload)
    
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: t('isa62443.compliance.assessmentSaved'),
      life: 3000
    })
    
    // Reload assessment data to get updated status
    await selectSecurityRequirement(selectedSR.value)
    
    // Emit zone-updated with recalculated SL-A and compliance from backend
    const zoneUpdated = res.data?.zone_updated
    if (zoneUpdated) {
      emit('zone-updated', { ...props.zone, ...zoneUpdated })
    } else {
      emit('zone-updated', props.zone)
    }
    // Refresh dashboard summary (compliant/partial/non_compliant counts)
    await loadSummary()
  } catch (error) {
    console.error('Error saving assessment:', error)
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: error.response?.data?.detail || error.message || t('isa62443.compliance.errorSavingAssessment'),
      life: 5000
    })
  }
}


function onApplicabilityChange() {
  if (srApplicability.value === 'no') {
    // Se non applicabile, salva immediatamente
    updateComplianceStatus(selectedSR.value, 'not_applicable')
  }
}

// Ottiene le caratteristiche tecniche osservabili per un asset in base all'SR
function getAssetTechnicalCharacteristics(asset) {
  // TODO: Implementare logica specifica per SR
  // Per ora, mostriamo caratteristiche generiche basate sui dati dell'asset
  const characteristics = {}
  
  // Esempio per SR 2.5 (Session Lock) - da estendere con logica SR-specific
  if (selectedSR.value?.requirement_id?.includes('2.5')) {
    // Per SR 2.5, mostriamo caratteristiche relative a sessioni interattive
    characteristics[t('isa62443.compliance.interactiveSessions')] = asset.remote_access ? 'YES' : 'NO'
    characteristics[t('isa62443.compliance.sessionLockSupported')] = asset.custom_fields?.session_lock_supported ? 'YES' : 'NO'
  } else {
    // Caratteristiche generiche per altri SR
    characteristics[t('isa62443.compliance.remoteAccess')] = asset.remote_access ? 'YES' : 'NO'
    if (asset.remote_access) {
      characteristics[t('isa62443.compliance.remoteAccessType')] = asset.remote_access_type || 'none'
    }
  }
  
  return characteristics
}

function isAssetRelevantForSR(asset) {
  // TODO: Implementare logica per determinare se un asset è rilevante per l'SR
  // Per ora, assumiamo che tutti gli asset siano rilevanti
  const characteristics = getAssetTechnicalCharacteristics(asset)
  return Object.keys(characteristics).length > 0
}

function formatCharacteristicValue(value) {
  if (typeof value === 'boolean') {
    return value ? 'YES' : 'NO'
  }
  if (value === null || value === undefined) {
    return 'N/A'
  }
  return String(value).toUpperCase()
}

function getCharacteristicValueClass(value) {
  if (value === true || value === 'YES' || value === 'yes') {
    return 'text-success'
  }
  if (value === false || value === 'NO' || value === 'no') {
    return 'text-danger'
  }
  return 'text-muted'
}

async function updateComplianceStatus(sr, status) {
  try {
    const complianceData = {
      requirement_id: sr.id,
      zone_id: props.zone.id,
      compliance_status: status,
      assessment_notes: sr.assessment_notes || null
    }
    
    // Check if compliance record exists
    const existing = sr.compliance_id
    if (existing) {
      await api.updateCompliance(existing, { compliance_status: status })
    } else {
      await api.assessCompliance(complianceData)
    }
    
    sr.compliance_status = status
    
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: t('isa62443.compliance.statusUpdated')
    })
    
    // Reload summary
    await loadSummary()
    
    // Recalculate security level achieved and update zone
    try {
      const slRes = await api.calculateZoneSecurityLevel(props.zone.id)
      if (slRes.data) {
        // Update zone prop by emitting event to parent
        emit('zone-updated', slRes.data)
      }
    } catch (slError) {
      console.error('Error recalculating security level:', slError)
      // Don't show error to user, just log it
    }
  } catch (error) {
    console.error('Error updating compliance status:', error)
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: error.response?.data?.detail || t('isa62443.compliance.errorUpdatingStatus')
    })
  }
}

async function saveAssessmentNotes() {
  if (!selectedSR.value) return
  
  try {
    const complianceData = {
      requirement_id: selectedSR.value.id,
      zone_id: props.zone.id,
      compliance_status: selectedSR.value.compliance_status || 'not_assessed',
      assessment_notes: selectedSR.value.assessment_notes || null
    }
    
    const existing = selectedSR.value.compliance_id
    if (existing) {
      await api.updateCompliance(existing, { assessment_notes: selectedSR.value.assessment_notes })
    } else {
      await api.assessCompliance(complianceData)
    }
    
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: t('isa62443.compliance.notesSaved')
    })
  } catch (error) {
    console.error('Error saving assessment notes:', error)
  }
}

async function saveEvidenceNotes() {
  if (!selectedSR.value) return
  
  try {
    const complianceData = {
      requirement_id: selectedSR.value.id,
      zone_id: props.zone.id,
      compliance_status: selectedSR.value.compliance_status || 'not_assessed',
      evidence_notes: selectedSR.value.evidence_notes || null
    }
    
    const existing = selectedSR.value.compliance_id
    if (existing) {
      await api.updateCompliance(existing, { evidence_notes: selectedSR.value.evidence_notes })
    } else {
      await api.assessCompliance(complianceData)
    }
    
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: t('isa62443.compliance.evidenceSaved')
    })
  } catch (error) {
    console.error('Error saving evidence notes:', error)
  }
}

function goToAsset(assetId) {
  router.push(`/assets/${assetId}`)
}

function goToConduit(conduitId) {
  router.push(`/conduits`)
}

// Watch zone changes
watch(() => props.zone.id, () => {
  if (props.zone.id) {
    loadSummary()
  }
})

onMounted(() => {
  if (props.zone.id) {
    loadSummary()
  }
})
</script>

<style scoped>
.zone-compliance-tab {
  padding: 1rem;
}

/* Dashboard */
.compliance-dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.zone-name {
  margin: 0;
  font-size: 1.5rem;
}

.sl-summary {
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
}

.sl-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.sl-label {
  font-size: 0.875rem;
  color: var(--text-color-secondary);
}

.sl-value {
  font-size: 1.25rem;
  font-weight: 600;
}

.sr-status-summary {
  margin-top: 2rem;
}

.section-title {
  font-size: 1.125rem;
  margin-bottom: 1rem;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.status-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
  border-radius: 8px;
  background: var(--surface-ground);
}

.status-item i {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.status-item.compliant i {
  color: var(--green-500);
}

.status-item.partial i {
  color: var(--orange-500);
}

.status-item.non-compliant i {
  color: var(--red-500);
}

.status-item.not-applicable i {
  color: var(--gray-500);
}

.status-count {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.status-label {
  font-size: 0.875rem;
  color: var(--text-color-secondary);
}

/* Foundation Requirements */
.foundation-requirements {
  max-width: 1400px;
  margin: 0 auto;
}

.level-header {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.fr-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.fr-card {
  cursor: pointer;
  transition: all 0.2s;
}

.fr-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.fr-card-content {
  padding: 1rem;
}

.fr-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.fr-id {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.fr-percentage {
  font-size: 1.5rem;
  font-weight: 700;
}

.fr-title {
  font-size: 0.875rem;
  color: var(--text-color-secondary);
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.fr-description {
  font-size: 0.8rem;
  color: var(--text-color);
  margin-bottom: 0.5rem;
  line-height: 1.4;
}

.fr-typical-assets {
  font-size: 0.75rem;
  color: var(--text-color-secondary);
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.fr-stats {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
}

.fr-stat {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

/* Security Requirements Detail */
.security-requirements-detail {
  max-width: 1800px;
  margin: 0 auto;
}

.sr-detail-layout {
  display: grid;
  grid-template-columns: 320px 1fr 380px;
  gap: 1.5rem;
  align-items: start;
}

.sr-left-panel {
  position: sticky;
  top: 1rem;
  max-height: calc(100vh - 100px);
  overflow-y: auto;
}

.sr-list-container {
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.sr-list-empty {
  padding: 2rem 1rem;
  text-align: center;
  color: var(--text-color-secondary);
}

.sr-list-empty i {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.sr-list-item {
  padding: 0.5rem 0.75rem;
  margin-bottom: 0.375rem;
  border: 1px solid var(--surface-border);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.sr-list-item:hover {
  border-color: var(--primary-color);
  background: var(--surface-ground);
}

.sr-list-item.sr-list-item-active {
  border-color: var(--primary-color);
  background: var(--primary-color-light);
}

.sr-list-item.sr-list-item-assessed {
  border-left: 3px solid;
  border-left-color: var(--surface-border);
}

.sr-list-item.sr-list-item-assessed[data-status="compliant"] {
  border-left-color: #28a745;
}

.sr-list-item.sr-list-item-assessed[data-status="partial"] {
  border-left-color: #ffc107;
}

.sr-list-item.sr-list-item-assessed[data-status="non_compliant"] {
  border-left-color: #dc3545;
}

.sr-list-item.sr-list-item-assessed[data-status="not_applicable"] {
  border-left-color: #6c757d;
}

.sr-list-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
}

.sr-list-item-id {
  font-weight: 600;
  font-size: 0.8rem;
  color: var(--primary-color);
}

.sr-list-item-status-badge {
  display: flex;
  align-items: center;
  font-size: 0.875rem;
}

.sr-list-item-title {
  font-size: 0.75rem;
  color: var(--text-color);
  line-height: 1.3;
  margin-bottom: 0.125rem;
}

.sr-list-item-status-label {
  font-size: 0.65rem;
  font-weight: 500;
  color: var(--text-color-secondary);
  margin-top: 0.125rem;
}

/* Processo guidato di valutazione */
.sr-assessment-step {
  margin-bottom: 2rem;
}

.sr-step-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 1rem;
}

.sr-step-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  background: var(--primary-color);
  color: white;
  font-weight: 700;
  font-size: 0.9rem;
}

.sr-applicability-options {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.sr-step-subtitle {
  font-size: 0.875rem;
  font-style: italic;
}

.sr-assets-justification-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.sr-asset-justification-card {
  padding: 1rem;
  border: 1px solid var(--surface-border);
  border-radius: 8px;
  background: var(--surface-ground);
}

.sr-asset-justification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sr-asset-justification-name {
  display: flex;
  align-items: center;
  font-size: 0.95rem;
}

.sr-asset-technical-characteristics {
  margin-top: 0.75rem;
}

.sr-asset-characteristic-item {
  display: flex;
  align-items: baseline;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  line-height: 1.6;
}

.sr-characteristic-label {
  font-weight: 500;
  color: var(--text-color);
  margin-right: 0.5rem;
  min-width: 200px;
}

.sr-characteristic-value {
  font-weight: 600;
}

.sr-asset-not-relevant {
  padding: 0.5rem;
  background: var(--surface-ground);
  border-radius: 4px;
  font-size: 0.85rem;
}

.sr-zone-status-selection {
  margin-top: 1rem;
}

.sr-zone-status-label {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-color);
  display: block;
}

.sr-zone-status-options {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 0.75rem;
}

.sr-zone-status-option {
  display: flex;
  align-items: center;
  font-size: 0.9rem;
}

.sr-justification-section {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--surface-border);
}

.sr-justification-label {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-color);
  display: block;
}

.sr-applicability-option,
.sr-asset-status-option {
  display: flex;
  align-items: center;
  font-size: 0.9rem;
}

.sr-assets-evaluation-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.sr-asset-evaluation-card {
  padding: 1rem;
  border: 1px solid var(--surface-border);
  border-radius: 8px;
  background: var(--surface-ground);
}

.sr-asset-evaluation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sr-asset-evaluation-name {
  display: flex;
  align-items: center;
  font-size: 0.95rem;
}

.sr-asset-evaluation-status {
  margin-top: 1rem;
}

.sr-asset-status-label,
.sr-asset-notes-label,
.sr-overall-notes-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 0.5rem;
  display: block;
}

.sr-asset-evaluation-notes {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--surface-border);
}

.sr-overall-status-summary {
  margin-top: 1rem;
}

.sr-status-summary-card {
  padding: 1.25rem;
  border-radius: 8px;
  border: 2px solid;
  background: var(--surface-ground);
}

.sr-status-summary-card.sr-status-compliant {
  border-color: #28a745;
  background: rgba(40, 167, 69, 0.1);
}

.sr-status-summary-card.sr-status-partial {
  border-color: #ffc107;
  background: rgba(255, 193, 7, 0.1);
}

.sr-status-summary-card.sr-status-non-compliant {
  border-color: #dc3545;
  background: rgba(220, 53, 69, 0.1);
}

.sr-status-summary-card.sr-status-not-applicable {
  border-color: #6c757d;
  background: rgba(108, 117, 125, 0.1);
}

.sr-status-summary-header {
  display: flex;
  align-items: center;
  font-size: 1.1rem;
  margin-bottom: 0.75rem;
}

.sr-status-summary-breakdown {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.sr-status-breakdown-item {
  font-size: 0.875rem;
  color: var(--text-color-secondary);
}

.sr-overall-notes {
  margin-top: 1.5rem;
}

.sr-save-status {
  margin-top: 1.5rem;
}

.sr-current-status {
  padding-top: 1rem;
  border-top: 1px solid var(--surface-border);
}

.sr-selected-details {
  padding: 0.5rem 0;
}

.sr-selected-header {
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--surface-border);
}

.sr-selected-id {
  font-weight: 700;
  font-size: 1.1rem;
  color: var(--primary-color);
  margin-bottom: 0.5rem;
}

.sr-selected-title {
  font-size: 0.9rem;
  color: var(--text-color);
  line-height: 1.4;
}

.sr-selected-sl {
  padding: 0.75rem;
  background: var(--surface-ground);
  border-radius: 6px;
}

.sr-selected-sl-label {
  font-size: 0.75rem;
  color: var(--text-color-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.25rem;
}

.sr-selected-sl-value {
  font-weight: 700;
  font-size: 1.25rem;
  color: var(--primary-color);
}

.sr-selected-status {
  padding-top: 1rem;
  border-top: 1px solid var(--surface-border);
}

.sr-status-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-color);
}

.sr-status-options {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 0.75rem;
}

.sr-status-option {
  display: flex;
  align-items: center;
  font-size: 0.875rem;
}

.sr-center-panel {
  min-height: 600px;
}

.sr-description-section {
  margin-bottom: 2rem;
}

.sr-description-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
  gap: 1rem;
}

.sr-status-badge-header {
  flex-shrink: 0;
}

.sr-description-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 0.5rem;
}

.sr-description {
  line-height: 1.8;
  color: var(--text-color);
  font-size: 0.95rem;
}

.sr-description p {
  margin: 0;
  text-align: justify;
}

.sr-assessment-notes-section {
  padding-top: 1.5rem;
  border-top: 1px solid var(--surface-border);
}

.sr-assessment-notes-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-color);
}

.sr-right-panel {
  position: sticky;
  top: 1rem;
  max-height: calc(100vh - 100px);
  overflow-y: auto;
}

.sr-detail-section {
  margin-bottom: 1.5rem;
}

.sr-detail-section-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
}

.sr-assets-list,
.sr-conduits-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.sr-asset-item,
.sr-conduit-item {
  padding: 0.5rem;
  border: 1px solid var(--surface-border);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.sr-asset-item:hover,
.sr-conduit-item:hover {
  background: var(--surface-ground);
  border-color: var(--primary-color);
}

.sr-evidence-notes {
  margin-top: 0.5rem;
}

@media (max-width: 1400px) {
  .sr-detail-layout {
    grid-template-columns: 300px 1fr 300px;
  }
}

@media (max-width: 1024px) {
  .sr-detail-layout {
    grid-template-columns: 1fr;
  }
  
  .sr-left-panel,
  .sr-right-panel {
    max-height: none;
  }
}
</style>

