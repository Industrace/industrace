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
              v-if="canWrite"
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
            <Column :header="t('common.actions.actions')" v-if="canWrite">
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

      <!-- Security Requirements Compliance -->
      <Card class="mb-4">
        <template #title>
          <div class="flex align-items-center">
            <i class="pi pi-check-circle mr-2"></i>
            {{ t('isa62443.compliance.requirements') }}
          </div>
        </template>
        <template #content>
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
            <Column field="requirement_title" :header="t('isa62443.compliance.requirementId')" sortable>
              <template #body="{ data }">
                <div>
                  <div class="font-semibold">{{ data.requirement_title || data.requirement_id }}</div>
                  <small class="text-600" v-if="data.requirement_id">{{ data.requirement_id }}</small>
                </div>
              </template>
            </Column>
            <Column field="compliance_status" :header="t('isa62443.compliance.status')" sortable>
              <template #body="{ data }">
                <Tag 
                  :value="getComplianceStatusLabel(data.compliance_status)" 
                  :severity="getComplianceSeverity(data.compliance_status)"
                />
              </template>
            </Column>
            <Column field="compliance_percentage" :header="t('isa62443.compliance.compliancePercentage')" sortable>
              <template #body="{ data }">
                <div v-if="data.compliance_percentage !== null && data.compliance_percentage !== undefined">
                  <ProgressBar :value="data.compliance_percentage" />
                  <span class="ml-2">{{ data.compliance_percentage }}%</span>
                </div>
                <span v-else class="text-600">-</span>
              </template>
            </Column>
            <Column field="assessment_date" :header="t('isa62443.compliance.lastAssessment')" sortable>
              <template #body="{ data }">
                {{ formatDate(data.assessment_date) }}
              </template>
            </Column>
          </DataTable>
        </template>
      </Card>
    </div>

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
import api from '@/api/api'

const props = defineProps({
  assetId: { type: [String, Number], required: true },
  asset: { type: Object, required: true },
  canWrite: { type: Function, default: () => false }
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

// Membership dialog
const showAddMembershipDialog = ref(false)
const selectedZone = ref(null)
const membershipRole = ref('')
const membershipInterfaceScope = ref('')
const membershipSlTarget = ref(null)
const editingMembership = ref(null)

const gap = computed(() => {
  if (!props.asset.security_level_target || !props.asset.security_level_achieved) {
    return null
  }
  return props.asset.security_level_target - props.asset.security_level_achieved
})

async function fetchMemberships() {
  try {
    const res = await api.getAssetZoneMemberships(props.assetId)
    memberships.value = res.data || []
  } catch (error) {
    console.error('Error fetching zone memberships:', error)
    memberships.value = []
  }
}

async function fetchCompliance() {
  complianceLoading.value = true
  try {
    const res = await api.getAssetCompliance(props.assetId)
    complianceRecords.value = res.data || []
  } catch (error) {
    console.error('Error fetching compliance:', error)
    complianceRecords.value = []
  } finally {
    complianceLoading.value = false
  }
}

async function loadAvailableZones() {
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
    'not_applicable': t('isa62443.compliance.notApplicable')
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
    'not_applicable': 'secondary'
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

onMounted(async () => {
  loading.value = true
  await Promise.all([
    fetchMemberships(),
    fetchCompliance(),
    loadAvailableZones()
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
</style>

