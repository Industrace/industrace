<template>
  <div class="asset-iec62443-tab">
    <div v-if="loading" class="text-center p-4">
      <ProgressSpinner />
    </div>

    <div v-else>
      <!-- Riepilogo Compliance -->
      <Card class="mb-4">
        <template #title>
          <div class="flex align-items-center">
            <i class="pi pi-shield mr-2"></i>
            {{ t('isa62443.compliance.title') }}
          </div>
        </template>
        <template #content>
          <div class="grid">
            <div class="col-12 md:col-4">
              <div class="field">
                <label class="font-semibold">{{ t('isa62443.compliance.securityLevelTarget') }}</label>
                <div class="mt-2">
                  <Tag 
                    v-if="asset.security_level_target" 
                    :value="`SL-${asset.security_level_target}`" 
                    severity="info"
                  />
                  <span v-else class="text-600">-</span>
                </div>
              </div>
            </div>
            <div class="col-12 md:col-4">
              <div class="field">
                <label class="font-semibold">{{ t('isa62443.compliance.securityLevelAchieved') }}</label>
                <div class="mt-2">
                  <Tag 
                    v-if="asset.security_level_achieved" 
                    :value="`SL-${asset.security_level_achieved}`" 
                    :severity="getSLAchievedSeverity(asset.security_level_achieved, asset.security_level_target)"
                  />
                  <span v-else class="text-600">-</span>
                </div>
              </div>
            </div>
            <div class="col-12 md:col-4">
              <div class="field">
                <label class="font-semibold">{{ t('isa62443.compliance.status') }}</label>
                <div class="mt-2">
                  <Tag 
                    v-if="asset.isa62443_compliance_status" 
                    :value="getComplianceStatusLabel(asset.isa62443_compliance_status)" 
                    :severity="getComplianceSeverity(asset.isa62443_compliance_status)"
                  />
                  <span v-else class="text-600">{{ t('isa62443.compliance.notAssessed') }}</span>
                </div>
              </div>
            </div>
            <div class="col-12" v-if="asset.security_level_target && asset.security_level_achieved">
              <div class="field">
                <label class="font-semibold">{{ t('isa62443.compliance.gap') }}</label>
                <div class="mt-2">
                  <Tag 
                    :value="`${gap} ${t('isa62443.compliance.gapLevels')}`" 
                    :severity="getGapSeverity(gap)"
                  />
                </div>
              </div>
            </div>
          </div>
        </template>
      </Card>

      <!-- Zone Memberships -->
      <Card class="mb-4">
        <template #title>
          <div class="flex align-items-center justify-content-between">
            <div class="flex align-items-center">
              <i class="pi pi-users mr-2"></i>
              {{ t('isa62443.securityZones.memberships') }} ({{ memberships.length }})
            </div>
            <Button 
              v-if="typeof canWrite === 'function' ? canWrite() : canWrite"
              :label="t('isa62443.securityZones.addMembership')" 
              icon="pi pi-plus" 
              size="small"
              @click="showAddMembershipDialog = true"
            />
          </div>
        </template>
        <template #content>
          <div v-if="memberships.length === 0" class="text-center p-4 text-600">
            <p>{{ t('isa62443.securityZones.noMemberships') }}</p>
            <p class="text-sm mt-2">{{ t('isa62443.asset.noMembershipsHelp') }}</p>
          </div>
          <DataTable 
            v-else
            :value="memberships" 
            :paginator="true"
            :rows="10"
            class="p-datatable-sm"
          >
            <Column field="security_zone_name" :header="t('isa62443.securityZones.title')" sortable>
              <template #body="{ data }">
                <a 
                  @click="goToZone(data.security_zone_id)" 
                  class="zone-link"
                >
                  {{ data.security_zone_name || data.security_zone_id }}
                </a>
              </template>
            </Column>
            <Column field="role" :header="t('isa62443.securityZones.role')" sortable>
              <template #body="{ data }">
                <Tag :value="data.role" severity="info" />
              </template>
            </Column>
            <Column field="interface_scope" :header="t('isa62443.securityZones.interfaceScope')" sortable>
              <template #body="{ data }">
                {{ data.interface_scope || '-' }}
              </template>
            </Column>
            <Column field="sl_target" :header="t('isa62443.securityZones.slTarget')" sortable>
              <template #body="{ data }">
                <Tag v-if="data.sl_target" :value="`SL-${data.sl_target}`" severity="success" />
                <span v-else class="text-600">-</span>
              </template>
            </Column>
            <Column :header="t('common.actions.actions')" v-if="typeof canWrite === 'function' ? canWrite() : canWrite">
              <template #body="{ data }">
                <div class="flex gap-2">
                  <Button 
                    icon="pi pi-pencil" 
                    class="p-button-text p-button-sm"
                    @click="editMembership(data)"
                    :title="t('common.actions.edit')"
                  />
                  <Button 
                    icon="pi pi-trash" 
                    class="p-button-text p-button-sm p-button-danger"
                    @click="removeMembership(data)"
                    :title="t('common.actions.delete')"
                  />
                </div>
              </template>
            </Column>
          </DataTable>
        </template>
      </Card>

      <!-- Security Requirements Compliance (asset-level SR) -->
      <Card class="mb-4">
        <template #title>
          <div class="flex align-items-center">
            <i class="pi pi-check-circle mr-2"></i>
            {{ t('isa62443.compliance.requirements') }}
          </div>
        </template>
        <template #content>
          <p class="text-sm text-600 mb-3">{{ t('isa62443.compliance.assetSrHelp') }}</p>
          <div v-if="complianceLoading" class="text-center p-4">
            <ProgressSpinner />
          </div>
          <div v-else-if="complianceRecords.length === 0" class="text-center p-4 text-600">
            <p>{{ t('isa62443.compliance.noRequirements') }}</p>
          </div>
          <DataTable 
            v-else
            :value="complianceRecords" 
            :paginator="true"
            :rows="10"
            class="p-datatable-sm"
          >
            <Column field="requirement_id" :header="t('isa62443.compliance.requirementId')" sortable>
              <template #body="{ data }">
                <div>
                  <div class="font-semibold">{{ data.title || data.requirement_id }}</div>
                  <small class="text-600">{{ data.requirement_id }}</small>
                </div>
              </template>
            </Column>
            <Column field="status" :header="t('isa62443.compliance.status')" sortable>
              <template #body="{ data }">
                <Tag 
                  :value="getComplianceStatusLabel(data.status || 'not_assessed')" 
                  :severity="getComplianceSeverity(data.status || 'not_assessed')"
                />
              </template>
            </Column>
            <Column field="assessed_at" :header="t('isa62443.compliance.lastAssessment')" sortable>
              <template #body="{ data }">
                {{ formatDate(data.assessed_at) }}
              </template>
            </Column>
            <Column v-if="typeof canWrite === 'function' ? canWrite() : canWrite" :header="t('common.strings.actions')">
              <template #body="{ data }">
                <Button
                  icon="pi pi-pencil"
                  class="p-button-text p-button-sm"
                  :title="t('isa62443.compliance.assessSr')"
                  @click="openAssessmentDialog(data)"
                />
              </template>
            </Column>
          </DataTable>
        </template>
      </Card>

      <!-- Security Capabilities -->
      <Card class="mb-4">
        <template #title>
          <div class="flex align-items-center justify-content-between">
            <div class="flex align-items-center">
              <i class="pi pi-shield mr-2"></i>
              {{ t('isa62443.capabilities.title') }}
            </div>
            <div class="flex gap-2">
              <Button 
                v-if="(typeof canWrite === 'function' ? canWrite() : canWrite) && selectedCapabilities.length > 0"
                :label="t('isa62443.capabilities.bulkUpdate')" 
                icon="pi pi-check-square" 
                size="small"
                @click="showBulkUpdateDialog = true"
              />
              <Button 
                v-if="typeof canWrite === 'function' ? canWrite() : canWrite"
                :label="t('isa62443.capabilities.addCapability')" 
                icon="pi pi-plus" 
                size="small"
                @click="showAddCapabilityDialog = true"
              />
            </div>
          </div>
        </template>
        <template #content>
          <!-- Filters -->
          <div class="flex gap-2 mb-3">
            <Dropdown
              v-model="capabilityFilters.supportLevel"
              :options="supportLevelOptions"
              optionLabel="label"
              optionValue="value"
              :placeholder="t('isa62443.capabilities.filterBySupportLevel')"
              class="w-full md:w-14rem"
              showClear
            />
            <Dropdown
              v-model="capabilityFilters.category"
              :options="categoryOptions"
              optionLabel="label"
              optionValue="value"
              :placeholder="t('isa62443.capabilities.filterByCategory')"
              class="w-full md:w-14rem"
              showClear
            />
            <Dropdown
              v-model="capabilityFilters.source"
              :options="sourceOptions"
              optionLabel="label"
              optionValue="value"
              :placeholder="t('isa62443.capabilities.filterBySource')"
              class="w-full md:w-14rem"
              showClear
            />
          </div>

          <div v-if="capabilitiesLoading" class="text-center p-4">
            <ProgressSpinner />
          </div>
          <div v-else-if="filteredCapabilities.length === 0" class="text-center p-4 text-600">
            <p>{{ t('isa62443.capabilities.noCapabilities') }}</p>
          </div>
          <DataTable 
            v-else
            :value="filteredCapabilities" 
            :paginator="true"
            :rows="20"
            v-model:selection="selectedCapabilities"
            dataKey="capability_id"
            class="p-datatable-sm capabilities-table"
            :selectAll="false"
            @row-click="onRowClick"
          >
            <Column selectionMode="multiple" headerStyle="width: 3rem"></Column>
            <Column field="capability.name" :header="t('isa62443.capabilities.name')" sortable>
              <template #body="{ data }">
                <div class="capability-name-cell">
                  <div class="capability-name">{{ data.capability.name }}</div>
                  <small class="capability-code" v-if="data.capability.code">{{ data.capability.code }}</small>
                </div>
              </template>
            </Column>
            <Column field="capability.category" :header="t('isa62443.capabilities.category')" sortable>
              <template #body="{ data }">
                <Tag v-if="data.capability.category" :value="data.capability.category" severity="info" />
                <span v-else class="text-600">-</span>
              </template>
            </Column>
            <Column field="support_level" :header="t('isa62443.capabilities.supportLevel')" sortable>
              <template #body="{ data }">
                <Tag 
                  :value="getSupportLevelLabel(data.support_level)" 
                  :severity="getSupportLevelSeverity(data.support_level)"
                />
              </template>
            </Column>
            <Column field="source" :header="t('isa62443.capabilities.source')" sortable>
              <template #body="{ data }">
                <Tag 
                  :value="getSourceLabel(data.source)" 
                  :severity="getSourceSeverity(data.source)"
                />
              </template>
            </Column>
            <Column field="inference_confidence" :header="t('isa62443.capabilities.inferenceConfidence')" sortable>
              <template #body="{ data }">
                <div v-if="data.source === 'inferred' && data.inference_confidence !== null && data.inference_confidence !== undefined">
                  <Tag 
                    :value="getConfidenceLabel(data.inference_confidence)" 
                    :severity="getConfidenceSeverity(data.inference_confidence)"
                  />
                  <span class="ml-2 text-sm text-600">
                    {{ Math.round(data.inference_confidence * 100) }}%
                  </span>
                </div>
                <span v-else class="text-600">-</span>
              </template>
            </Column>
            <Column field="notes" :header="t('isa62443.capabilities.notes')">
              <template #body="{ data }">
                <span v-if="data.notes" v-tooltip.top="data.notes.length > 50 ? data.notes : ''">
                  {{ data.notes.length > 50 ? data.notes.substring(0, 50) + '...' : data.notes }}
                </span>
                <span v-else class="text-600">-</span>
              </template>
            </Column>
            <Column field="evidence_ref" :header="t('isa62443.capabilities.evidenceRef')">
              <template #body="{ data }">
                <a v-if="data.evidence_ref" :href="data.evidence_ref" target="_blank" class="evidence-link">
                  {{ data.evidence_ref.length > 30 ? data.evidence_ref.substring(0, 30) + '...' : data.evidence_ref }}
                </a>
                <span v-else class="text-600">-</span>
              </template>
            </Column>
            <Column :header="t('common.strings.actions')" v-if="typeof canWrite === 'function' ? canWrite() : canWrite" headerStyle="width: 120px">
              <template #body="{ data }">
                <div class="flex gap-2" v-if="data.source === 'explicit'">
                  <Button 
                    icon="pi pi-pencil" 
                    class="p-button-text p-button-sm"
                    @click.stop="editCapability(data)"
                    :title="t('isa62443.capabilities.editCapability')"
                  />
                  <Button 
                    icon="pi pi-trash" 
                    class="p-button-text p-button-sm p-button-danger"
                    @click.stop="deleteCapability(data)"
                    :title="t('isa62443.capabilities.deleteCapability')"
                  />
                </div>
                <span v-else class="text-600">-</span>
              </template>
            </Column>
          </DataTable>
        </template>
      </Card>
    </div>

    <!-- Asset SR Assessment Dialog -->
    <Dialog
      v-model:visible="showAssessmentDialog"
      :header="t('isa62443.compliance.assessSr')"
      modal
      :style="{ width: '500px' }"
      @hide="resetAssessmentForm"
    >
      <div v-if="selectedSr" class="p-fluid">
        <p class="font-semibold mb-2">{{ selectedSr.requirement_id }} — {{ selectedSr.title }}</p>
        <div class="field">
          <label>{{ t('isa62443.compliance.status') }} *</label>
          <Dropdown
            v-model="assessmentForm.status"
            :options="assessmentStatusOptions"
            optionLabel="label"
            optionValue="value"
            class="w-full"
          />
        </div>
        <div class="field" v-if="assessmentForm.status && assessmentForm.status !== 'compliant'">
          <label>{{ t('isa62443.compliance.assessmentNotes') }} *</label>
          <Textarea v-model="assessmentForm.justification" :rows="4" class="w-full" />
        </div>
      </div>
      <template #footer>
        <Button :label="t('common.actions.cancel')" class="p-button-text" @click="showAssessmentDialog = false" />
        <Button :label="t('common.actions.save')" icon="pi pi-check" :loading="savingAssessment" @click="saveAssessment" />
      </template>
    </Dialog>

    <!-- Add/Edit Membership Dialog -->
    <Dialog 
      v-model:visible="showAddMembershipDialog" 
      :header="editingMembership ? t('isa62443.securityZones.editMembership') : t('isa62443.securityZones.addMembership')" 
      :modal="true"
      :style="{ width: '600px' }"
      @hide="resetMembershipForm"
    >
      <div class="p-fluid">
        <div class="field">
          <label for="membership-zone">{{ t('isa62443.securityZones.title') }} *</label>
          <Dropdown
            id="membership-zone"
            v-model="selectedZone"
            :options="availableZones"
            optionLabel="name"
            optionValue="id"
            :placeholder="t('isa62443.securityZones.selectZone')"
            :disabled="editingMembership !== null"
            class="w-full"
          />
        </div>

        <div class="field">
          <label for="membership-role">{{ t('isa62443.securityZones.role') }} *</label>
          <InputText
            id="membership-role"
            v-model="membershipRole"
            :placeholder="t('isa62443.securityZones.rolePlaceholder')"
            class="w-full"
          />
          <small class="p-text-secondary">{{ t('isa62443.securityZones.roleHelp') }}</small>
        </div>

        <div class="field">
          <label for="membership-interface-scope">{{ t('isa62443.securityZones.interfaceScope') }}</label>
          <InputText
            id="membership-interface-scope"
            v-model="membershipInterfaceScope"
            :placeholder="t('isa62443.securityZones.interfaceScopePlaceholder')"
            class="w-full"
          />
        </div>

        <div class="field">
          <label for="membership-sl-target">{{ t('isa62443.securityZones.slTarget') }}</label>
          <InputNumber
            id="membership-sl-target"
            v-model="membershipSlTarget"
            :min="1"
            :max="4"
            :placeholder="t('isa62443.securityZones.slTargetPlaceholder')"
            class="w-full"
          />
        </div>
      </div>

      <template #footer>
        <Button 
          :label="t('common.actions.cancel')" 
          icon="pi pi-times" 
          @click="showAddMembershipDialog = false; resetMembershipForm()"
          class="p-button-text"
        />
        <Button 
          :label="editingMembership ? t('common.actions.update') : t('common.actions.add')" 
          icon="pi pi-check" 
          @click="saveMembership"
        />
      </template>
    </Dialog>

    <!-- Add/Edit Capability Dialog -->
    <Dialog 
      v-model:visible="showAddCapabilityDialog" 
      :header="editingCapability ? t('isa62443.capabilities.editCapability') : t('isa62443.capabilities.addCapability')" 
      :modal="true"
      :style="{ width: '600px' }"
      @hide="resetCapabilityForm"
    >
      <div class="p-fluid">
        <div class="field">
          <label for="capability-select">{{ t('isa62443.capabilities.selectCapability') }} *</label>
          <Dropdown
            id="capability-select"
            v-model="capabilityForm.capability_id"
            :options="availableCapabilitiesForAdd"
            optionLabel="name"
            optionValue="id"
            :placeholder="t('isa62443.capabilities.selectCapability')"
            :disabled="editingCapability !== null"
            class="w-full"
          />
          <small v-if="!editingCapability" class="p-text-secondary">
            {{ t('isa62443.capabilities.description') }}
          </small>
        </div>

        <div class="field">
          <label for="support-level">{{ t('isa62443.capabilities.selectSupportLevel') }} *</label>
          <SelectButton
            id="support-level"
            v-model="capabilityForm.support_level"
            :options="supportLevelOptions"
            optionLabel="label"
            optionValue="value"
          />
        </div>

        <div class="field">
          <label for="capability-notes">{{ t('isa62443.capabilities.notes') }}</label>
          <Textarea
            id="capability-notes"
            v-model="capabilityForm.notes"
            :placeholder="t('isa62443.capabilities.notesPlaceholder')"
            :rows="4"
            class="w-full"
          />
        </div>

        <div class="field">
          <label for="evidence-ref">{{ t('isa62443.capabilities.evidenceRef') }}</label>
          <InputText
            id="evidence-ref"
            v-model="capabilityForm.evidence_ref"
            :placeholder="t('isa62443.capabilities.evidenceRefPlaceholder')"
            class="w-full"
          />
        </div>
      </div>

      <template #footer>
        <Button 
          :label="t('common.actions.cancel')" 
          icon="pi pi-times" 
          @click="showAddCapabilityDialog = false; resetCapabilityForm()"
          class="p-button-text"
        />
        <Button 
          :label="editingCapability ? t('common.actions.update') : t('common.actions.add')" 
          icon="pi pi-check" 
          @click="saveCapability"
          :loading="savingCapability"
        />
      </template>
    </Dialog>

    <!-- Bulk Update Dialog -->
    <Dialog 
      v-model:visible="showBulkUpdateDialog" 
      :header="t('isa62443.capabilities.bulkUpdateTitle')" 
      :modal="true"
      :style="{ width: '600px' }"
      @hide="resetBulkUpdateForm"
    >
      <div class="p-fluid">
        <div class="mb-3">
          <label class="font-semibold">{{ t('isa62443.capabilities.selectedCapabilities') }}: {{ selectedCapabilities.length }}</label>
          <ul class="mt-2 pl-4">
            <li v-for="cap in selectedCapabilities" :key="cap.capability_id" class="mb-1">
              {{ cap.capability.name }} ({{ cap.capability.code }})
            </li>
          </ul>
        </div>

        <div class="field">
          <label for="bulk-support-level">{{ t('isa62443.capabilities.bulkSupportLevel') }} *</label>
          <SelectButton
            id="bulk-support-level"
            v-model="bulkUpdateForm.support_level"
            :options="supportLevelOptions"
            optionLabel="label"
            optionValue="value"
          />
        </div>

        <div class="field">
          <label for="bulk-notes">{{ t('isa62443.capabilities.bulkNotes') }}</label>
          <Textarea
            id="bulk-notes"
            v-model="bulkUpdateForm.notes"
            :placeholder="t('isa62443.capabilities.notesPlaceholder')"
            :rows="3"
            class="w-full"
          />
        </div>

        <div class="field-checkbox">
          <Checkbox 
            v-model="bulkUpdateForm.replaceNotes" 
            :binary="true"
            inputId="replace-notes"
          />
          <label for="replace-notes" class="ml-2">{{ t('isa62443.capabilities.replaceNotes') }}</label>
          <small class="text-color-secondary block mt-1">{{ t('isa62443.capabilities.appendNotes') }}</small>
        </div>
      </div>

      <template #footer>
        <Button 
          :label="t('common.actions.cancel')" 
          icon="pi pi-times" 
          @click="showBulkUpdateDialog = false; resetBulkUpdateForm()"
          class="p-button-text"
        />
        <Button 
          :label="t('common.actions.save')" 
          icon="pi pi-check" 
          @click="saveBulkUpdate"
          :loading="savingBulkUpdate"
        />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import Card from 'primevue/card'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import ProgressSpinner from 'primevue/progressspinner'
