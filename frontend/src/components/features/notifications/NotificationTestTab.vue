<template>
  <div class="notification-test-tab">
    <Card>
      <template #title>
        {{ t('notifications.sendTestEmail') }}
      </template>
      <template #content>
        <div class="p-fluid">
          <div class="field">
            <label>{{ t('notifications.template') }} *</label>
            <Dropdown
              v-model="selectedTemplate"
              :options="templateOptions"
              optionLabel="label"
              optionValue="value"
              :placeholder="t('notifications.selectTemplate')"
              class="w-full"
            />
          </div>
          <div class="field">
            <label>{{ t('common.fields.email') }} *</label>
            <InputText 
              v-model="testEmail" 
              type="email"
              :placeholder="t('notifications.testEmailPlaceholder')"
            />
          </div>
          <div class="flex justify-content-end gap-2 mt-3">
            <Button 
              :label="t('notifications.sendTest')" 
              icon="pi pi-send" 
              @click="sendTest"
              :loading="sending"
              :disabled="!selectedTemplate || !testEmail"
            />
          </div>
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import api from '@/api/api'

const emit = defineEmits(['test'])
const { t } = useI18n()

const selectedTemplate = ref(null)
const testEmail = ref('')
const sending = ref(false)

const templateOptions = [
  { label: t('notifications.types.assetReviewDue'), value: 'asset_review_due' },
  { label: t('notifications.types.assetReviewOverdue'), value: 'asset_review_overdue' },
  { label: t('notifications.types.riskAlert'), value: 'risk_alert' }
]

async function sendTest() {
  if (!selectedTemplate.value || !testEmail.value) return
  
  sending.value = true
  try {
    await emit('test', {
      template_code: selectedTemplate.value,
      email: testEmail.value
    })
    testEmail.value = ''
    selectedTemplate.value = null
  } finally {
    sending.value = false
  }
}
</script>

<style scoped>
.notification-test-tab {
  padding: 1rem 0;
}
</style>

