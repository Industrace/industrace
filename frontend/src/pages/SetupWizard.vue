<template>
  <div class="setup-wizard">
    <div class="setup-container">
      <!-- Header -->
      <div class="setup-header">
        <img src="@/static/logo.png" alt="Industrace" class="logo" />
        <h1>{{ t('setup.welcome') }}</h1>
        <p>{{ t('setup.description') }}</p>
      </div>

      <!-- Progress Steps -->
      <div class="setup-progress">
        <div 
          v-for="(step, index) in steps" 
          :key="index"
          class="step"
          :class="{ 
            'active': currentStep === index,
            'completed': currentStep > index,
            'disabled': currentStep < index
          }"
        >
          <div class="step-number">{{ index + 1 }}</div>
          <div class="step-label">{{ step.label }}</div>
        </div>
      </div>

      <!-- Step Content -->
      <div class="setup-content">
        <!-- Step 1: System Check -->
        <div v-if="currentStep === 0" class="step-content">
          <h2>{{ t('setup.systemCheck.title') }}</h2>
          <p>{{ t('setup.systemCheck.description') }}</p>
          
          <div class="check-list">
            <div class="check-item" :class="{ 'success': systemStatus.database_connected, 'error': !systemStatus.database_connected }">
              <i :class="systemStatus.database_connected ? 'pi pi-check-circle' : 'pi pi-times-circle'"></i>
              <span>{{ t('setup.systemCheck.database') }}</span>
            </div>
            <div class="check-item" :class="{ 'success': !systemStatus.is_configured, 'error': systemStatus.is_configured }">
              <i :class="!systemStatus.is_configured ? 'pi pi-check-circle' : 'pi pi-times-circle'"></i>
              <span>{{ t('setup.systemCheck.freshInstall') }}</span>
            </div>
          </div>

          <div v-if="systemStatus.error" class="error-message">
            <i class="pi pi-exclamation-triangle"></i>
            {{ systemStatus.error }}
          </div>

          <div class="step-actions">
            <Button 
              :label="t('setup.refresh')" 
              icon="pi pi-refresh" 
              @click="checkSystemStatus"
              :loading="loading"
            />
            <Button 
              :label="t('setup.next')" 
              icon="pi pi-arrow-right" 
              @click="nextStep"
              :disabled="!canProceed"
            />
          </div>
        </div>

        <!-- Step 2: Organization Setup -->
        <div v-if="currentStep === 1" class="step-content">
          <h2>{{ t('setup.organization.title') }}</h2>
          <p>{{ t('setup.organization.description') }}</p>
          
          <div class="form-grid">
            <div class="form-group">
              <label>{{ t('setup.organization.name') }} *</label>
              <InputText 
                v-model="setupData.tenant_name" 
                :placeholder="t('setup.organization.namePlaceholder')"
                :class="{ 'p-invalid': errors.tenant_name }"
              />
              <small v-if="errors.tenant_name" class="p-error">{{ errors.tenant_name }}</small>
            </div>
            
            <div class="form-group">
              <label>{{ t('setup.organization.slug') }} *</label>
              <InputText 
                v-model="setupData.tenant_slug" 
                :placeholder="t('setup.organization.slugPlaceholder')"
                :class="{ 'p-invalid': errors.tenant_slug }"
              />
              <small v-if="errors.tenant_slug" class="p-error">{{ errors.tenant_slug }}</small>
            </div>
            
            <div class="form-group">
              <label>{{ t('setup.organization.language') }}</label>
              <Dropdown 
                v-model="setupData.language" 
                :options="languages" 
                optionLabel="label" 
                optionValue="value"
                :placeholder="t('setup.organization.languagePlaceholder')"
              />
            </div>
          </div>

          <div class="modules-section">
            <h3>{{ t('setup.strings.features.title') }}</h3>
            <p class="modules-hint">{{ t('setup.strings.features.help') }}</p>
            <label class="module-toggle">
              <InputSwitch v-model="setupData.iec62443_enabled" inputId="wizard_iec62443" />
              <span>{{ t('setup.strings.features.iec62443') }}</span>
            </label>
            <small class="module-detail">{{ t('setup.strings.features.iec62443Hint') }}</small>
          </div>

          <div class="step-actions">
            <Button 
              :label="t('setup.back')" 
              icon="pi pi-arrow-left" 
              class="p-button-secondary"
              @click="previousStep"
            />
            <Button 
              :label="t('setup.next')" 
              icon="pi pi-arrow-right" 
              @click="nextStep"
              :disabled="!canProceed"
            />
          </div>
        </div>

        <!-- Step 3: Admin Account -->
        <div v-if="currentStep === 2" class="step-content">
          <h2>{{ t('setup.admin.title') }}</h2>
          <p>{{ t('setup.admin.description') }}</p>
          
          <div class="form-grid">
            <div class="form-group">
              <label>{{ t('setup.admin.name') }} *</label>
              <InputText 
                v-model="setupData.admin_name" 
                :placeholder="t('setup.admin.namePlaceholder')"
                :class="{ 'p-invalid': errors.admin_name }"
              />
              <small v-if="errors.admin_name" class="p-error">{{ errors.admin_name }}</small>
            </div>
            
            <div class="form-group">
              <label>{{ t('setup.admin.email') }} *</label>
              <InputText 
                v-model="setupData.admin_email" 
                type="email"
                :placeholder="t('setup.admin.emailPlaceholder')"
                :class="{ 'p-invalid': errors.admin_email }"
              />
              <small v-if="errors.admin_email" class="p-error">{{ errors.admin_email }}</small>
            </div>
            
            <div class="form-group">
              <label>{{ t('setup.admin.password') }} *</label>
              <Password 
                v-model="setupData.admin_password" 
                :placeholder="t('setup.admin.passwordPlaceholder')"
                :class="{ 'p-invalid': errors.admin_password }"
                :feedback="false"
                toggleMask
              />
              <small v-if="errors.admin_password" class="p-error">{{ errors.admin_password }}</small>
            </div>
          </div>

          <div class="step-actions">
            <Button 
              :label="t('setup.back')" 
              icon="pi pi-arrow-left" 
              class="p-button-secondary"
              @click="previousStep"
            />
            <Button 
              :label="t('setup.next')" 
              icon="pi pi-arrow-right" 
              @click="nextStep"
              :disabled="!canProceed"
            />
          </div>
        </div>

        <!-- Step 4: Review & Install -->
        <div v-if="currentStep === 3" class="step-content">
          <h2>{{ t('setup.review.title') }}</h2>
          <p>{{ t('setup.review.description') }}</p>
          
          <div class="review-section">
            <h3>{{ t('setup.review.organization') }}</h3>
            <div class="review-item">
              <span class="label">{{ t('setup.organization.name') }}:</span>
              <span class="value">{{ setupData.tenant_name }}</span>
            </div>
            <div class="review-item">
              <span class="label">{{ t('setup.organization.slug') }}:</span>
              <span class="value">{{ setupData.tenant_slug }}</span>
            </div>
            <div class="review-item">
              <span class="label">{{ t('setup.organization.language') }}:</span>
              <span class="value">{{ getLanguageLabel(setupData.language) }}</span>
            </div>
            <div class="review-item">
              <span class="label">{{ t('setup.strings.features.iec62443') }}:</span>
              <span class="value">{{ setupData.iec62443_enabled ? t('setup.strings.features.enabled') : t('setup.strings.features.disabled') }}</span>
            </div>
          </div>
          
          <div class="review-section">
            <h3>{{ t('setup.review.admin') }}</h3>
            <div class="review-item">
              <span class="label">{{ t('setup.admin.name') }}:</span>
              <span class="value">{{ setupData.admin_name }}</span>
            </div>
            <div class="review-item">
              <span class="label">{{ t('setup.admin.email') }}:</span>
              <span class="value">{{ setupData.admin_email }}</span>
            </div>
          </div>

          <div class="step-actions">
            <Button 
              :label="t('setup.back')" 
              icon="pi pi-arrow-left" 
              class="p-button-secondary"
              @click="previousStep"
            />
            <Button 
              :label="t('setup.install')" 
              icon="pi pi-check" 
              class="p-button-success"
              @click="installSystem"
              :loading="installing"
            />
          </div>
        </div>

        <!-- Step 5: Success -->
        <div v-if="currentStep === 4" class="step-content">
          <div class="success-content">
            <i class="pi pi-check-circle success-icon"></i>
            <h2>{{ t('setup.success.title') }}</h2>
            <p>{{ t('setup.success.description') }}</p>
            
            <div class="credentials">
              <h3>{{ t('setup.success.credentials') }}</h3>
              <div class="credential-item">
                <span class="label">{{ t('setup.admin.email') }}:</span>
                <span class="value">{{ setupData.admin_email }}</span>
              </div>
              <div class="credential-item">
                <span class="label">{{ t('setup.admin.password') }}:</span>
                <span class="value">{{ setupData.admin_password }}</span>
              </div>
            </div>
            
            <div class="warning">
              <i class="pi pi-exclamation-triangle"></i>
              <span>{{ t('setup.success.warning') }}</span>
            </div>
          </div>

          <div class="step-actions">
            <Button 
              :label="t('setup.goToLogin')" 
              icon="pi pi-sign-in" 
              class="p-button-success"
              @click="goToLogin"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Dropdown from 'primevue/dropdown'