import ProgressBar from 'primevue/progressbar'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import SelectButton from 'primevue/selectbutton'
import Checkbox from 'primevue/checkbox'
import api from '@/api/api'

const props = defineProps({
  assetId: { type: [String, Number], required: true },
  asset: { type: Object, required: true },
  canWrite: { type: [Function, Boolean], default: false }
})

const emit = defineEmits(['updated'])

const { t } = useI18n()
const router = useRouter()
const toast = useToast()

const loading = ref(false)
const memberships = ref([])
const complianceRecords = ref([])
const complianceLoading = ref(false)
const availableZones = ref([])

// Capabilities
const capabilities = ref([])
const capabilitiesLoading = ref(false)
const selectedCapabilities = ref([])
const showAddCapabilityDialog = ref(false)
const showBulkUpdateDialog = ref(false)
const editingCapability = ref(null)
const savingCapability = ref(false)
const savingBulkUpdate = ref(false)

const capabilityForm = ref({
  capability_id: null,
  support_level: 'unknown',
  notes: '',
  evidence_ref: ''
})

const bulkUpdateForm = ref({
  support_level: 'unknown',
  notes: '',
  replaceNotes: false
})

const capabilityFilters = ref({
  supportLevel: null,
  category: null,
  source: null
})

// Membership dialog
const showAddMembershipDialog = ref(false)
const selectedZone = ref(null)
const membershipRole = ref('')
const membershipInterfaceScope = ref('')
const membershipSlTarget = ref(null)
const editingMembership = ref(null)

