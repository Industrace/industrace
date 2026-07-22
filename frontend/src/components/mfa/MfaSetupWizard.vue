<template>
  <div class="mfa-setup-wizard">
    <div v-if="step === 'qr'" class="step">
      <p>{{ t('mfa.setupScan') }}</p>
      <div class="qr-wrap" v-if="qrDataUrl">
        <img :src="qrDataUrl" alt="MFA QR code" width="200" height="200" />
      </div>
      <p class="manual">{{ t('mfa.setupManual') }}</p>
      <code class="secret">{{ secret }}</code>
      <p class="mt-3">{{ t('mfa.setupConfirm') }}</p>
      <InputText
        v-model="verifyCode"
        maxlength="6"
        class="code-input"
        :placeholder="t('mfa.codePlaceholder')"
        @keyup.enter="confirmSetup"
      />
      <div class="actions">
        <Button
          :label="t('mfa.enable')"
          icon="pi pi-check"
          :loading="loading"
          :disabled="verifyCode.length !== 6"
          @click="confirmSetup"
        />
        <Button
          :label="t('common.actions.cancel')"
          severity="secondary"
          @click="$emit('cancel')"
        />
      </div>
    </div>

    <div v-else-if="step === 'backup'" class="step">
      <h3>{{ t('mfa.backupCodesTitle') }}</h3>
      <BackupCodesDisplay :codes="backupCodes" />
      <div class="field-checkbox mt-3">
        <Checkbox v-model="saved" :binary="true" inputId="codes-saved" />
        <label for="codes-saved" class="ml-2">{{ t('mfa.backupCodesSaved') }}</label>
      </div>
      <Button
        class="mt-3"
        :label="t('common.actions.close')"
        :disabled="!saved"
        @click="$emit('done')"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import QRCode from 'qrcode'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import api from '@/api/api'
import BackupCodesDisplay from './BackupCodesDisplay.vue'

const emit = defineEmits(['done', 'cancel'])
const { t } = useI18n()
const toast = useToast()

const step = ref('qr')
const secret = ref('')
const provisioningUri = ref('')
const qrDataUrl = ref('')
const verifyCode = ref('')
const backupCodes = ref([])
const saved = ref(false)
const loading = ref(false)

onMounted(async () => {
  try {
    const res = await api.mfaSetup()
    secret.value = res.data.secret
    provisioningUri.value = res.data.provisioning_uri
    qrDataUrl.value = await QRCode.toDataURL(provisioningUri.value, { width: 200, margin: 2 })
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: t('mfa.messages.setupError'),
      life: 4000
    })
    emit('cancel')
  }
})

async function confirmSetup() {
  loading.value = true
  try {
    const res = await api.mfaVerifySetup(verifyCode.value)
    backupCodes.value = res.data.backup_codes || []
    step.value = 'backup'
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: t('mfa.enabledSuccess'),
      life: 3000
    })
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: error.response?.data?.detail || t('mfa.invalidCode'),
      life: 4000
    })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.mfa-setup-wizard {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.qr-wrap {
  display: flex;
  justify-content: center;
  margin: 1rem 0;
}
.secret {
  display: block;
  word-break: break-all;
  padding: 0.75rem;
  background: var(--surface-100, #f4f4f5);
  border-radius: 4px;
  font-family: ui-monospace, monospace;
}
.code-input {
  width: 100%;
  max-width: 12rem;
  letter-spacing: 0.3em;
  font-size: 1.25rem;
  text-align: center;
}
.actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}
.field-checkbox {
  display: flex;
  align-items: center;
}
.mt-3 {
  margin-top: 1rem;
}
.ml-2 {
  margin-left: 0.5rem;
}
</style>