import InputSwitch from 'primevue/inputswitch'
import api from '@/api/api'

const { t } = useI18n()
const router = useRouter()
const toast = useToast()

// State
const currentStep = ref(0)
const loading = ref(false)
const installing = ref(false)
const systemStatus = reactive({
  is_configured: false,
  tenant_count: 0,
  user_count: 0,
  role_count: 0,
  database_connected: false,
  error: null
})

const setupData = reactive({
  tenant_name: '',
  tenant_slug: '',
  admin_name: '',
  admin_email: '',
  admin_password: '',
  language: 'en',
  iec62443_enabled: false
})

const errors = reactive({})

// Steps configuration
const steps = [
  { label: t('setup.steps.systemCheck') },
  { label: t('setup.steps.organization') },
  { label: t('setup.steps.admin') },
  { label: t('setup.steps.review') },
  { label: t('setup.steps.complete') }
]

const languages = [
  { label: 'English', value: 'en' },
  { label: 'Italiano', value: 'it' }
]

// Computed
const canProceed = computed(() => {
  switch (currentStep.value) {
    case 0:
      return systemStatus.database_connected && !systemStatus.is_configured
    case 1:
      return setupData.tenant_name && setupData.tenant_slug && !hasErrors()
    case 2:
      return setupData.admin_name && setupData.admin_email && setupData.admin_password && !hasErrors()
    case 3:
      return true
    default:
      return false
  }
})