const showAssessmentDialog = ref(false)
const selectedSr = ref(null)
const savingAssessment = ref(false)
const assessmentForm = ref({ status: 'insufficient_info', justification: '' })

const assessmentStatusOptions = computed(() => [
  { label: t('isa62443.compliance.compliant'), value: 'compliant' },
  { label: t('isa62443.compliance.nonCompliant'), value: 'non_compliant' },
  { label: t('isa62443.compliance.partial'), value: 'partial' },
  { label: t('isa62443.compliance.notApplicable'), value: 'not_applicable' },
  { label: t('isa62443.compliance.insufficientInfo'), value: 'insufficient_info' }
])

const gap = computed(() => {
  if (!props.asset.security_level_target || !props.asset.security_level_achieved) {
    return null
  }
  return props.asset.security_level_target - props.asset.security_level_achieved
})

// Capability options
const supportLevelOptions = [
  { label: t('isa62443.capabilities.supportLevels.supported'), value: 'supported' },
  { label: t('isa62443.capabilities.supportLevels.not_supported'), value: 'not_supported' },
  { label: t('isa62443.capabilities.supportLevels.unknown'), value: 'unknown' }
]

const sourceOptions = [
  { label: t('isa62443.capabilities.sources.explicit'), value: 'explicit' },
  { label: t('isa62443.capabilities.sources.inferred'), value: 'inferred' },
  { label: t('isa62443.capabilities.sources.available'), value: 'available' }
]

