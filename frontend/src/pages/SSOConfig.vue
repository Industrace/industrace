<template>
  <div class="sso-config-page">
    <div class="page-header">
      <h1>{{ t('sso.title') }}</h1>
    </div>

    <TabView v-if="config" class="mt-4">
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
              :disabled="!!config"
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
            <label>{{ t('sso.clientSecret') }} *</label>
            <Password v-model="formData.client_secret" :feedback="false" toggleMask />
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
              :selection="selectedUsers"
              selectionMode="multiple"
              @selection-change="selectedUsers = $event"
              :globalFilterFields="['displayName', 'mail', 'userPrincipalName']"
              class="p-datatable-sm"
            >
              <Column selectionMode="multiple" headerStyle="width: 3rem" />
              <Column field="displayName" :header="t('common.fields.name')" sortable />
              <Column field="mail" :header="t('common.fields.email')" sortable>
                <template #body="{ data }">
                  {{ data.mail || data.userPrincipalName || '-' }}
                </template>
              </Column>
              <Column field="userPrincipalName" :header="t('sso.userPrincipalName')" sortable />
              <Column field="accountEnabled" :header="t('sso.accountEnabled')">
                <template #body="{ data }">
                  <Tag 
                    :value="data.accountEnabled ? t('common.strings.yes') : t('common.strings.no')" 
                    :severity="data.accountEnabled ? 'success' : 'danger'"
                  />
                </template>
              </Column>
              <Column field="jobTitle" :header="t('sso.jobTitle')" />
              <Column field="department" :header="t('sso.department')" />
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

    <Card v-if="!config">
      <template #title>{{ t('sso.noConfiguration') }}</template>
      <template #content>
        <p>{{ t('sso.setupMessage') }}</p>
        <Button 
          :label="t('sso.startSetup')" 
          icon="pi pi-plus" 
          @click="startSetup"
        />
      </template>
    </Card>
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
  auto_provision_enabled: true,
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

const providerOptions = [
  { label: 'Azure AD (EntraID)', value: 'azure_ad' },
  { label: 'Generic OIDC', value: 'oidc_generic' }
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
    }
  } catch (error) {
    if (error.response?.status === 404) {
      config.value = null
    } else {
      console.error('Error fetching SSO config:', error)
    }
  }
}

function startSetup() {
  config.value = { enabled: false }
}

async function saveConfig() {
  saving.value = true
  try {
    if (config.value && config.value.tenant_id) {
      await api.updateSSOConfig(formData.value)
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('sso.configUpdated') })
    } else {
      await api.createSSOConfig(formData.value)
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('sso.configCreated') })
    }
    await fetchConfig()
  } catch (error) {
    console.error('Error saving SSO config:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: error.response?.data?.detail || t('sso.errorSaving') })
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
  try {
    const params = {}
    if (userFilter.value) {
      // Simple filter: search in displayName or mail
      params.filter_query = `startswith(displayName,'${userFilter.value}') or startswith(mail,'${userFilter.value}')`
    }
    const res = await api.listAzureADUsers(params)
    azureUsers.value = res.data.users || []
  } catch (error) {
    console.error('Error loading Azure AD users:', error)
    toast.add({ 
      severity: 'error', 
      summary: t('common.errors.error'), 
      detail: error.response?.data?.detail || t('sso.errorLoadingUsers') 
    })
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
  if (config.value && config.value.provider_type === 'azure_ad') {
    await loadAzureUsers()
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