// Methods
const checkSystemStatus = async () => {
  loading.value = true
  try {
    const response = await api.get('/setup/status')
    Object.assign(systemStatus, response.data)
  } catch (error) {
    systemStatus.error = error.response?.data?.detail || 'Connection failed'
    systemStatus.database_connected = false
  } finally {
    loading.value = false
  }
}

const validateStep = () => {
  errors.value = {}
  
  if (currentStep.value === 1) {
    if (!setupData.tenant_name) errors.tenant_name = t('setup.errors.required')
    if (!setupData.tenant_slug) errors.tenant_slug = t('setup.errors.required')
    if (setupData.tenant_slug && !/^[a-z0-9-_]+$/.test(setupData.tenant_slug)) {
      errors.tenant_slug = t('setup.errors.invalidSlug')
    }
  }
  
  if (currentStep.value === 2) {
    if (!setupData.admin_name) errors.admin_name = t('setup.errors.required')
    if (!setupData.admin_email) errors.admin_email = t('setup.errors.required')
    if (setupData.admin_email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(setupData.admin_email)) {
      errors.admin_email = t('setup.errors.invalidEmail')
    }
    if (!setupData.admin_password) errors.admin_password = t('setup.errors.required')
    if (setupData.admin_password && setupData.admin_password.length < 8) {
      errors.admin_password = t('setup.errors.passwordTooShort')
    }
  }
}

const hasErrors = () => {
  return Object.keys(errors.value).length > 0
}

const nextStep = () => {
  validateStep()
  if (!hasErrors() && canProceed.value) {
    currentStep.value++
  }
}

const previousStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const installSystem = async () => {
  installing.value = true
  try {
    const response = await api.post('/setup/initialize', setupData)
    if (response.data.success) {
      currentStep.value = 4
      toast.add({
        severity: 'success',
        summary: t('setup.success.title'),
        detail: t('setup.success.installed'),
        life: 5000
      })
    }
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: t('setup.errors.installationFailed'),
      detail: error.response?.data?.detail || 'Unknown error',
      life: 5000
    })
  } finally {
    installing.value = false
  }
}

const goToLogin = () => {
  router.push('/login')
}

