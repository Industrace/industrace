<template>
  <div class="security-zone-detail" v-if="zone">
    <div class="page-header">
      <h1>{{ zone.name }}</h1>
      <Button 
        :label="t('common.actions.back')" 
        icon="pi pi-arrow-left" 
        @click="$router.push('/security-zones')"
      />
    </div>

    <Card class="mb-4">
      <template #title>{{ t('isa62443.securityZones.details') }}</template>
      <template #content>
        <div class="zone-status-row mb-3">
          <Tag
            v-if="zone.compliance_status"
            :value="getComplianceStatusLabel(zone.compliance_status)"
            :severity="getComplianceSeverity(zone.compliance_status)"
          />
          <Tag
            :value="`SL-T: ${zone.security_level_target ?? '-'}`"
            severity="info"
          />
          <Tag
            :value="`SL-A: ${zone.security_level_achieved ?? '-'}`"
            :severity="getSLASeverity(zone.security_level_achieved, zone.security_level_target)"
          />
          <Tag
            v-if="zone.security_level_capability != null"
            :value="`SL-C: ${zone.security_level_capability}`"
            severity="secondary"
          />
          <Tag
            v-if="zone.security_level_target != null && zone.security_level_achieved != null"
            :value="`${t('isa62443.compliance.gap')}: ${Math.max(0, zone.security_level_target - zone.security_level_achieved)}`"
            :severity="getGapSeverity(zone.security_level_target, zone.security_level_achieved)"
          />
        </div>
        <div class="zone-details-grid">
          <div><strong>{{ t('common.fields.description') }}:</strong> {{ zone.description || '-' }}</div>
          <div><strong>{{ t('isa62443.securityZones.zoneType') }}:</strong> {{ zone.zone_type || '-' }}</div>
          <div><strong>{{ t('isa62443.securityZones.securityLevel') }}:</strong> SL-T {{ zone.security_level_target || '-' }}</div>
          <div><strong>{{ t('isa62443.compliance.slAchieved') }}:</strong> SL-A {{ zone.security_level_achieved ?? '-' }}</div>
          <div><strong>{{ t('isa62443.compliance.securityLevelCapability') }}:</strong> SL-C {{ zone.security_level_capability ?? '-' }}</div>
          <div><strong>{{ t('isa62443.securityZones.assets') }}:</strong> {{ zone.asset_count || 0 }}</div>
          <div><strong>{{ t('isa62443.securityZones.conduits') }}:</strong> {{ zone.conduit_count || 0 }}</div>
        </div>
        <div class="mt-3 flex justify-content-end">
          <Button 
            :label="t('isa62443.compliance.reviewSecurityRequirements')"
            icon="pi pi-shield"
            @click="goToComplianceTab"
            class="p-button-primary"
          />
        </div>
      </template>
    </Card>

    <TabView v-model:activeIndex="activeTabIndex" class="mt-4">
      <!-- Assets Tab -->
      <TabPanel>
        <template #header>
          <span style="display: flex; align-items: center; gap: 0.4em;">
            <i class="pi pi-server"></i> {{ t('isa62443.securityZones.assets') }} ({{ assets.length }})
          </span>
        </template>

        <div class="mb-3 flex justify-content-end">
          <Button 
            v-if="canWrite('security_zones')"
            :label="t('isa62443.securityZones.addAsset')" 
            icon="pi pi-plus" 
            @click="showAddAssetDialog = true"
            class="p-button-sm"
          />
        </div>

        <div v-if="assetsLoading" class="text-center p-4">
          <ProgressSpinner />
        </div>

        <div v-else-if="assets.length === 0" class="text-center p-4">
          <p>{{ t('isa62443.securityZones.noAssetsInZone') }}</p>
        </div>

        <DataTable 
          v-else
          :value="assets" 
          :loading="assetsLoading"
          :paginator="true"
          :rows="20"
          :sortField="sortField"
          :sortOrder="sortOrder"
          @sort="onSort"
          class="p-datatable-sm"
        >
          <Column field="name" :header="t('common.fields.name')" sortable>
            <template #body="{ data }">
              <a 
                @click="goToAsset(data.id)" 
                class="asset-link"
              >
                {{ data.name }}
              </a>
            </template>
          </Column>
          <Column field="asset_type" :header="t('assets.fields.assetType')" sortable />
          <Column field="role_in_zone" :header="t('isa62443.securityZones.role')" sortable>
            <template #body="{ data }">
              <Tag v-if="data.role_in_zone" :value="getParticipationTypeLabelForDisplay(data.role_in_zone)" severity="info" />
              <span v-else class="text-600">-</span>
            </template>
          </Column>
          <Column :header="t('isa62443.securityZones.otherZones')" sortable>
            <template #body="{ data }">
              <div v-if="data.other_zones && data.other_zones.length > 0" class="flex flex-wrap gap-1">
                <Tag 
                  v-for="otherZone in data.other_zones" 
                  :key="otherZone.zone_id"
                  :value="`${otherZone.zone_name || otherZone.zone_id} (${getParticipationTypeLabelForDisplay(otherZone.role)})`"
                  severity="secondary"
                  :title="`${t('isa62443.securityZones.role')}: ${getParticipationTypeLabelForDisplay(otherZone.role)}${otherZone.interface_scope ? `, ${t('isa62443.securityZones.interfaceScope')}: ${otherZone.interface_scope}` : ''}`"
                />
              </div>
              <span v-else class="text-600">-</span>
            </template>
          </Column>
          <Column field="risk_score" :header="t('assets.riskBreakdown.baseRiskScore')" sortable>
            <template #body="{ data }">
              <Tag 
                v-if="data.risk_score !== null && data.risk_score !== undefined"
                :value="data.risk_score.toFixed(2)" 
                :severity="getRiskSeverity(data.risk_score)"
              />
              <span v-else>-</span>
            </template>
          </Column>
          <Column :header="t('common.actions.actions')">
            <template #body="{ data }">
              <div class="flex gap-2">
                <Button 
                  icon="pi pi-eye" 
                  class="p-button-text p-button-sm"
                  @click="goToAsset(data.id)"
                  :title="t('common.actions.view')"
                />
                <Button 
                  v-if="canWrite('security_zones')"
                  icon="pi pi-times" 
                  class="p-button-text p-button-sm p-button-danger"
                  @click="removeAssetFromZone(data.id)"
                  :title="t('isa62443.securityZones.removeAsset')"
                />
              </div>
            </template>
          </Column>
        </DataTable>
      </TabPanel>

      <!-- Conduits Tab -->
      <TabPanel>
        <template #header>
          <span style="display: flex; align-items: center; gap: 0.4em;">
            <i class="pi pi-sitemap"></i> {{ t('isa62443.securityZones.conduits') }} ({{ conduits.length }})
          </span>
        </template>

        <div class="mb-3 flex justify-content-end">
          <Button 
            v-if="canWrite('compliance')"
            :label="t('isa62443.securityZones.addConduit')" 
            icon="pi pi-plus" 
            @click="showAddConduitDialog = true"
            class="p-button-sm"
          />
        </div>

        <div v-if="conduitsLoading" class="text-center p-4">
          <ProgressSpinner />
        </div>

        <div v-else-if="conduits.length === 0" class="text-center p-4">
          <p>{{ t('isa62443.securityZones.noConduitsInZone') }}</p>
        </div>

        <DataTable 
          v-else
          :value="conduits" 
          :loading="conduitsLoading"
          :paginator="true"
          :rows="20"
          :sortField="conduitsSortField"
          :sortOrder="conduitsSortOrder"
          @sort="onConduitsSort"
          class="p-datatable-sm"
        >
          <Column field="name" :header="t('common.fields.name')" sortable>
            <template #body="{ data }">
              <a 
                @click="goToConduit(data.id)" 
                class="conduit-link"
              >
                {{ data.name }}
              </a>
            </template>
          </Column>
          <Column :header="t('isa62443.conduits.fromZone')" sortable sortField="from_zone_name">
            <template #body="{ data }">
              {{ data.from_zone_name || '-' }}
            </template>
          </Column>
          <Column :header="t('isa62443.conduits.toZone')" sortable sortField="to_zone_name">
            <template #body="{ data }">
              {{ data.to_zone_name || '-' }}
            </template>
          </Column>
          <Column field="conduit_type" :header="t('isa62443.conduits.conduitType')" sortable />
          <Column :header="t('isa62443.securityZones.securityLevel')" sortable sortField="security_level_target">
            <template #body="{ data }">
              <span v-if="data.security_level_target">SL-{{ data.security_level_target }}</span>
              <span v-else>-</span>
            </template>
          </Column>
          <Column :header="t('isa62443.compliance.status')" sortable sortField="compliance_status">
            <template #body="{ data }">
              <Tag 
                :value="getComplianceStatusLabel(data.compliance_status)" 
                :severity="getComplianceSeverity(data.compliance_status)"
              />
            </template>
          </Column>
          <Column :header="t('common.actions.view')">
            <template #body="{ data }">
              <Button 
                icon="pi pi-eye" 
                class="p-button-text p-button-sm"
                @click="goToConduit(data.id)"
                :title="t('common.actions.view')"
              />
            </template>
          </Column>
        </DataTable>
      </TabPanel>

      <!-- Compliance Tab -->
      <TabPanel>
        <template #header>
          <span style="display: flex; align-items: center; gap: 0.4em;">
            <i class="pi pi-shield"></i> {{ t('isa62443.compliance.title') }}
          </span>
        </template>
        <ZoneComplianceTab :zone="zone" @zone-updated="handleZoneUpdated" />
      </TabPanel>
    </TabView>

    <!-- Add Asset Dialog -->
    <Dialog 
      v-model:visible="showAddAssetDialog" 
      :header="t('isa62443.securityZones.addAsset')" 
      modal 
      :closable="true" 
      :dismissableMask="true"
      style="width: 800px"
    >
      <div class="mb-3">
        <InputText 
          v-model="assetSearchFilter"
          :placeholder="t('common.actions.search')"
          class="w-full"
        />
      </div>
      <div v-if="availableAssetsLoading" class="text-center p-4">
        <ProgressSpinner />
      </div>
      <DataTable 
        v-else
        :value="filteredAvailableAssets" 
        :paginator="true"
        :rows="10"
        v-model:selection="selectedAssets"
        selectionMode="multiple"
        dataKey="id"
        class="p-datatable-sm"
      >
        <Column selectionMode="multiple" headerStyle="width: 3rem" />
        <Column field="name" :header="t('common.fields.name')" sortable />
        <Column field="asset_type" :header="t('assets.fields.assetType')" sortable>
          <template #body="{ data }">
            {{ data.asset_type?.name || '-' }}
          </template>
        </Column>
        <Column :header="t('isa62443.securityZones.otherZones')" sortable>
          <template #body="{ data }">
            <div v-if="getAssetOtherZonesInDialog(data.id) && getAssetOtherZonesInDialog(data.id).length > 0" class="flex flex-wrap gap-1">
              <Tag 
                v-for="zone in getAssetOtherZonesInDialog(data.id)" 
                :key="zone.id"
                :value="`${zone.name} (${getParticipationTypeLabelForDisplay(zone.role)})`"
                severity="info"
              />
            </div>
            <span v-else>-</span>
          </template>
        </Column>
      </DataTable>
      
      <!-- Selected assets with individual participation types -->
      <div v-if="selectedAssets.length > 0" class="mt-4 p-3 border-round" style="background: var(--surface-ground);">
        <div class="flex justify-content-between align-items-center mb-3">
          <h4 class="mt-0 mb-0">{{ t('isa62443.securityZones.selectedAssets', { count: selectedAssets.length }) }}</h4>
          <div class="flex align-items-center gap-2">
            <label class="text-sm mr-2">{{ t('isa62443.securityZones.applyToAll') }}:</label>
            <Dropdown
              v-model="defaultParticipationType"
              :options="zoneParticipationTypes"
              optionLabel="label"
              optionValue="value"
              :placeholder="t('isa62443.securityZones.selectDefaultType')"
              class="w-12rem"
              @change="applyDefaultParticipationType"
            >
              <template #option="slotProps">
                <div class="flex flex-column">
                  <span class="font-semibold">{{ slotProps.option.label }}</span>
                  <small class="text-500">{{ slotProps.option.description }}</small>
                </div>
              </template>
            </Dropdown>
          </div>
        </div>
        <small class="p-text-secondary mb-3 d-block">{{ t('isa62443.securityZones.roleHelp') }}</small>
        
        <DataTable 
          :value="selectedAssetsWithDetails" 
          class="p-datatable-sm"
        >
          <Column field="name" :header="t('common.fields.name')" />
          <Column field="asset_type.name" :header="t('assets.fields.assetType')">
            <template #body="{ data }">
              {{ data.asset_type?.name || '-' }}
            </template>
          </Column>
          <Column :header="t('isa62443.securityZones.role') + ' *'">
            <template #body="{ data }">
              <Dropdown
                v-model="data.participationType"
                :options="zoneParticipationTypes"
                optionLabel="label"
                optionValue="value"
                :placeholder="t('isa62443.securityZones.rolePlaceholder')"
                class="w-full"
                @change="updateAssetParticipationType(data.id, data.participationType)"
              >
                <template #option="slotProps">
                  <div class="flex flex-column">
                    <span class="font-semibold">{{ slotProps.option.label }}</span>
                    <small class="text-500">{{ slotProps.option.description }}</small>
                  </div>
                </template>
              </Dropdown>
            </template>
          </Column>
          <Column :header="t('isa62443.securityZones.interfaceScope')">
            <template #body="{ data }">
              <InputText
                v-model="data.interfaceScope"
                :placeholder="t('isa62443.securityZones.interfaceScopePlaceholder')"
                class="w-full"
                @input="updateAssetInterfaceScope(data.id, data.interfaceScope)"
              />
            </template>
          </Column>
          <Column :header="t('isa62443.securityZones.slTarget')">
            <template #body="{ data }">
              <InputNumber
                v-model="data.slTarget"
                :min="1"
                :max="4"
                :placeholder="t('isa62443.securityZones.slTargetPlaceholder')"
                class="w-full"
                @input="updateAssetSlTarget(data.id, data.slTarget)"
              />
            </template>
          </Column>
          <Column :header="t('common.actions.actions')">
            <template #body="{ data }">
              <Button 
                icon="pi pi-times" 
                class="p-button-text p-button-sm p-button-danger"
                @click="removeSelectedAsset(data.id)"
                :title="t('common.actions.remove')"
              />
            </template>
          </Column>
        </DataTable>
      </div>
      
      <template #footer>
        <Button 
          :label="t('common.actions.cancel')" 
          icon="pi pi-times" 
          class="p-button-secondary" 
          @click="showAddAssetDialog = false; resetAddAssetForm()" 
        />
        <Button 
          :label="t('common.actions.add')" 
          icon="pi pi-check" 
          @click="addAssetsToZone"
          :disabled="selectedAssets.length === 0 || !allAssetsHaveParticipationType"
        />
      </template>
    </Dialog>

    <!-- Add Conduit Dialog -->
    <Dialog 
      v-model:visible="showAddConduitDialog" 
      :header="t('isa62443.securityZones.addConduit')" 
      modal 
      :closable="true" 
      :dismissableMask="true"
      style="width: 800px"
    >
      <ConduitForm 
        :zones="allZones"
        :defaultFromZone="zone?.id"
        @submit="handleConduitSubmit"
        @cancel="showAddConduitDialog = false"
      />
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { usePermissions } from '@/composables/usePermissions'
import Button from 'primevue/button'
import Card from 'primevue/card'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import ProgressSpinner from 'primevue/progressspinner'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import InputNumber from 'primevue/inputnumber'
import ConduitForm from '@/components/features/isa62443/ConduitForm.vue'
import ZoneComplianceTab from '@/components/features/isa62443/ZoneComplianceTab.vue'
import api from '@/api/api'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const toast = useToast()
const { canWrite, canDelete } = usePermissions()

