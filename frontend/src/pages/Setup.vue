<template>
  <div class="setup-page">
    <div class="setup-header">
      <h1>{{ $t('setup.title') }}</h1>
      <p class="setup-description">
        {{ $t('setup.strings.description') }}
      </p>
    </div>

    <div class="setup-tiles">
      <!-- SSO Configuration Tile -->
      <div class="setup-tile" @click="goToSSO">
        <div class="tile-icon">
          <i class="pi pi-lock"></i>
        </div>
        <div class="tile-content">
          <h3>{{ $t('setup.strings.sso.title') }}</h3>
          <p>{{ $t('setup.strings.sso.description') }}</p>
        </div>
        <div class="tile-status">
          <i class="pi pi-arrow-right"></i>
        </div>
      </div>

      <!-- Users Management Tile -->
      <div class="setup-tile" @click="goToUsers">
        <div class="tile-icon">
          <i class="pi pi-users"></i>
        </div>
        <div class="tile-content">
          <h3>{{ $t('setup.strings.users.title') }}</h3>
          <p>{{ $t('setup.strings.users.description') }}</p>
        </div>
        <div class="tile-status">
          <i class="pi pi-arrow-right"></i>
        </div>
      </div>

      <!-- Roles Management Tile -->
      <div class="setup-tile" @click="goToRoles">
        <div class="tile-icon">
          <i class="pi pi-key"></i>
        </div>
        <div class="tile-content">
          <h3>{{ $t('setup.strings.roles.title') }}</h3>
          <p>{{ $t('setup.strings.roles.description') }}</p>
        </div>
        <div class="tile-status">
          <i class="pi pi-arrow-right"></i>
        </div>
      </div>

      <!-- Notifications Management Tile -->
      <div class="setup-tile" @click="goToNotifications">
        <div class="tile-icon">
          <i class="pi pi-bell"></i>
        </div>
        <div class="tile-content">
          <h3>{{ $t('setup.strings.notifications.title') }}</h3>
          <p>{{ $t('setup.strings.notifications.description') }}</p>
        </div>
        <div class="tile-status">
          <i class="pi pi-arrow-right"></i>
        </div>
      </div>

      <!-- SMTP Configuration Tile -->
      <div class="setup-tile" @click="openSmtpDialog">
        <div class="tile-icon">
          <i class="pi pi-envelope"></i>
        </div>
        <div class="tile-content">
          <h3>{{ $t('setup.strings.smtp.title') }}</h3>
          <p>{{ $t('setup.strings.smtp.description') }}</p>
        </div>
        <div class="tile-status" :class="{ 'configured': smtpConfigured }">
          <i :class="smtpConfigured ? 'pi pi-check-circle' : 'pi pi-exclamation-circle'"></i>
        </div>
      </div>

      <!-- Print Templates Tile -->
      <div class="setup-tile" @click="openTemplatesDialog">
        <div class="tile-icon">
          <i class="pi pi-print"></i>
        </div>
        <div class="tile-content">
          <h3>{{ $t('setup.strings.printTemplates.title') }}</h3>
          <p>{{ $t('setup.strings.printTemplates.initDescription') }}</p>
        </div>
        <div class="tile-status" :class="{ 'configured': templatesConfigured }">
          <i :class="templatesConfigured ? 'pi pi-check-circle' : 'pi pi-cog'"></i>
        </div>
      </div>

      <!-- Printed Kit Tile -->
      <div class="setup-tile" @click="openPrintedKitDialog">
        <div class="tile-icon">
          <i class="pi pi-book"></i>
        </div>
        <div class="tile-content">
          <h3>{{ $t('setup.strings.printedKit.title') }}</h3>
          <p>{{ $t('setup.strings.printedKit.description') }}</p>
        </div>
        <div class="tile-status">
          <i class="pi pi-download"></i>
        </div>
      </div>

      <!-- Vulnerability Feeds Tile -->
      <div class="setup-tile" @click="goToVulnerabilityFeeds">
        <div class="tile-icon">
          <i class="pi pi-shield"></i>
        </div>
        <div class="tile-content">
          <h3>{{ $t('setup.strings.vulnerabilityFeeds.title') }}</h3>
          <p>{{ $t('setup.strings.vulnerabilityFeeds.description') }}</p>
        </div>
        <div class="tile-status">
          <i class="pi pi-arrow-right"></i>
        </div>
      </div>

    </div>

    <!-- SMTP Configuration Dialog -->
    <Dialog 
      v-model:visible="smtpDialogVisible" 
      :header="$t('setup.strings.smtp.title')"
      modal 
      class="setup-dialog"
      :style="{ width: '600px' }"
    >
      <div class="smtp-form">
        <div class="form-row">
          <div class="form-field">
            <label for="smtp_host">{{ $t('setup.fields.smtp.host') }}</label>
            <InputText id="smtp_host" v-model="smtpConfig.host" placeholder="smtp.gmail.com" />
          </div>
          <div class="form-field">
            <label for="smtp_port">{{ $t('setup.fields.smtp.port') }}</label>
            <InputNumber id="smtp_port" v-model="smtpConfig.port" placeholder="587" />
          </div>
        </div>

        <div class="form-row">
          <div class="form-field">
            <label for="smtp_username">{{ $t('setup.fields.smtp.username') }}</label>
            <InputText id="smtp_username" v-model="smtpConfig.username" placeholder="user@example.com" />
          </div>
          <div class="form-field">
            <label for="smtp_password_input">{{ $t('setup.fields.smtp.password') }}</label>
            <Password id="smtp_password" v-model="smtpConfig.password" :feedback="false" inputId="smtp_password_input" />
          </div>
        </div>

        <div class="form-row">
          <div class="form-field">
            <label for="smtp_from_email">{{ $t('setup.fields.smtp.fromEmail') }}</label>
            <InputText id="smtp_from_email" v-model="smtpConfig.from_email" placeholder="noreply@example.com" />
          </div>
          <div class="form-field checkbox-field">
            <label class="checkbox-label">
              <Checkbox v-model="smtpConfig.use_tls" :binary="true" inputId="smtp_use_tls" />
              {{ $t('setup.fields.smtp.useTls') }}
            </label>
          </div>
        </div>

        <div class="form-actions">
          <Button 
            :label="$t('setup.strings.smtp.testConnection')" 
            icon="pi pi-refresh" 
            @click="testSmtpConnection"
            :loading="testingConnection"
          />
          <Button 
            :label="$t('setup.strings.smtp.saveSettings')" 
            icon="pi pi-save" 
            @click="saveSmtpConfig"
            :loading="savingSmtp"
          />
        </div>
      </div>
    </Dialog>

    <!-- Print Templates Dialog - Semplificato -->
    <Dialog 
      v-model:visible="templatesDialogVisible" 
      :header="$t('setup.strings.printTemplates.title')"
      modal 
      class="setup-dialog"
      :style="{ width: '500px' }"
    >
      <div class="templates-simple">
        <div class="templates-info">
          <i class="pi pi-info-circle" style="color: var(--primary-color); font-size: 1.2rem;"></i>
          <p>{{ $t('setup.strings.printTemplates.defaultTemplatesInfo') }}</p>
          <ul>
            <li v-for="item in defaultTemplatesList" :key="item">{{ item }}</li>
            <!-- Fallback se gli array non funzionano -->
            <li v-if="defaultTemplatesList.length === 0">{{ $t('setup.strings.printTemplates.defaultTemplate1') }}</li>
            <li v-if="defaultTemplatesList.length === 0">{{ $t('setup.strings.printTemplates.defaultTemplate2') }}</li>
          </ul>
        </div>
        
        <div class="templates-actions">
          <Button 
            :label="$t('setup.strings.printTemplates.initDefaults')" 
            icon="pi pi-download" 
            @click="initDefaultTemplates"
            :loading="initializingTemplates"
            severity="primary"
            class="w-full"
          />
        </div>
      </div>
    </Dialog>

    <!-- Printed Kit Dialog - Nuovo -->
    <Dialog 
      v-model:visible="printedKitDialogVisible" 
      :header="$t('setup.strings.printedKit.info.title')"
      modal 
      class="setup-dialog"
      :style="{ width: '600px' }"
    >
      <div class="printed-kit">
        <div class="kit-info">
          <i class="pi pi-book" style="color: var(--primary-color); font-size: 1.2rem;"></i>
          <p>{{ $t('setup.strings.printedKit.info.description') }}</p>
          <ul>
            <li v-for="item in printedKitItems" :key="item">{{ item }}</li>
            <!-- Fallback se gli array non funzionano -->
            <li v-if="printedKitItems.length === 0">{{ $t('setup.strings.printedKit.info.item1') }}</li>
            <li v-if="printedKitItems.length === 0">{{ $t('setup.strings.printedKit.info.item2') }}</li>
            <li v-if="printedKitItems.length === 0">{{ $t('setup.strings.printedKit.info.item3') }}</li>
            <li v-if="printedKitItems.length === 0">{{ $t('setup.strings.printedKit.info.item4') }}</li>
            <li v-if="printedKitItems.length === 0">{{ $t('setup.strings.printedKit.info.item5') }}</li>
          </ul>
        </div>
        
        <div class="kit-options">
          <h4>{{ $t('setup.strings.printedKit.generationOptions') }}</h4>
          <div class="option-item">
            <label class="checkbox-label">
              <Checkbox v-model="kitOptions.includeAssets" :binary="true" inputId="kit_include_assets" />
              {{ $t('setup.strings.printedKit.options.includeAssets') }}
            </label>
          </div>
          <div class="option-item">
            <label class="checkbox-label">
              <Checkbox v-model="kitOptions.includeSites" :binary="true" inputId="kit_include_sites" />
              {{ $t('setup.strings.printedKit.options.includeSites') }}
            </label>
          </div>
          <div class="option-item">
            <label class="checkbox-label">
              <Checkbox v-model="kitOptions.includeContacts" :binary="true" inputId="kit_include_contacts" />
              {{ $t('setup.strings.printedKit.options.includeContacts') }}
            </label>
          </div>
          <div class="option-item">
            <label class="checkbox-label">
              <Checkbox v-model="kitOptions.includeSuppliers" :binary="true" inputId="kit_include_suppliers" />
              {{ $t('setup.strings.printedKit.options.includeSuppliers') }}
            </label>
          </div>
        </div>
        
        <div class="kit-actions">
          <Button 
            :label="$t('setup.strings.printedKit.generate')" 
            icon="pi pi-download" 
            @click="generatePrintedKit"
            :loading="generatingKit"
            severity="primary"
            class="w-full"
          />
        </div>
      </div>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import api from '@/api/api'