const categoryOptions = computed(() => {
  const categories = [...new Set(capabilities.value.map(c => c.capability?.category).filter(Boolean))]
  return [
    { label: t('isa62443.capabilities.allCategories'), value: null },
    ...categories.map(cat => ({ label: cat, value: cat }))
  ]
})

const filteredCapabilities = computed(() => {
  let filtered = capabilities.value

  if (capabilityFilters.value.supportLevel) {
    filtered = filtered.filter(c => c.support_level === capabilityFilters.value.supportLevel)
  }

  if (capabilityFilters.value.category) {
    filtered = filtered.filter(c => c.capability?.category === capabilityFilters.value.category)
  }

  if (capabilityFilters.value.source) {
    filtered = filtered.filter(c => c.source === capabilityFilters.value.source)
  }

  return filtered
})

const availableCapabilitiesForAdd = computed(() => {
  // Only show capabilities that are not already explicit
  const explicitIds = capabilities.value
    .filter(c => c.source === 'explicit')
    .map(c => c.capability_id)
  
  return capabilities.value
    .filter(c => !explicitIds.includes(c.capability_id))
    .map(c => ({
      id: c.capability_id,
      name: `${c.capability.name} (${c.capability.code})`,
      code: c.capability.code
    }))
})

async function fetchMemberships() {
  if (!props.assetId) {
    memberships.value = []
    return
  }
  try {
    const res = await api.getAssetZoneMemberships(props.assetId)
    memberships.value = res.data || []
  } catch (error) {
    console.error('Error fetching zone memberships:', error)
    memberships.value = []
  }
}