const zone = ref(null)
const activeTabIndex = ref(0) // 0=Assets, 1=Conduits, 2=Compliance
const assets = ref([])
const assetsLoading = ref(false)
const sortField = ref('name')
const sortOrder = ref(1) // 1 = ascending, -1 = descending
const conduits = ref([])
const conduitsLoading = ref(false)
const conduitsSortField = ref('name')
const conduitsSortOrder = ref(1)

// Add Asset Dialog
const showAddAssetDialog = ref(false)
const availableAssets = ref([])
const availableAssetsLoading = ref(false)
const selectedAssets = ref([])
const assetSearchFilter = ref('')
const allZones = ref([])
const defaultParticipationType = ref(null)
// Store individual participation details for each selected asset
const selectedAssetsDetails = ref({}) // { assetId: { participationType, interfaceScope, slTarget } }

// Zone Participation Types
const zoneParticipationTypes = computed(() => [
  { value: 'primary', label: t('isa62443.securityZones.zoneParticipationTypes.primary'), description: t('isa62443.securityZones.zoneParticipationTypes.primaryDesc') },
  { value: 'supporting', label: t('isa62443.securityZones.zoneParticipationTypes.supporting'), description: t('isa62443.securityZones.zoneParticipationTypes.supportingDesc') },
  { value: 'boundary', label: t('isa62443.securityZones.zoneParticipationTypes.boundary'), description: t('isa62443.securityZones.zoneParticipationTypes.boundaryDesc') },
  { value: 'shared', label: t('isa62443.securityZones.zoneParticipationTypes.shared'), description: t('isa62443.securityZones.zoneParticipationTypes.sharedDesc') },
  { value: 'monitoring', label: t('isa62443.securityZones.zoneParticipationTypes.monitoring'), description: t('isa62443.securityZones.zoneParticipationTypes.monitoringDesc') },
  { value: 'maintenance', label: t('isa62443.securityZones.zoneParticipationTypes.maintenance'), description: t('isa62443.securityZones.zoneParticipationTypes.maintenanceDesc') },
  { value: 'safety', label: t('isa62443.securityZones.zoneParticipationTypes.safety'), description: t('isa62443.securityZones.zoneParticipationTypes.safetyDesc') }
])

