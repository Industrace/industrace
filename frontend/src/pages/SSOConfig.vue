<template>
  <div class="sso-config-page">
    <div class="page-header">
      <h1>{{ t('sso.title') }}</h1>
    </div>

        <!-- Setup Guide for Azure AD -->
        <Card v-if="formData.provider_type === 'azure_ad' || !formData.provider_type" class="mb-3">
      <template #title>
        <div class="flex align-items-center gap-2">
          <i class="pi pi-info-circle"></i>
          {{ t('sso.setupGuide') }}
        </div>
      </template>
      <template #content>
        <div class="setup-guide">
          <p class="mb-3">{{ t('sso.setupGuideDescription') }}</p>
          <Button 
            :label="t('sso.viewSetupGuide')" 
            icon="pi pi-external-link"
            @click="openSetupGuide"
            class="p-button-outlined"
          />
        </div>
      </template>
    </Card>

    <TabView class="mt-4">
      <!-- Configuration Tab -->
      <TabPanel>
        <template #header>
          <span style="display: flex; align-items: center; gap: 0.4em;">
            <i class="pi pi-cog"></i> {{ t('sso.configuration') }}
          </span>
        </template>
        <Card>
      <template #title>{{ t('sso.configuration') }}</template>
      <template #content>
        <div class="p-fluid">
          <div class="field">
            <label>{{ t('sso.providerType') }} *</label>
            <Dropdown
              v-model="formData.provider_type"
              :options="providerOptions"
              optionLabel="label"
              optionValue="value"
              :placeholder="t('sso.selectProvider')"
              class="w-full"
            />
          </div>
          <div class="field">
            <label>{{ t('sso.enabled') }}</label>
            <InputSwitch v-model="formData.enabled" />
          </div>
          <div class="field">
            <label>{{ t('sso.clientId') }} *</label>
            <InputText v-model="formData.client_id" />
          </div>
          <div class="field">
            <label>{{ t('sso.clientSecret') }}<span v-if="!config"> *</span></label>
            <Password v-model="formData.client_secret" :feedback="false" toggleMask :placeholder="config ? t('sso.clientSecretPlaceholder') || 'Leave empty to keep existing secret' : ''" />
            <small v-if="config" class="text-color-secondary block mt-1">{{ t('sso.clientSecretHelp') || 'Leave empty to keep the existing secret. Enter a new value only to change it.' }}</small>
          </div>
          <div class="field">
            <label>{{ t('sso.tenantDomain') }}</label>
            <InputText v-model="formData.tenant_domain" :placeholder="t('sso.tenantDomainPlaceholder')" />
          </div>
          <div class="field">
            <label>{{ t('sso.redirectUri') }} *</label>
            <InputText v-model="formData.redirect_uri" />
          </div>
          <div class="field-checkbox">
            <Checkbox 
              v-model="formData.auto_provision_enabled" 
              :binary="true"
              inputId="auto_provision"
            />
            <label for="auto_provision" class="ml-2">{{ t('sso.autoProvisionEnabled') }}</label>
            <small class="text-color-secondary block mt-1">{{ t('sso.autoProvisionHelp') }}</small>
          </div>
          <div class="field">
            <label>{{ t('sso.domainRestriction') }}</label>
            <InputText v-model="formData.domain_restriction" :placeholder="t('sso.domainRestrictionPlaceholder')" />
          </div>
          <div class="flex justify-content-end gap-2 mt-3">
            <Button 
              :label="t('sso.testConnection')" 
              icon="pi pi-check" 
              @click="testConnection"
              :loading="testing"
            />
            <Button 
              :label="t('common.actions.save')" 
              icon="pi pi-save" 
              @click="saveConfig"
              :loading="saving"
            />
          </div>
        </div>
      </template>
        </Card>
      </TabPanel>

      <!-- Import Users Tab (Azure AD only) -->
      <TabPanel v-if="config && config.provider_type === 'azure_ad'">
        <template #header>
          <span style="display: flex; align-items: center; gap: 0.4em;">
            <i class="pi pi-users"></i> {{ t('sso.importUsers') }}
          </span>
        </template>
        <Card>
          <template #title>{{ t('sso.importUsersFromAzureAD') }}</template>
          <template #content>
            <div class="mb-4">
              <div class="flex gap-2 mb-3">
                <InputText 
                  v-model="userFilter" 
                  :placeholder="t('sso.filterUsers')"
                  class="flex-1"
                  @keyup.enter="loadAzureUsers"
                />
                <Button 
                  :label="t('common.actions.search')" 
                  icon="pi pi-search" 
                  @click="loadAzureUsers"
                  :loading="loadingUsers"
                />
                <Button 
                  :label="t('common.actions.refresh')" 
                  icon="pi pi-refresh" 
                  @click="loadAzureUsers"
                  :loading="loadingUsers"
                  severity="secondary"
                />
              </div>
              
              <div class="mb-3">
                <label class="block mb-2">{{ t('sso.selectRoleForImport') }} *</label>
                <Dropdown
                  v-model="selectedRoleId"
                  :options="roles"
                  optionLabel="name"
                  optionValue="id"
                  :placeholder="t('sso.selectRole')"
                  class="w-full"
                />
              </div>
            </div>

            <div v-if="loadingUsers" class="text-center p-4">
              <ProgressSpinner />
            </div>

            <div v-else-if="azureUsers.length === 0" class="text-center p-4">
              <p>{{ t('sso.noUsersFound') }}</p>
            </div>

            <DataTable 
              v-else
              :value="azureUsers" 
              :paginator="true"
              :rows="20"
              v-model:selection="selectedUsers"
              selectionMode="multiple"
              dataKey="id"
              :globalFilterFields="['displayName', 'mail', 'userPrincipalName']"
              class="p-datatable-sm"
              :key="`azure-users-${azureUsers.length}`"
            >
              <Column selectionMode="multiple" headerStyle="width: 3rem" />
              <Column field="displayName" :header="t('common.fields.name')" sortable>
                <template #body="{ data }">
                  <span v-if="data">{{ data.displayName || '-' }}</span>
                </template>
              </Column>
              <Column field="mail" :header="t('common.fields.email')" sortable>
                <template #body="{ data }">
                  <span v-if="data">{{ data.mail || data.userPrincipalName || '-' }}</span>
                </template>
              </Column>
              <Column field="userPrincipalName" :header="t('sso.userPrincipalName')" sortable>
                <template #body="{ data }">
                  <span v-if="data">{{ data.userPrincipalName || '-' }}</span>
                </template>
              </Column>
              <Column field="accountEnabled" :header="t('sso.accountEnabled')">
                <template #body="{ data }">
                  <Tag 
                    v-if="data"
                    :value="data.accountEnabled ? t('common.strings.yes') : t('common.strings.no')" 
                    :severity="data.accountEnabled ? 'success' : 'danger'"
                  />
                </template>
              </Column>
              <Column field="jobTitle" :header="t('sso.jobTitle')">
                <template #body="{ data }">
                  <span v-if="data">{{ data.jobTitle || '-' }}</span>
                </template>
              </Column>
              <Column field="department" :header="t('sso.department')">
                <template #body="{ data }">
                  <span v-if="data">{{ data.department || '-' }}</span>
                </template>
              </Column>
            </DataTable>

            <div v-if="selectedUsers.length > 0" class="mt-4 flex justify-content-between align-items-center">
              <span>{{ t('sso.selectedUsersCount', { count: selectedUsers.length }) }}</span>
              <Button 
                :label="t('sso.importSelected')" 
                icon="pi pi-download" 
                @click="importUsers"
                :loading="importing"
                :disabled="!selectedRoleId"
              />
            </div>
          </template>
        </Card>
      </TabPanel>
    </TabView>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import InputSwitch from 'primevue/inputswitch'
