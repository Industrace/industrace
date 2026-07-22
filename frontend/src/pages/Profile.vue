<!--
  - Profile.vue
  - Componente per la gestione del profilo utente
  - Permette di visualizzare informazioni e resettare la password
-->
<template>
  <div class="profile-page">
    <div class="page-header">
      <h1>{{ t('profile.title') }}</h1>
    </div>

    <div class="grid">
      <!-- Informazioni utente -->
      <div class="col-12 lg:col-6">
        <Card>
          <template #title>
            <div class="flex align-items-center gap-2">
              <i class="pi pi-user"></i>
              {{ t('profile.strings.userInfo') }}
            </div>
          </template>
          <template #content>
            <div class="grid">
              <div class="col-12">
                <div class="field">
                  <label class="block text-sm font-medium mb-2">{{ t('profile.fields.fullName') }}</label>
                  <div class="p-3 bg-gray-50 border-round">
                    {{ user.full_name || t('common.strings.na') }}
                  </div>
                </div>
              </div>
              <div class="col-12">
                <div class="field">
                  <label class="block text-sm font-medium mb-2">{{ t('common.fields.email') }}</label>
                  <div class="p-3 bg-gray-50 border-round">
                    {{ user.email }}
                  </div>
                </div>
              </div>
              <div class="col-12">
                <div class="field">
                  <label class="block text-sm font-medium mb-2">{{ t('profile.fields.role') }}</label>
                  <div class="p-3 bg-gray-50 border-round">
                    {{ user.role?.name || t('common.strings.na') }}
                  </div>
                </div>
              </div>
              <div class="col-12">
                <div class="field">
                  <label class="block text-sm font-medium mb-2">{{ t('profile.fields.tenant') }}</label>
                  <div class="p-3 bg-gray-50 border-round">
                    {{ user.tenant?.name || t('common.strings.na') }}
                  </div>
                </div>
              </div>
              <div class="col-12">
                <div class="field">
                  <label class="block text-sm font-medium mb-2">{{ t('profile.fields.lastLogin') }}</label>
                  <div class="p-3 bg-gray-50 border-round">
                    {{ formatDate(user.last_login) }}
                  </div>
                </div>
              </div>
            </div>
          </template>
        </Card>
      </div>

      <!-- Reset Password -->
      <div class="col-12 lg:col-6">
        <Card>
          <template #title>
            <div class="flex align-items-center gap-2">
              <i class="pi pi-lock"></i>
              {{ t('profile.strings.security') }}
            </div>
          </template>
          <template #content>
            <div class="mb-4">
              <p class="text-sm text-gray-600 mb-3">
                {{ t('profile.strings.resetPasswordInfo') }}
              </p>
            </div>
            
            <form @submit.prevent="resetPassword" class="space-y-4">
              <div class="field">
                <label class="block text-sm font-medium mb-2">{{ t('profile.fields.currentPassword') }}</label>
                <Password 
                  v-model="passwordForm.currentPassword" 
                  :placeholder="t('profile.strings.enterCurrentPassword')"
                  :feedback="false"
                  toggleMask
                  class="w-full"
                  :class="{ 'p-invalid': passwordErrors.currentPassword }"
                />
                <small v-if="passwordErrors.currentPassword" class="p-error">
                  {{ passwordErrors.currentPassword }}
                </small>
              </div>

              <div class="field">
                <label class="block text-sm font-medium mb-2">{{ t('profile.fields.newPassword') }}</label>
                <Password 
                  v-model="passwordForm.newPassword" 
                  :placeholder="t('profile.strings.enterNewPassword')"
                  toggleMask
                  class="w-full"
                  :class="{ 'p-invalid': passwordErrors.newPassword }"
                />
                <small v-if="passwordErrors.newPassword" class="p-error">
                  {{ passwordErrors.newPassword }}
                </small>
              </div>

              <div class="field">
                <label class="block text-sm font-medium mb-2">{{ t('profile.fields.confirmPassword') }}</label>
                <Password 
                  v-model="passwordForm.confirmPassword" 
                  :placeholder="t('profile.strings.confirmNewPassword')"
                  :feedback="false"
                  toggleMask
                  class="w-full"
                  :class="{ 'p-invalid': passwordErrors.confirmPassword }"
                />
                <small v-if="passwordErrors.confirmPassword" class="p-error">
                  {{ passwordErrors.confirmPassword }}
                </small>
              </div>

              <div class="flex gap-2">
                <Button 
                  type="submit" 
                  :label="t('profile.fields.resetPassword')" 
                  icon="pi pi-key"
                  :loading="resetting"
                  :disabled="!isPasswordFormValid"
                />
                <Button 
                  type="button" 
                  :label="t('common.actions.clear')" 
                  severity="secondary"
                  @click="clearPasswordForm"
                />
              </div>
            </form>
          </template>
        </Card>
      </div>

      <!-- Impostazioni -->
      <div class="col-12">
        <Card>
          <template #title>
            <div class="flex align-items-center gap-2">
              <i class="pi pi-cog"></i>
              {{ t('profile.fields.settings') }}
            </div>
          </template>
          <template #content>
            <div class="p-fluid">
              <div class="field">
                <div class="flex align-items-center justify-content-between">
                  <div class="flex flex-column gap-1">
                    <label class="block text-sm font-medium">{{ t('profile.fields.notificationsEnabled') }}</label>
                    <small class="text-color-secondary">{{ t('profile.strings.notificationsEnabledHelp') }}</small>
                  </div>
                  <InputSwitch 
                    v-model="user.notifications_enabled" 
                    @update:modelValue="updateNotificationsPreference"
                    :loading="updatingNotifications"
                  />
                </div>
              </div>
            </div>
          </template>
        </Card>
      </div>

      <!-- MFA -->
      <div class="col-12">
        <Card>
          <template #title>
            <div class="flex align-items-center gap-2">
              <i class="pi pi-shield"></i>
              {{ t('mfa.title') }}
            </div>
          </template>
          <template #content>
            <div v-if="mfaStatusLoading" class="text-color-secondary">…</div>
            <div v-else-if="showSetupWizard">
              <MfaSetupWizard @done="onMfaDone" @cancel="showSetupWizard = false" />
            </div>
            <div v-else-if="showDisableForm" class="p-fluid">
              <p class="mb-3">{{ t('mfa.disableConfirm') }}</p>
              <div class="field">
                <label>{{ t('mfa.password') }}</label>
                <Password v-model="disableForm.password" :feedback="false" toggleMask class="w-full" />
              </div>
              <div class="field">
                <label>{{ t('mfa.code') }}</label>
                <InputText v-model="disableForm.code" maxlength="6" class="w-full" />
              </div>
              <div class="flex gap-2">
                <Button :label="t('mfa.disable')" severity="danger" :loading="mfaLoading" @click="disableMfa" />
                <Button :label="t('common.actions.cancel')" severity="secondary" @click="showDisableForm = false" />
              </div>
            </div>
            <div v-else-if="mfaStatus">
              <p class="mb-3">
                {{ mfaStatus.totp_enabled ? t('mfa.statusEnabled') : t('mfa.statusDisabled') }}
              </p>
              <p v-if="mfaStatus.totp_enabled" class="text-color-secondary mb-3">
                {{ t('mfa.remainingCodes', { count: mfaStatus.backup_codes_remaining }) }}
              </p>
              <div class="flex gap-2 flex-wrap">
                <Button
                  v-if="!mfaStatus.totp_enabled"
                  :label="t('mfa.enable')"
                  icon="pi pi-lock"
                  @click="showSetupWizard = true"
                />
                <template v-else>
                  <Button
                    v-if="mfaStatus.can_self_disable"
                    :label="t('mfa.disable')"
                    icon="pi pi-unlock"
                    severity="danger"
                    outlined
                    @click="showDisableForm = true"
                  />
                  <Button
                    :label="t('mfa.regenerateBackupCodes')"
                    icon="pi pi-refresh"
                    severity="secondary"
                    outlined
                    @click="startRegenerate"
                  />
                </template>
              </div>
              <div v-if="showRegenForm" class="mt-3 p-fluid">
                <label>{{ t('mfa.code') }}</label>
                <InputText v-model="regenCode" maxlength="6" class="w-full mb-2" />
                <Button :label="t('mfa.regenerateBackupCodes')" :loading="mfaLoading" @click="regenerateCodes" />
                <BackupCodesDisplay v-if="regenCodes.length" class="mt-3" :codes="regenCodes" />
              </div>
            </div>
          </template>
        </Card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import i18n from '../locales/loader-final.js'
