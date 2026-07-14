<template>
  <div class="login-container">
    <!-- Background con pattern geometrico -->
    <div class="login-background">
      <div class="background-pattern"></div>
      <div class="background-overlay"></div>
    </div>

    <!-- Container principale -->
    <div class="login-content">
      <!-- Logo e titolo -->
      <div class="login-brand">
        <div class="logo-container">
          <img src="@/static/logo_black.png" alt="Industrace" class="login-logo" />
          <div class="logo-glow"></div>
        </div>
        <h1 class="brand-title">{{ $t('login.title') }}</h1>
        <p class="brand-subtitle">{{ $t('login.strings.welcomeMessage') }}</p>
      </div>

      <!-- Form di login -->
      <div class="login-form-container">
        <div class="form-card">
          <div class="form-header">
            <h2>{{ $t('login.strings.signIn') }}</h2>
            <p>{{ $t('login.strings.enterCredentials') }}</p>
          </div>

          <form @submit.prevent="handleSubmit" class="login-form">
            <div class="form-group">
              <label for="email" class="form-label">
                <i class="pi pi-envelope"></i>
                {{ $t('login.strings.email') }}
              </label>
              <div class="input-wrapper">
                <InputText 
                  id="email" 
                  v-model="email" 
                  type="email" 
                  required 
                  class="form-input"
                  :placeholder="$t('login.strings.emailPlaceholder')"
                  :class="{ 'p-invalid': emailError }"
                />
                <div class="input-icon">
                  <i class="pi pi-envelope"></i>
                </div>
              </div>
              <small v-if="emailError" class="error-message">{{ emailError }}</small>
            </div>

            <div class="form-group">
              <label for="password_input" class="form-label">
                <i class="pi pi-lock"></i>
                {{ $t('login.strings.password') }}
              </label>
              <div class="input-wrapper">
                <Password 
                  id="password" 
                  v-model="password" 
                  :feedback="false" 
                  required 
                  toggleMask 
                  class="form-input"
                  :placeholder="$t('login.strings.passwordPlaceholder')"
                  :class="{ 'p-invalid': passwordError }"
                  inputId="password_input"
                />
                <div class="input-icon">
                  <i class="pi pi-lock"></i>
                </div>
              </div>
              <small v-if="passwordError" class="error-message">{{ passwordError }}</small>
            </div>

            <div class="form-options">
              <div class="remember-me">
                <Checkbox 
                  v-model="rememberMe" 
                  :binary="true" 
                  :inputId="'remember'"
                />
                <label for="remember" class="checkbox-label">{{ $t('login.strings.rememberMe') }}</label>
              </div>
            </div>

            <Button 
              type="submit" 
              :label="$t('login.strings.submit')" 
              :loading="loading" 
              class="login-button"
              :disabled="!isFormValid"
            />

            <!-- SSO Login Button -->
            <div v-if="ssoEnabled" class="sso-section">
              <div class="divider">
                <span>{{ $t('login.strings.or') }}</span>
              </div>
              <Button 
                :label="ssoButtonLabel" 
                :icon="ssoProvider.value === 'google' ? 'pi pi-google' : ssoProvider.value === 'okta' ? 'pi pi-key' : 'pi pi-microsoft'"
                @click="handleSSOLogin"
                class="sso-button"
                :loading="ssoLoading"
              />
            </div>

          </form>
        </div>
      </div>
    </div>

    <!-- Toast per notifiche -->
    <Toast position="top-right" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { useAuthStore } from '../store/auth'
import { useI18n } from 'vue-i18n'
import api from '../api/api'

import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import Toast from 'primevue/toast'

const email = ref('')
const password = ref('')
const rememberMe = ref(false)
const loading = ref(false)

const emailError = ref('')
const passwordError = ref('')

const ssoEnabled = ref(false)
const ssoProvider = ref(null)
const ssoLoading = ref(false)

const toast = useToast()
const authStore = useAuthStore()
const router = useRouter()
const { t } = useI18n()

// Check SSO availability on mount
onMounted(async () => {
  try {
    const response = await api.checkSSOEnabled()
    ssoEnabled.value = response.data.enabled || false
    ssoProvider.value = response.data.provider || null
  } catch (error) {
    console.error('Error checking SSO availability:', error)
    ssoEnabled.value = false
  }
})