import Checkbox from 'primevue/checkbox'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import ProgressSpinner from 'primevue/progressspinner'
import api from '@/api/api'

const { t } = useI18n()
const toast = useToast()

const config = ref(null)
const formData = ref({
  provider_type: 'azure_ad',
  enabled: false,
  client_id: '',
  client_secret: '',
  tenant_domain: '',
  redirect_uri: '',
  auto_provision_enabled: false, // Default: disabled for maximum security (only existing users can login)
  domain_restriction: ''
})
const saving = ref(false)
const testing = ref(false)

// Azure AD User Import
const azureUsers = ref([])
const selectedUsers = ref([])
const selectedRoleId = ref(null)
const roles = ref([])
const loadingUsers = ref(false)
const importing = ref(false)
const userFilter = ref('')

const openSetupGuide = () => {
  window.open(
    'https://github.com/industrace/industrace/blob/main/docs/ADMINISTRATION.md#sso-with-azure-ad',
    '_blank'
  )
}

// Provider SSO disponibili
// Nota: Il backend supporta già Azure AD, Google Workspace, Okta e Generic OIDC
// Altri provider verranno abilitati nel frontend quando implementati
const providerOptions = [
  { label: 'Azure AD (EntraID)', value: 'azure_ad' }
  // Temporaneamente disabilitati - da implementare in futuro
  // { label: 'Google Workspace', value: 'google' },
  // { label: 'Okta', value: 'okta' },
  // { label: 'Generic OIDC', value: 'oidc_generic' }
]

async function fetchConfig() {
  try {
    const res = await api.getSSOConfig()
    config.value = res.data
    if (config.value) {
      formData.value = {
        provider_type: config.value.provider_type || 'azure_ad',
        enabled: config.value.enabled || false,
        client_id: config.value.client_id || '',
        client_secret: '', // Never show existing secret
        tenant_domain: config.value.tenant_domain || '',
        redirect_uri: config.value.redirect_uri || '',
        auto_provision_enabled: config.value.auto_provision_enabled !== false,
        domain_restriction: config.value.domain_restriction || ''
      }
    } else {
      // Reset form if no config exists
      formData.value = {
        provider_type: 'azure_ad',
        enabled: false,
        client_id: '',
        client_secret: '',
        tenant_domain: '',
        redirect_uri: '',
        auto_provision_enabled: false,
        domain_restriction: ''
      }
    }
  } catch (error) {
    if (error.response?.status === 404) {
      config.value = null
      // Reset form if no config exists
      formData.value = {
        provider_type: 'azure_ad',
        enabled: false,
        client_id: '',
        client_secret: '',
        tenant_domain: '',
        redirect_uri: '',
        auto_provision_enabled: false,
        domain_restriction: ''
      }
    } else {
      console.error('Error fetching SSO config:', error)
    }
  }
}