// PrimeVue Components
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Password from 'primevue/password'
import Checkbox from 'primevue/checkbox'

const { t, locale } = useI18n()
const toast = useToast()
const router = useRouter()

// Computed properties for arrays
const printedKitItems = computed(() => {
  const items = t('setup.strings.printedKit.info.items')
  return Array.isArray(items) ? items : []
})

const defaultTemplatesList = computed(() => {
  const items = t('setup.strings.printTemplates.defaultTemplatesList')
  return Array.isArray(items) ? items : []
})

// State
const smtpDialogVisible = ref(false)
const templatesDialogVisible = ref(false)
const printedKitDialogVisible = ref(false)
const smtpConfigured = ref(false)
const templatesConfigured = ref(false)
const testingConnection = ref(false)
const savingSmtp = ref(false)
const initializingTemplates = ref(false)
const generatingKit = ref(false)

const smtpConfig = ref({
  host: '',
  port: 587,
  username: '',
  password: '',
  from_email: '',
  use_tls: true,
  provider: 'smtp'
})

const kitOptions = ref({
  includeAssets: true,
  includeSites: true,
  includeContacts: true,
  includeSuppliers: true
})

// Methods
const loadSmtpConfig = async () => {
  try {
    const response = await api.getSMTPConfig()
    if (response.data) {
      smtpConfig.value = response.data
      smtpConfigured.value = true
    }
  } catch (error) {
    // SMTP not configured
  }
}