function getParticipationTypeLabel(value) {
  const types = zoneParticipationTypes.value
  const type = types.find(t => t.value === value)
  return type ? type.label : value
}

function getParticipationTypeLabelForDisplay(value) {
  return getParticipationTypeLabel(value)
}

// Computed property for selected assets with their details
const selectedAssetsWithDetails = computed(() => {
  return selectedAssets.value.map(asset => {
    const details = selectedAssetsDetails.value[asset.id] || {}
    return {
      ...asset,
      participationType: details.participationType || null,
      interfaceScope: details.interfaceScope || '',
      slTarget: details.slTarget || null
    }
  })
})

// Check if all selected assets have a participation type
const allAssetsHaveParticipationType = computed(() => {
  if (selectedAssets.value.length === 0) return false
  return selectedAssets.value.every(asset => {
    const details = selectedAssetsDetails.value[asset.id]
    return details && details.participationType
  })
})

// Apply default participation type to all selected assets
function applyDefaultParticipationType() {
  if (!defaultParticipationType.value) return
  
  selectedAssets.value.forEach(asset => {
    if (!selectedAssetsDetails.value[asset.id]) {
      selectedAssetsDetails.value[asset.id] = {}
    }
    selectedAssetsDetails.value[asset.id].participationType = defaultParticipationType.value
  })
}