async function fetchCompliance() {
  if (!props.assetId) {
    complianceRecords.value = []
    return
  }
  complianceLoading.value = true
  try {
    const res = await api.getAssetSecurityRequirements(props.assetId)
    complianceRecords.value = res.data || []
  } catch (error) {
    console.error('Error fetching asset security requirements:', error)
    complianceRecords.value = []
  } finally {
    complianceLoading.value = false
  }
}

function openAssessmentDialog(sr) {
  selectedSr.value = sr
  assessmentForm.value = {
    status: sr.status || 'insufficient_info',
    justification: sr.justification || ''
  }
  showAssessmentDialog.value = true
}

function resetAssessmentForm() {
  selectedSr.value = null
  assessmentForm.value = { status: 'insufficient_info', justification: '' }
}

async function saveAssessment() {
  if (!selectedSr.value) return
  const { status, justification } = assessmentForm.value
  if (status !== 'compliant' && !justification?.trim()) {
    toast.add({
      severity: 'warn',
      summary: t('common.messages.warning'),
      detail: t('isa62443.compliance.justificationRequired'),
      life: 3000
    })
    return
  }
  savingAssessment.value = true
  try {
    const res = await api.createOrUpdateAssetSRAssessment(props.assetId, selectedSr.value.sr_id, {
      status,
      justification: justification || null,
      evidence: []
    })
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: t('isa62443.compliance.assessmentSaved'),
      life: 3000
    })
    showAssessmentDialog.value = false
    await fetchCompliance()
    if (res.data?.asset_updated) {
      emit('updated', {
        security_level_achieved: res.data.asset_updated.security_level_achieved,
        isa62443_compliance_status: res.data.asset_updated.isa62443_compliance_status
      })
    } else {
      const recalc = await api.recalculateAssetIec62443(props.assetId)
      if (recalc.data) emit('updated', recalc.data)
    }
  } catch (error) {
    console.error('Error saving assessment:', error)
    toast.add({ severity: 'error', summary: t('common.messages.error'), detail: t('isa62443.compliance.errorSaving') })
  } finally {
    savingAssessment.value = false
  }
}