import { useToast } from 'primevue/usetoast'
import { useApi } from '../composables/useApi'
import api from '../api/api'

import Card from 'primevue/card'
import Button from 'primevue/button'
import Password from 'primevue/password'
import InputSwitch from 'primevue/inputswitch'
import InputText from 'primevue/inputtext'
import MfaSetupWizard from '@/components/mfa/MfaSetupWizard.vue'
import BackupCodesDisplay from '@/components/mfa/BackupCodesDisplay.vue'

const { t } = useI18n()
const toast = useToast()
const { loading, execute } = useApi()

// Data
const user = ref({})
const resetting = ref(false)
const updatingNotifications = ref(false)
const mfaStatus = ref(null)
const mfaStatusLoading = ref(false)
const showSetupWizard = ref(false)
const showDisableForm = ref(false)
const showRegenForm = ref(false)
const mfaLoading = ref(false)
const disableForm = ref({ password: '', code: '' })
const regenCode = ref('')
const regenCodes = ref([])

// Password form
const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordErrors = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// Computed
const isPasswordFormValid = computed(() => {
  return passwordForm.value.currentPassword && 
         passwordForm.value.newPassword && 
         passwordForm.value.confirmPassword &&
         passwordForm.value.newPassword === passwordForm.value.confirmPassword
})