// Update participation type for a specific asset
function updateAssetParticipationType(assetId, participationType) {
  if (!selectedAssetsDetails.value[assetId]) {
    selectedAssetsDetails.value[assetId] = {}
  }
  selectedAssetsDetails.value[assetId].participationType = participationType
}

// Update interface scope for a specific asset
function updateAssetInterfaceScope(assetId, interfaceScope) {
  if (!selectedAssetsDetails.value[assetId]) {
    selectedAssetsDetails.value[assetId] = {}
  }
  selectedAssetsDetails.value[assetId].interfaceScope = interfaceScope
}

// Update SL target for a specific asset
function updateAssetSlTarget(assetId, slTarget) {
  if (!selectedAssetsDetails.value[assetId]) {
    selectedAssetsDetails.value[assetId] = {}
  }
  selectedAssetsDetails.value[assetId].slTarget = slTarget
}

// Remove asset from selection
function removeSelectedAsset(assetId) {
  selectedAssets.value = selectedAssets.value.filter(a => a.id !== assetId)
  delete selectedAssetsDetails.value[assetId]
}

// Add Conduit Dialog
const showAddConduitDialog = ref(false)

async function fetchZone() {
  try {
    const res = await api.getSecurityZone(route.params.id)
    zone.value = res.data
  } catch (error) {
    console.error('Error fetching zone:', error)
  }
}