async function loadAvailableZones() {
  if (!props.assetId) {
    availableZones.value = []
    return
  }
  try {
    const res = await api.getSecurityZones()
    availableZones.value = res.data || []
  } catch (error) {
    console.error('Error loading zones:', error)
    availableZones.value = []
  }
}

function goToZone(zoneId) {
  router.push(`/security-zones/${zoneId}`)
}

function getComplianceStatusLabel(status) {
  if (!status) return '-'
  const statusMap = {
    'compliant': t('isa62443.compliance.compliant'),
    'non_compliant': t('isa62443.compliance.nonCompliant'),
    'partial': t('isa62443.compliance.partial'),
    'not_assessed': t('isa62443.compliance.notAssessed'),
    'not_applicable': t('isa62443.compliance.notApplicable'),
    'insufficient_info': t('isa62443.compliance.insufficientInfo')
  }
  return statusMap[status] || status
}

function getComplianceSeverity(status) {
  if (!status) return 'info'
  const severityMap = {
    'compliant': 'success',
    'non_compliant': 'danger',
    'partial': 'warning',
    'not_assessed': 'info',
    'not_applicable': 'secondary',
    'insufficient_info': 'warning'
  }
  return severityMap[status] || 'info'
}

function getSLAchievedSeverity(slAchieved, slTarget) {
  if (!slTarget) return 'info'
  const gap = slTarget - slAchieved
  if (gap === 0) return 'success'
  if (gap === 1) return 'warning'
  return 'danger'
}

function getGapSeverity(gap) {
  if (gap === 0) return 'success'
  if (gap === 1) return 'warning'
  return 'danger'
}

function formatDate(date) {
  if (!date) return '-'
  return new Date(date).toLocaleDateString()
}

function editMembership(membership) {
  editingMembership.value = membership
  selectedZone.value = membership.security_zone_id
  membershipRole.value = membership.role
  membershipInterfaceScope.value = membership.interface_scope || ''
  membershipSlTarget.value = membership.sl_target || null
  showAddMembershipDialog.value = true
}

function resetMembershipForm() {
  editingMembership.value = null
  selectedZone.value = null
  membershipRole.value = ''
  membershipInterfaceScope.value = ''
  membershipSlTarget.value = null
}