const checkTemplatesStatus = async () => {
  try {
    const response = await api.getPrintTemplates()
    templatesConfigured.value = response.data && response.data.length > 0
  } catch (error) {
    templatesConfigured.value = false
  }
}

const saveSmtpConfig = async () => {
  try {
    savingSmtp.value = true
    // Validazione base
    if (!smtpConfig.value.host || !smtpConfig.value.port || !smtpConfig.value.from_email) {
      toast.add({
        severity: 'warn',
        summary: t('common.messages.warning'),
        detail: 'Compila tutti i campi obbligatori (Host, Porta, From Email)',
        life: 3000
      })
      savingSmtp.value = false
      return
    }
    await api.setSMTPConfig(smtpConfig.value)
    smtpConfigured.value = true
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: t('setup.messages.smtpSaved'),
      life: 3000
    })
    smtpDialogVisible.value = false
  } catch (error) {
    console.error('Error saving SMTP config:', error)
    const errorMessage = error.response?.data?.detail || t('setup.messages.smtpSaveError')
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: errorMessage,
      life: 5000
    })
  } finally {
    savingSmtp.value = false
  }
}

const testSmtpConnection = async () => {
  try {
    testingConnection.value = true
    await api.testSMTPConfig(smtpConfig.value)
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: t('setup.messages.smtpTestSuccess'),
      life: 3000
    })
  } catch (error) {
    console.error('Error testing SMTP connection:', error)
    const errorMessage = error.response?.data?.detail || t('setup.messages.smtpTestError')
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: errorMessage,
      life: 5000
    })
  } finally {
    testingConnection.value = false
  }
}

const initDefaultTemplates = async () => {
  try {
    initializingTemplates.value = true
    const response = await api.initDefaultTemplates()
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: t('setup.strings.printTemplates.templatesInitialized'),
      life: 3000
    })
    templatesConfigured.value = true
    templatesDialogVisible.value = false
  } catch (error) {
    if (error.response?.status === 400) {
      toast.add({
        severity: 'warn',
        summary: t('common.messages.warning'),
        detail: t('setup.strings.printTemplates.templatesAlreadyExist'),
        life: 3000
      })
      templatesConfigured.value = true
    } else {
      toast.add({
        severity: 'error',
        summary: t('common.messages.error'),
        detail: t('setup.strings.printTemplates.templatesInitError'),
        life: 3000
      })
    }
  } finally {
    initializingTemplates.value = false
  }
}