function startSetup() {
  // Form is always visible now, this function is no longer needed
  // But keeping it for backward compatibility
}

async function saveConfig() {
  saving.value = true
  try {
    if (config.value && config.value.tenant_id) {
      // For update: don't send client_secret if it's empty (preserve existing secret)
      const updateData = { ...formData.value }
      if (!updateData.client_secret || updateData.client_secret.trim() === '') {
        delete updateData.client_secret
      }
      await api.updateSSOConfig(updateData)
      toast.add({ severity: 'success', summary: t('common.messages.success'), detail: t('sso.configUpdated') })
    } else {
      await api.createSSOConfig(formData.value)
      toast.add({ severity: 'success', summary: t('common.messages.success'), detail: t('sso.configCreated') })
    }
    await fetchConfig()
  } catch (error) {
    console.error('Error saving SSO config:', error)
    toast.add({ severity: 'error', summary: t('common.messages.error'), detail: error.response?.data?.detail || t('sso.errorSaving') })
  } finally {
    saving.value = false
  }
}

async function testConnection() {
  testing.value = true
  try {
    const res = await api.testSSOConnection()
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('sso.testSuccess') })
  } catch (error) {
    console.error('Error testing SSO:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: error.response?.data?.detail || t('sso.testFailed') })
  } finally {
    testing.value = false
  }
}

async function loadRoles() {
  try {
    const res = await api.getRoles()
    roles.value = res.data || []
  } catch (error) {
    console.error('Error loading roles:', error)
  }
}

async function loadAzureUsers() {
  if (!config.value || config.value.provider_type !== 'azure_ad') {
    return
  }
  
  loadingUsers.value = true
  selectedUsers.value = [] // Clear selection when loading new users
  try {
    const params = {}
    if (userFilter.value) {
      // Simple filter: search in displayName or mail
      params.filter_query = `startswith(displayName,'${userFilter.value}') or startswith(mail,'${userFilter.value}')`
    }
    const res = await api.listAzureADUsers(params)
    // Filter out any invalid users and ensure all have an id
    azureUsers.value = (res.data.users || []).filter(user => user && user.id)
  } catch (error) {
    console.error('Error loading Azure AD users:', error)
    const errorDetail = error.response?.data?.detail || t('sso.errorLoadingUsers')
    // Check if it's a decryption error
    if (errorDetail && (errorDetail.toLowerCase().includes('decrypt') || errorDetail.toLowerCase().includes('encryption_key'))) {
      toast.add({ 
        severity: 'error', 
        summary: t('common.errors.error'), 
        detail: t('sso.clientSecretDecryptError') || 'Unable to decrypt client secret. Please reconfigure the SSO settings with a new client secret.',
        life: 8000
      })
    } else {
      toast.add({ 
        severity: 'error', 
        summary: t('common.errors.error'), 
        detail: errorDetail
      })
    }
    azureUsers.value = []
  } finally {
    loadingUsers.value = false
  }
}

async function importUsers() {
  if (!selectedRoleId.value || selectedUsers.value.length === 0) {
    toast.add({ 
      severity: 'warn', 
      summary: t('common.messages.warning'), 
      detail: t('sso.selectUsersAndRole') 
    })
    return
  }
  
  importing.value = true
  try {
    const userIds = selectedUsers.value.map(u => u.id)
    const res = await api.importAzureADUsers({
      user_ids: userIds,
      role_id: selectedRoleId.value,
      send_invitation: false
    })
    
    toast.add({ 
      severity: 'success', 
      summary: t('common.messages.success'), 
      detail: t('sso.usersImported', { imported: res.data.imported, skipped: res.data.skipped })
    })
    
    // Clear selection and reload
    selectedUsers.value = []
    await loadAzureUsers()
  } catch (error) {
    console.error('Error importing users:', error)
    toast.add({ 
      severity: 'error', 
      summary: t('common.errors.error'), 
      detail: error.response?.data?.detail || t('sso.errorImportingUsers') 
    })
  } finally {
    importing.value = false
  }
}

onMounted(async () => {
  await fetchConfig()
  await loadRoles()
  // Try to load Azure AD users, but don't fail if it errors (e.g., decryption error)
  // User can still reconfigure SSO settings
  if (config.value && config.value.provider_type === 'azure_ad') {
    try {
      await loadAzureUsers()
    } catch (error) {
      // Error already handled in loadAzureUsers, just log it
      console.warn('Failed to load Azure AD users on mount:', error)
    }
  }
})
</script>

<style scoped>
.sso-config-page {
  padding: 1.5rem;
}

.page-header {
  margin-bottom: 1.5rem;
}
</style>