async function saveMembership() {
  if (!selectedZone.value || !membershipRole.value) {
    toast.add({
      severity: 'warn',
      summary: t('common.messages.warning'),
      detail: t('isa62443.securityZones.membershipRequiredFields'),
      life: 3000
    })
    return
  }

  try {
    const membershipData = {
      asset_id: props.assetId,
      role: membershipRole.value,
      interface_scope: membershipInterfaceScope.value || null,
      sl_target: membershipSlTarget.value || null
    }

    if (editingMembership.value) {
      await api.updateZoneMembership(editingMembership.value.security_zone_id, editingMembership.value.id, membershipData)
      toast.add({
        severity: 'success',
        summary: t('common.messages.success'),
        detail: t('isa62443.securityZones.membershipUpdated'),
        life: 3000
      })
    } else {
      await api.createZoneMembership(selectedZone.value, membershipData)
      toast.add({
        severity: 'success',
        summary: t('common.messages.success'),
        detail: t('isa62443.securityZones.membershipAdded'),
        life: 3000
      })
    }

    showAddMembershipDialog.value = false
    resetMembershipForm()
    await fetchMemberships()
    emit('updated')
  } catch (error) {
    console.error('Error saving membership:', error)
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: error.response?.data?.detail || t('isa62443.securityZones.errorSavingMembership'),
      life: 3000
    })
  }
}

async function removeMembership(membership) {
  if (!confirm(t('isa62443.securityZones.confirmRemoveMembership'))) {
    return
  }

  try {
    await api.deleteZoneMembership(membership.security_zone_id, membership.id)
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: t('isa62443.securityZones.membershipRemoved'),
      life: 3000
    })
    await fetchMemberships()
    emit('updated')
  } catch (error) {
    console.error('Error removing membership:', error)
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: t('isa62443.securityZones.errorRemovingMembership'),
      life: 3000
    })
  }
}

// Capability functions
async function fetchCapabilities() {
  if (!props.assetId) {
    capabilities.value = []
    return
  }
  capabilitiesLoading.value = true
  try {
    const res = await api.getAssetCapabilities(props.assetId)
    capabilities.value = res.data || []
  } catch (error) {
    console.error('Error fetching capabilities:', error)
    toast.add({ 
      severity: 'error', 
      summary: t('common.messages.error'), 
      detail: t('isa62443.capabilities.errorLoading') 
    })
    capabilities.value = []
  } finally {
    capabilitiesLoading.value = false
  }
}

function getSupportLevelLabel(level) {
  const labels = {
    'supported': t('isa62443.capabilities.supportLevels.supported'),
    'not_supported': t('isa62443.capabilities.supportLevels.not_supported'),
    'unknown': t('isa62443.capabilities.supportLevels.unknown'),
    'available': t('isa62443.capabilities.supportLevels.available')
  }
  return labels[level] || level
}

function getSupportLevelSeverity(level) {
  const severityMap = {
    'supported': 'success',
    'not_supported': 'danger',
    'unknown': 'warning',
    'available': 'info'
  }
  return severityMap[level] || 'info'
}

function getSourceLabel(source) {
  const labels = {
    'explicit': t('isa62443.capabilities.sources.explicit'),
    'inferred': t('isa62443.capabilities.sources.inferred'),
    'available': t('isa62443.capabilities.sources.available')
  }
  return labels[source] || source
}

function getSourceSeverity(source) {
  const severityMap = {
    'explicit': 'success',
    'inferred': 'info',
    'available': 'secondary'
  }
  return severityMap[source] || 'info'
}

function getConfidenceLabel(confidence) {
  if (confidence >= 0.7) {
    return t('isa62443.capabilities.confidenceHigh')
  } else if (confidence >= 0.4) {
    return t('isa62443.capabilities.confidenceMedium')
  } else {
    return t('isa62443.capabilities.confidenceLow')
  }
}

function getConfidenceSeverity(confidence) {
  if (confidence >= 0.7) {
    return 'success'
  } else if (confidence >= 0.4) {
    return 'warning'
  } else {
    return 'danger'
  }
}

function onRowClick(event) {
  // Ignora il click se è sulla checkbox, sui pulsanti di azione o sui link
  const target = event.originalEvent?.target
  if (!target) return
  
  if (target.closest('.p-checkbox') || 
      target.closest('button') ||
      target.closest('a')) {
    return
  }
  
  // Apri il dialog di modifica solo per capability esplicite e se l'utente può scrivere
  const capability = event.data
  if (capability && capability.source === 'explicit' && (typeof props.canWrite === 'function' ? props.canWrite() : props.canWrite)) {
    editCapability(capability)
  }
}

function editCapability(capability) {
  editingCapability.value = capability
  capabilityForm.value = {
    capability_id: capability.capability_id,
    support_level: capability.support_level,
    notes: capability.notes || '',
    evidence_ref: capability.evidence_ref || ''
  }
  showAddCapabilityDialog.value = true
}

function resetCapabilityForm() {
  editingCapability.value = null
  capabilityForm.value = {
    capability_id: null,
    support_level: 'unknown',
    notes: '',
    evidence_ref: ''
  }
}