const ssoButtonLabel = computed(() => {
  if (ssoProvider.value === 'azure_ad') {
    return t('login.strings.loginWithMicrosoft')
  } else if (ssoProvider.value === 'google') {
    return t('login.strings.loginWithGoogle')
  } else if (ssoProvider.value === 'okta') {
    return t('login.strings.loginWithOkta')
  }
  return t('login.strings.loginWithSSO')
})

const handleSSOLogin = () => {
  ssoLoading.value = true
  try {
    // Redirect directly to SSO authorization endpoint
    // The backend will handle tenant detection and redirect to provider
    const provider = ssoProvider.value || 'azure_ad'
    window.location.href = `/api/auth/sso/${provider}/authorize`
  } catch (error) {
    console.error('SSO login error:', error)
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: error.response?.data?.detail || t('login.messages.ssoError'),
      life: 5000
    })
    ssoLoading.value = false
  }
}


// Validazione form
const isFormValid = computed(() => {
  return email.value.trim() !== '' && password.value.trim() !== ''
})

// Validazione email
const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

const handleSubmit = async () => {
  // Reset errori
  emailError.value = ''
  passwordError.value = ''

  // Validazione
  if (!email.value.trim()) {
    emailError.value = t('login.messages.emailRequired')
    return
  }

  if (!validateEmail(email.value)) {
    emailError.value = t('login.messages.emailInvalid')
    return
  }

  if (!password.value.trim()) {
    passwordError.value = t('login.messages.passwordRequired')
    return
  }

  loading.value = true
  try {
    await authStore.login(email.value, password.value)
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: t('login.messages.success'),
      life: 3000
    })
    router.push('/')
  } catch (error) {
    const errorCode = error.response?.data?.error_code
    const errorDetail = error.response?.data?.detail
    let message = t('login.messages.error')

    // Gestione specifica per SSO_REQUIRED
    if (errorCode === 'SSO_REQUIRED') {
      message = errorDetail || t('login.messages.ssoRequired')
      toast.add({
        severity: 'warn',
        summary: t('login.messages.ssoRequiredTitle'),
        detail: message,
        life: 7000
      })
      // Opzionalmente, potresti reindirizzare al login SSO qui
      // router.push('/auth/sso/azure_ad/authorize')
      return
    }

    // Prova a ottenere la traduzione specifica per il codice di errore
    if (errorCode) {
      const translatedError = t(`core.${errorCode}`)
      // Se la traduzione esiste e non è uguale alla chiave, usala
      if (translatedError && translatedError !== `core.${errorCode}`) {
        message = translatedError
      } else if (errorDetail) {
        message = errorDetail
      }
    }

    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: message,
      life: 5000
    })
  } finally {
    loading.value = false
  }
}


</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}

/* Background con pattern */
.login-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1;
}

.background-pattern {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    radial-gradient(circle at 25% 25%, rgba(102, 126, 234, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 75% 75%, rgba(118, 75, 162, 0.03) 0%, transparent 50%),
    linear-gradient(45deg, transparent 40%, rgba(102, 126, 234, 0.02) 50%, transparent 60%);
  animation: backgroundFloat 20s ease-in-out infinite;
}

.background-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.1);
}

@keyframes backgroundFloat {
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  50% { transform: translateY(-20px) rotate(1deg); }
}

/* Container principale */
.login-content {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
  max-width: 1200px;
  width: 100%;
  padding: 2rem;
}

/* Brand section */
.login-brand {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 1rem;
}

.logo-container {
  position: relative;
  display: inline-block;
  margin-bottom: 1rem;
}

.login-logo {
  width: 100px;
  height: auto;
  filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));
  transition: transform 0.3s ease;
}

.login-logo:hover {
  transform: scale(1.05);
}

.logo-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 120px;
  height: 120px;
  background: radial-gradient(circle, rgba(102, 126, 234, 0.1) 0%, transparent 70%);
  border-radius: 50%;
  animation: logoGlow 3s ease-in-out infinite alternate;
}

@keyframes logoGlow {
  0% { opacity: 0.5; transform: translate(-50%, -50%) scale(1); }
  100% { opacity: 1; transform: translate(-50%, -50%) scale(1.1); }
}