const generatePrintedKit = async () => {
  try {
    generatingKit.value = true
    
    // Include current language in options
    const options = {
      ...kitOptions.value,
      language: locale.value || 'en'
    }
    
    const response = await api.generatePrintedKit(options)
    
    // Download the generated file
    if (response.data.file_url) {
      // Extract filename from URL
      const filename = response.data.file_url.split('/').pop()
      
      // Download file using API
      const downloadResponse = await api.downloadPrintedKit(filename)
      
      // Create blob and download
      const blob = new Blob([downloadResponse.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    }
    
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: t('setup.strings.printedKit.success'),
      life: 3000
    })
    printedKitDialogVisible.value = false
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: t('setup.strings.printedKit.error'),
      life: 3000
    })
  } finally {
    generatingKit.value = false
  }
}

const goToSSO = () => {
  router.push('/sso-config')
}

const goToUsers = () => {
  router.push('/users')
}

const goToRoles = () => {
  router.push('/roles')
}

const goToNotifications = () => {
  router.push('/notifications')
}

const goToVulnerabilityFeeds = () => {
  router.push('/vulnerability-feeds')
}

const openSmtpDialog = () => {
  smtpDialogVisible.value = true
}

const openTemplatesDialog = () => {
  templatesDialogVisible.value = true
}

const openPrintedKitDialog = () => {
  printedKitDialogVisible.value = true
}

// Lifecycle
onMounted(() => {
  loadSmtpConfig()
  checkTemplatesStatus()
})
</script>

<style scoped>
.setup-page {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.setup-header {
  text-align: center;
  margin-bottom: 3rem;
}

.setup-header h1 {
  font-size: 2.5rem;
  color: var(--primary-color);
  margin-bottom: 0.5rem;
}

.setup-description {
  font-size: 1.1rem;
  color: var(--text-color-secondary);
}

.setup-tiles {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.setup-tile {
  background: var(--surface-card);
  border: 1px solid var(--surface-border);
  border-radius: 12px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 1rem;
  position: relative;
}

.setup-tile:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  border-color: var(--primary-color);
}

.setup-tile.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.setup-tile.disabled:hover {
  transform: none;
  box-shadow: none;
  border-color: var(--surface-border);
}

.tile-icon {
  width: 60px;
  height: 60px;
  background: var(--primary-color);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.5rem;
}

.tile-content {
  flex: 1;
}

.tile-content h3 {
  margin: 0 0 0.5rem 0;
  color: var(--text-color);
  font-size: 1.2rem;
}

.tile-content p {
  margin: 0;
  color: var(--text-color-secondary);
  font-size: 0.9rem;
  line-height: 1.4;
}

.tile-status {
  color: var(--text-color-secondary);
  font-size: 1.2rem;
}

.tile-status.configured {
  color: var(--green-500);
}

.setup-dialog {
  border-radius: 12px;
}

.smtp-form {
  padding: 1rem 0;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-field label {
  font-weight: 600;
  color: var(--text-color);
}

.checkbox-field {
  justify-content: center;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid var(--surface-border);
}

/* Templates semplificati */
.templates-simple {
  padding: 1rem 0;
}

.templates-info {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 2rem;
  padding: 1rem;
  background: var(--surface-50);
  border-radius: 8px;
}

.templates-info p {
  margin: 0 0 0.5rem 0;
  font-weight: 600;
}

.templates-info ul {
  margin: 0;
  padding-left: 1.5rem;
}

.templates-info li {
  margin-bottom: 0.25rem;
}

.templates-actions {
  text-align: center;
}

/* Printed Kit */
.printed-kit {
  padding: 1rem 0;
}

.kit-info {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 2rem;
  padding: 1rem;
  background: var(--surface-50);
  border-radius: 8px;
}

.kit-info p {
  margin: 0 0 0.5rem 0;
  font-weight: 600;
}

.kit-info ul {
  margin: 0;
  padding-left: 1.5rem;
}

.kit-info li {
  margin-bottom: 0.25rem;
}

.kit-options {
  margin-bottom: 2rem;
}

.kit-options h4 {
  margin: 0 0 1rem 0;
  color: var(--text-color);
}

.option-item {
  margin-bottom: 0.75rem;
}

.kit-actions {
  text-align: center;
}

@media (max-width: 768px) {
  .setup-page {
    padding: 1rem;
  }
  
  .setup-tiles {
    grid-template-columns: 1fr;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .form-actions {
    flex-direction: column;
  }
}
</style> 