async function saveCapability() {
  if (!capabilityForm.value.capability_id || !capabilityForm.value.support_level) {
    toast.add({
      severity: 'warn',
      summary: t('common.messages.warning'),
      detail: t('isa62443.capabilities.selectCapability') + ' e ' + t('isa62443.capabilities.selectSupportLevel') + ' sono obbligatori',
      life: 3000
    })
    return
  }

  savingCapability.value = true
  try {
    if (editingCapability.value) {
      // Update existing
      await api.updateAssetCapability(
        props.assetId,
        editingCapability.value.id,
        {
          support_level: capabilityForm.value.support_level,
          notes: capabilityForm.value.notes || null,
          evidence_ref: capabilityForm.value.evidence_ref || null
        }
      )
      toast.add({
        severity: 'success',
        summary: t('common.messages.success'),
        detail: t('isa62443.capabilities.capabilityUpdated'),
        life: 3000
      })
    } else {
      // Create new
      await api.createAssetCapability(props.assetId, {
        capability_id: capabilityForm.value.capability_id,
        support_level: capabilityForm.value.support_level,
        notes: capabilityForm.value.notes || null,
        evidence_ref: capabilityForm.value.evidence_ref || null
      })
      toast.add({
        severity: 'success',
        summary: t('common.messages.success'),
        detail: t('isa62443.capabilities.capabilityAdded'),
        life: 3000
      })
    }

    showAddCapabilityDialog.value = false
    resetCapabilityForm()
    await fetchCapabilities()
    emit('updated')
  } catch (error) {
    console.error('Error saving capability:', error)
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: error.response?.data?.detail || t('isa62443.capabilities.errorSaving'),
      life: 3000
    })
  } finally {
    savingCapability.value = false
  }
}

async function deleteCapability(capability) {
  if (!confirm(t('isa62443.capabilities.confirmDelete'))) {
    return
  }

  try {
    await api.deleteAssetCapability(props.assetId, capability.id)
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: t('isa62443.capabilities.capabilityDeleted'),
      life: 3000
    })
    await fetchCapabilities()
    emit('updated')
  } catch (error) {
    console.error('Error deleting capability:', error)
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: t('isa62443.capabilities.errorDeleting'),
      life: 3000
    })
  }
}

function resetBulkUpdateForm() {
  bulkUpdateForm.value = {
    support_level: 'unknown',
    notes: '',
    replaceNotes: false
  }
}

async function saveBulkUpdate() {
  if (selectedCapabilities.value.length === 0) {
    toast.add({
      severity: 'warn',
      summary: t('common.messages.warning'),
      detail: t('isa62443.capabilities.selectAtLeastOne'),
      life: 3000
    })
    return
  }

  if (!bulkUpdateForm.value.support_level) {
    toast.add({
      severity: 'warn',
      summary: t('common.messages.warning'),
      detail: t('isa62443.capabilities.selectSupportLevel') + ' è obbligatorio',
      life: 3000
    })
    return
  }

  savingBulkUpdate.value = true
  try {
    const bulkData = {
      capabilities: selectedCapabilities.value.map(cap => {
        const item = {
          capability_id: cap.capability_id,
          support_level: bulkUpdateForm.value.support_level
        }

        if (bulkUpdateForm.value.notes) {
          if (bulkUpdateForm.value.replaceNotes || !cap.notes) {
            item.notes = bulkUpdateForm.value.notes
          } else {
            item.notes = cap.notes + '\n' + bulkUpdateForm.value.notes
          }
        } else if (!bulkUpdateForm.value.replaceNotes) {
          item.notes = cap.notes || null
        }

        if (cap.evidence_ref) {
          item.evidence_ref = cap.evidence_ref
        }

        return item
      })
    }

    await api.bulkUpdateAssetCapabilities(props.assetId, bulkData)
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: t('isa62443.capabilities.bulkUpdateSuccess', { count: selectedCapabilities.value.length }),
      life: 3000
    })

    showBulkUpdateDialog.value = false
    resetBulkUpdateForm()
    selectedCapabilities.value = []
    await fetchCapabilities()
    emit('updated')
  } catch (error) {
    console.error('Error in bulk update:', error)
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: error.response?.data?.detail || t('isa62443.capabilities.errorBulkUpdate'),
      life: 3000
    })
  } finally {
    savingBulkUpdate.value = false
  }
}

onMounted(async () => {
  loading.value = true
  // fetchCompliance() rimosso - la compliance è gestita a livello di zone
  await Promise.all([
    fetchMemberships(),
    loadAvailableZones(),
    fetchCapabilities()
  ])
  loading.value = false
})
</script>

<style scoped>
.asset-iec62443-tab {
  max-width: 1200px;
}

.zone-link {
  color: var(--primary-color);
  cursor: pointer;
  text-decoration: none;
  font-weight: 500;
}

.zone-link:hover {
  text-decoration: underline;
}

.evidence-link {
  color: var(--primary-color);
  text-decoration: none;
}

.evidence-link:hover {
  text-decoration: underline;
}

/* Stili per la tabella delle capabilities */
.capabilities-table :deep(.p-datatable-tbody > tr) {
  cursor: pointer;
  transition: background-color 0.2s;
}

.capabilities-table :deep(.p-datatable-tbody > tr:hover) {
  background-color: var(--surface-hover);
}

.capabilities-table :deep(.p-datatable-tbody > tr.p-highlight) {
  background-color: var(--primary-color);
  color: var(--primary-color-text);
}

.capability-name-cell {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.capability-name {
  font-weight: 500;
  color: var(--text-color);
}

.capability-code {
  color: var(--text-color-secondary);
  font-size: 0.875rem;
  font-family: monospace;
}
</style>