function handleZoneUpdated(updatedZone) {
  zone.value = updatedZone
}

async function fetchAssets() {
  assetsLoading.value = true
  try {
    const res = await api.getZoneAssets(route.params.id)
    assets.value = res.data || []
  } catch (error) {
    console.error('Error fetching zone assets:', error)
    assets.value = []
  } finally {
    assetsLoading.value = false
  }
}

async function fetchConduits() {
  conduitsLoading.value = true
  try {
    const res = await api.getConduits({ zone_id: route.params.id })
    conduits.value = res.data || []
  } catch (error) {
    console.error('Error fetching zone conduits:', error)
    conduits.value = []
  } finally {
    conduitsLoading.value = false
  }
}

function goToAsset(assetId) {
  router.push(`/assets/${assetId}`)
}

function goToConduit(conduitId) {
  router.push(`/conduits`)
}

function getRiskSeverity(riskScore) {
  if (riskScore >= 7) return 'danger'
  if (riskScore >= 4) return 'warning'
  return 'success'
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

function getSLASeverity(slAchieved, slTarget) {
  if (slTarget == null || slAchieved == null) return 'info'
  if (slAchieved >= slTarget) return 'success'
  if (slTarget - slAchieved === 1) return 'warning'
  return 'danger'
}

function getGapSeverity(slTarget, slAchieved) {
  if (slTarget == null || slAchieved == null) return 'info'
  const gap = slTarget - slAchieved
  if (gap <= 0) return 'success'
  if (gap === 1) return 'warning'
  return 'danger'
}

function onSort(event) {
  sortField.value = event.sortField
  sortOrder.value = event.sortOrder
}

function onConduitsSort(event) {
  conduitsSortField.value = event.sortField
  conduitsSortOrder.value = event.sortOrder
}

const filteredAvailableAssets = computed(() => {
  if (!assetSearchFilter.value) {
    return availableAssets.value
  }
  const filter = assetSearchFilter.value.toLowerCase()
  return availableAssets.value.filter(asset => 
    asset.name?.toLowerCase().includes(filter) ||
    asset.asset_type?.name?.toLowerCase().includes(filter)
  )
})

async function loadAvailableAssets() {
  availableAssetsLoading.value = true
  try {
    const res = await api.getAssets({ limit: 1000, include_memberships: true })
    if (res.data && res.data.data) {
      availableAssets.value = res.data.data || []
    } else if (res.data && Array.isArray(res.data)) {
      availableAssets.value = res.data
    } else {
      availableAssets.value = []
    }
    // Ensure all assets have an id field (keep original UUID, but also store as string for PrimeVue compatibility)
    availableAssets.value = availableAssets.value.map(asset => {
      const assetId = asset.id || asset.uuid || asset._id
      return {
        ...asset,
        id: assetId ? String(assetId) : null,
        uuid: assetId // Keep original UUID for API calls
      }
    }).filter(asset => asset.id) // Remove assets without id
    
    // Debug: log first asset to verify structure
    if (availableAssets.value.length > 0) {
      console.log('First asset structure:', availableAssets.value[0])
      console.log('Asset ID type:', typeof availableAssets.value[0].id)
    }
  } catch (error) {
    console.error('Error loading available assets:', error)
    availableAssets.value = []
  } finally {
    availableAssetsLoading.value = false
  }
}

async function loadAllZones() {
  try {
    const res = await api.getSecurityZones()
    allZones.value = res.data || []
  } catch (error) {
    console.error('Error loading zones:', error)
    allZones.value = []
  }
}

async function addAssetsToZone() {
  if (selectedAssets.value.length === 0) {
    toast.add({
      severity: 'warn',
      summary: t('common.messages.warning'),
      detail: t('isa62443.securityZones.membershipRequiredFields'),
      life: 3000
    })
    return
  }
  
  // Validate that all assets have a participation type
  const assetsWithoutType = selectedAssets.value.filter(asset => {
    const details = selectedAssetsDetails.value[asset.id]
    return !details || !details.participationType
  })
  
  if (assetsWithoutType.length > 0) {
    toast.add({
      severity: 'warn',
      summary: t('common.messages.warning'),
      detail: t('isa62443.securityZones.allAssetsNeedParticipationType'),
      life: 3000
    })
    return
  }
  
  try {
    const promises = selectedAssets.value.map(asset => {
      const details = selectedAssetsDetails.value[asset.id] || {}
      // Use the original UUID (stored in uuid field) or convert string id back to UUID
      const assetId = asset.uuid || asset.id
      return api.createZoneMembership(route.params.id, {
        asset_id: assetId,
        role: details.participationType,
        interface_scope: details.interfaceScope || null,
        sl_target: details.slTarget || null
      })
    })
    await Promise.all(promises)
    
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: t('isa62443.securityZones.assetsAdded', { count: selectedAssets.value.length }),
      life: 3000
    })
    
    selectedAssets.value = []
    selectedAssetsDetails.value = {}
    defaultParticipationType.value = null
    showAddAssetDialog.value = false
    await fetchAssets()
    await fetchZone() // Refresh zone to update asset count
  } catch (error) {
    console.error('Error adding assets to zone:', error)
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: error.response?.data?.detail || t('isa62443.securityZones.errorAddingAssets'),
      life: 3000
    })
  }
}