const getLanguageLabel = (value) => {
  const lang = languages.find(l => l.value === value)
  return lang ? lang.label : value
}

// Lifecycle
onMounted(() => {
  checkSystemStatus()
})
</script>

<style scoped>
.setup-wizard {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.setup-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  max-width: 800px;
  width: 100%;
  overflow: hidden;
}

.setup-header {
  text-align: center;
  padding: 3rem 2rem 2rem;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

.logo {
  height: 60px;
  margin-bottom: 1rem;
}

.setup-header h1 {
  color: #2c3e50;
  margin-bottom: 0.5rem;
  font-size: 2rem;
}

.setup-header p {
  color: #6c757d;
  font-size: 1.1rem;
}

.setup-progress {
  display: flex;
  justify-content: center;
  padding: 2rem;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 0 1rem;
  position: relative;
}

.step:not(:last-child)::after {
  content: '';
  position: absolute;
  top: 20px;
  left: 100%;
  width: 2rem;
  height: 2px;
  background: #dee2e6;
  z-index: 1;
}

.step.completed:not(:last-child)::after {
  background: #28a745;
}

.step-number {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #dee2e6;
  color: #6c757d;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-bottom: 0.5rem;
  z-index: 2;
  position: relative;
}

.step.active .step-number {
  background: #007bff;
  color: white;
}

.step.completed .step-number {
  background: #28a745;
  color: white;
}

.step-label {
  font-size: 0.9rem;
  color: #6c757d;
  text-align: center;
}

.step.active .step-label {
  color: #007bff;
  font-weight: 600;
}

.step.completed .step-label {
  color: #28a745;
}

.setup-content {
  padding: 2rem;
}

.step-content h2 {
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.step-content p {
  color: #6c757d;
  margin-bottom: 2rem;
}

.check-list {
  margin-bottom: 2rem;
}

.check-item {
  display: flex;
  align-items: center;
  padding: 1rem;
  margin-bottom: 0.5rem;
  border-radius: 8px;
  background: #f8f9fa;
}

.check-item.success {
  background: #d4edda;
  color: #155724;
}

.check-item.error {
  background: #f8d7da;
  color: #721c24;
}

.check-item i {
  margin-right: 0.75rem;
  font-size: 1.2rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #2c3e50;
}

.modules-section {
  margin-bottom: 2rem;
  padding: 1.25rem 1.5rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.modules-section h3 {
  margin: 0 0 0.5rem;
  font-size: 1rem;
  color: #2c3e50;
}

.modules-hint {
  margin: 0 0 1rem;
  color: #6c757d;
  font-size: 0.9rem;
}

.module-toggle {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  font-weight: 500;
  color: #2c3e50;
}

.module-detail {
  display: block;
  margin-top: 0.5rem;
  margin-left: 3.25rem;
  color: #6c757d;
  font-size: 0.85rem;
}

.step-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 2rem;
  border-top: 1px solid #e9ecef;
}

.review-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.review-section h3 {
  color: #2c3e50;
  margin-bottom: 1rem;
  font-size: 1.1rem;
}

.review-item, .credential-item {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid #e9ecef;
}

.review-item:last-child, .credential-item:last-child {
  border-bottom: none;
}

.review-item .label, .credential-item .label {
  font-weight: 600;
  color: #6c757d;
}

.review-item .value, .credential-item .value {
  color: #2c3e50;
}

.success-content {
  text-align: center;
  padding: 2rem 0;
}

.success-icon {
  font-size: 4rem;
  color: #28a745;
  margin-bottom: 1rem;
}

.credentials {
  margin: 2rem 0;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 8px;
  text-align: left;
}

.warning {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: #fff3cd;
  color: #856404;
  border-radius: 8px;
  margin-top: 1rem;
}

.warning i {
  margin-right: 0.5rem;
}

.error-message {
  display: flex;
  align-items: center;
  padding: 1rem;
  background: #f8d7da;
  color: #721c24;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.error-message i {
  margin-right: 0.5rem;
}

@media (max-width: 768px) {
  .setup-wizard {
    padding: 1rem;
  }
  
  .setup-progress {
    flex-direction: column;
    align-items: center;
  }
  
  .step {
    margin: 0.5rem 0;
  }
  
  .step:not(:last-child)::after {
    display: none;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .step-actions {
    flex-direction: column;
    gap: 1rem;
  }
}
</style> 