.brand-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
  text-shadow: 0 2px 4px rgba(0,0,0,0.1);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-subtitle {
  font-size: 1.1rem;
  margin: 0;
  color: #64748b;
  font-weight: 400;
}

/* Form container */
.login-form-container {
  width: 100%;
  max-width: 450px;
}

.form-card {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 2.5rem;
  box-shadow: 
    0 20px 40px rgba(0,0,0,0.08),
    0 0 0 1px rgba(255,255,255,0.8);
  border: 1px solid rgba(226, 232, 240, 0.8);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.form-card:hover {
  transform: translateY(-5px);
  box-shadow: 
    0 25px 50px rgba(0,0,0,0.12),
    0 0 0 1px rgba(255,255,255,0.9);
}

.form-header {
  text-align: center;
  margin-bottom: 2rem;
}

.form-header h2 {
  font-size: 1.8rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 0.5rem 0;
}

.form-header p {
  color: #64748b;
  margin: 0;
  font-size: 0.95rem;
}

/* Form groups */
.form-group {
  margin-bottom: 1.5rem;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  color: #2c3e50;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.form-label i {
  color: #667eea;
  font-size: 0.8rem;
}

.input-wrapper {
  position: relative;
}

.form-input {
  width: 100%;
  padding: 1rem 1rem 1rem 3rem;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 1rem;
  transition: all 0.3s ease;
  background: rgba(255,255,255,0.95);
}

.form-input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  outline: none;
}

.form-input.p-invalid {
  border-color: #e74c3c;
  box-shadow: 0 0 0 3px rgba(231, 76, 60, 0.1);
}

.input-icon {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: #667eea;
  z-index: 2;
}

.error-message {
  color: #e74c3c;
  font-size: 0.8rem;
  margin-top: 0.25rem;
  display: block;
}

/* Form options */
.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  font-size: 0.9rem;
}

.remember-me {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.checkbox-label {
  color: #64748b;
  cursor: pointer;
}

.forgot-password {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;
}

.forgot-password:hover {
  color: #5a6fd8;
}

/* Buttons */
.login-button {
  width: 100%;
  padding: 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 1rem;
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Divider */
.divider {
  text-align: center;
  margin: 1.5rem 0;
  position: relative;
}

.divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: #e1e8ed;
}

.divider span {
  background: rgba(255,255,255,0.98);
  padding: 0 1rem;
  color: #64748b;
  font-size: 0.9rem;
}

/* SSO Section */
.sso-section {
  margin-top: 1.5rem;
}

.sso-button {
  width: 100%;
  padding: 1rem;
  background: #0078d4;
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.sso-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 120, 212, 0.3);
  background: #106ebe;
}

.sso-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}



/* Form footer */
.form-footer {
  text-align: center;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e2e8f0;
  color: #64748b;
  font-size: 0.9rem;
}

.signup-link {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;
}

.signup-link:hover {
  color: #5a6fd8;
}

/* Responsive */
@media (max-width: 768px) {
  .login-content {
    padding: 1rem;
  }
  
  .form-card {
    padding: 2rem;
  }
  
  .brand-title {
    font-size: 2rem;
  }
  
  .form-options {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
}

/* Animazioni di entrata */
.form-card {
  animation: slideInUp 0.6s ease-out;
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Stili per PrimeVue components */
:deep(.p-password) {
  width: 100%;
}

:deep(.p-password-input) {
  width: 100%;
  padding: 1rem 1rem 1rem 3rem;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 1rem;
  transition: all 0.3s ease;
  background: rgba(255,255,255,0.95);
}

:deep(.p-password-input:focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  outline: none;
}

:deep(.p-password-input.p-invalid) {
  border-color: #e74c3c;
  box-shadow: 0 0 0 3px rgba(231, 76, 60, 0.1);
}

:deep(.p-checkbox) {
  margin-right: 0.5rem;
}

:deep(.p-checkbox .p-checkbox-box) {
  border-radius: 4px;
  border-color: #667eea;
}

:deep(.p-checkbox .p-checkbox-box.p-highlight) {
  background: #667eea;
  border-color: #667eea;
}
</style>