async function removeAssetFromZone(assetId) {
  // Find the membership for this asset in this zone
  const asset = assets.value.find(a => a.id === assetId)
  if (!asset) return
  
  // Get membership ID from the asset data (if available) or fetch it
  try {
    // Fetch asset memberships to find the one for this zone
    const membershipsRes = await api.getAssetZoneMemberships(assetId)
    const membership = membershipsRes.data.find(m => m.security_zone_id === route.params.id)
    
    if (!membership) {
      toast.add({
        severity: 'error',
        summary: t('common.messages.error'),
        detail: t('isa62443.securityZones.membershipNotFound'),
        life: 3000
      })
      return
    }
    
    await api.deleteZoneMembership(route.params.id, membership.id)
    
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: t('isa62443.securityZones.assetRemoved'),
      life: 3000
    })
    
    await fetchAssets()
    await fetchZone() // Refresh zone to update asset count
  } catch (error) {
    console.error('Error removing asset from zone:', error)
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: error.response?.data?.detail || t('isa62443.securityZones.errorRemovingAsset'),
      life: 3000
    })
  }
}

function getZoneNameForAsset(zoneId) {
  const foundZone = allZones.value.find(z => z.id === zoneId)
  return foundZone?.name || zoneId
}

function getAssetOtherZones(assetId) {
  const asset = assets.value.find(a => a.id === assetId)
  if (!asset || !asset.other_zones) return []
  return asset.other_zones.map(oz => ({
    id: oz.zone_id,
    name: oz.zone_name,
    role: oz.role
  }))
}