// Methods
function formatDate(dateString) {
  if (!dateString) return t('common.strings.na')
  const locale = i18n.global.locale.value;
  const dateLocale = locale === 'it' ? 'it-IT' : 'en-US';
  return new Date(dateString).toLocaleString(dateLocale)
}

function clearPasswordErrors() {
  passwordErrors.value = {
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
}

function validatePasswordForm() {
  clearPasswordErrors()
  let isValid = true

  if (!passwordForm.value.currentPassword) {
    passwordErrors.value.currentPassword = t('profile.strings.currentPasswordRequired')
    isValid = false
  }

  if (!passwordForm.value.newPassword) {
    passwordErrors.value.newPassword = t('profile.strings.newPasswordRequired')
    isValid = false
  } else if (passwordForm.value.newPassword.length < 8) {
    passwordErrors.value.newPassword = t('profile.strings.passwordMinLength')
    isValid = false
  }

  if (!passwordForm.value.confirmPassword) {
    passwordErrors.value.confirmPassword = t('profile.strings.confirmPasswordRequired')
    isValid = false
  } else if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    passwordErrors.value.confirmPassword = t('profile.strings.passwordsDoNotMatch')
    isValid = false
  }

  return isValid
}

async function resetPassword() {
  if (!validatePasswordForm()) return

  resetting.value = true
  try {
    await execute(async () => {
      await api.changePassword({
        current_password: passwordForm.value.currentPassword,
        new_password: passwordForm.value.newPassword
      })
      
      clearPasswordForm()
      toast.add({
        severity: 'success',
        summary: t('common.messages.success'),
        detail: t('profile.strings.passwordResetSuccess'),
        life: 3000
      })
    }, {
      errorContext: t('profile.strings.passwordResetError')
    })
  } finally {
    resetting.value = false
  }
}

function clearPasswordForm() {
  passwordForm.value = {
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
  clearPasswordErrors()
}

async function updateNotificationsPreference(enabled) {
  updatingNotifications.value = true
  try {
    await execute(async () => {
      const response = await api.updateNotificationsPreference(enabled)
      // Update local user state with response
      if (response.data) {
        user.value.notifications_enabled = response.data.notifications_enabled
      }
      toast.add({
        severity: 'success',
        summary: t('common.messages.success'),
        detail: t('profile.strings.notificationsUpdated'),
        life: 3000
      })
    }, {
      errorContext: t('profile.strings.notificationsUpdateError')
    })
  } catch (error) {
    // Revert the switch if update failed
    user.value.notifications_enabled = !enabled
    console.error('Error updating notifications preference:', error)
  } finally {
    updatingNotifications.value = false
  }
}

async function fetchUserProfile() {
  await execute(async () => {
    const response = await api.getCurrentUser()
    user.value = response.data
    return response
  }, {
    errorContext: t('profile.strings.fetchError')
  })
}

async function fetchMfaStatus() {
  mfaStatusLoading.value = true
  try {
    const res = await api.getMfaStatus()
    mfaStatus.value = res.data
  } catch (e) {
    mfaStatus.value = null
  } finally {
    mfaStatusLoading.value = false
  }
}

async function onMfaDone() {
  showSetupWizard.value = false
  await fetchMfaStatus()
}

async function disableMfa() {
  mfaLoading.value = true
  try {
    await api.mfaDisable(disableForm.value.password, disableForm.value.code)
    showDisableForm.value = false
    disableForm.value = { password: '', code: '' }
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: t('mfa.disabledSuccess'),
      life: 3000
    })
    await fetchMfaStatus()
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: error.response?.data?.detail || t('mfa.invalidCode'),
      life: 4000
    })
  } finally {
    mfaLoading.value = false
  }
}

function startRegenerate() {
  showRegenForm.value = true
  regenCode.value = ''
  regenCodes.value = []
}

async function regenerateCodes() {
  mfaLoading.value = true
  try {
    const res = await api.mfaRegenerateBackupCodes(regenCode.value)
    regenCodes.value = res.data.backup_codes || []
    await fetchMfaStatus()
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: error.response?.data?.detail || t('mfa.invalidCode'),
      life: 4000
    })
  } finally {
    mfaLoading.value = false
  }
}

onMounted(async () => {
  await fetchUserProfile()
  await fetchMfaStatus()
})
</script>

<style scoped>
.profile-page {
  padding: 1rem;
}

.page-header {
  margin-bottom: 1.5rem;
}

.space-y-4 > * + * {
  margin-top: 1rem;
}
</style> 