function getAssetOtherZonesInDialog(assetId) {
  const asset = availableAssets.value.find(a => a.id === assetId)
  if (!asset || !asset.zone_memberships) return []
  return asset.zone_memberships
    .filter(m => m.security_zone_id !== route.params.id)
    .map(m => ({
      id: m.security_zone_id,
      name: m.security_zone_name || m.security_zone_id,
      role: m.role
    }))
}

function resetAddAssetForm() {
  selectedAssets.value = []
  selectedAssetsDetails.value = {}
  defaultParticipationType.value = null
}


async function handleConduitSubmit(conduitData) {
  try {
    await api.createConduit(conduitData)
    
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: t('isa62443.conduits.conduitCreated'),
      life: 3000
    })
    
    showAddConduitDialog.value = false
    await fetchConduits()
    await fetchZone() // Refresh zone to update conduit count
  } catch (error) {
    console.error('Error creating conduit:', error)
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: t('isa62443.conduits.errorCreatingConduit'),
      life: 3000
    })
  }
}

// Watch for dialog opening to load data
watch(showAddAssetDialog, (isOpen) => {
  if (isOpen) {
    loadAvailableAssets()
    loadAllZones()
    selectedAssets.value = []
    assetSearchFilter.value = ''
  }
})

watch(showAddConduitDialog, (isOpen) => {
  if (isOpen) {
    loadAllZones()
  }
})

function goToComplianceTab() {
  // Switch to compliance tab (index 2: Assets=0, Conduits=1, Compliance=2)
  activeTabIndex.value = 2
}

onMounted(async () => {
  await Promise.all([
    fetchZone(),
    fetchAssets(),
    fetchConduits(),
    loadAllZones()
  ])
})
</script>

<style scoped>
.security-zone-detail {
  padding: 1.5rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.zone-details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.zone-status-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.asset-link,
.conduit-link {
  color: var(--primary-color);
  cursor: pointer;
  text-decoration: none;
  font-weight: 500;
}

.asset-link:hover,
.conduit-link:hover {
  text-decoration: underline;
}
</style>
