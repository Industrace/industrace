<template>
  <div class="notification-test-tab">
    <Card>
      <template #title>
        {{ t('notifications.sendTestEmail') }}
      </template>
      <template #content>
        <div v-if="loading" class="text-center p-4">
          <ProgressSpinner />
        </div>
        <div v-else class="p-fluid">
          <div class="field">
            <label>{{ t('notifications.template') }} *</label>
            <Dropdown
              v-model="selectedTemplate"
              :options="templateOptions"
              optionLabel="label"
              optionValue="value"
              :placeholder="t('notifications.selectTemplate')"
              class="w-full"
              :disabled="loading"
            />
            <small v-if="templateOptions.length === 0" class="text-color-secondary">
              {{ t('notifications.noTemplates') }}
            </small>
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
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import ProgressSpinner from 'primevue/progressspinner'
import api from '@/api/api'

const emit = defineEmits(['test'])
const { t } = useI18n()
const toast = useToast()

const selectedTemplate = ref(null)
const testEmail = ref('')
const sending = ref(false)
const loading = ref(false)
const templates = ref([])

const templateOptions = computed(() => {
  return templates.value.map(template => ({
    label: template.name || template.template_code,
    value: template.template_code
  }))
})

async function fetchTemplates() {
  loading.value = true
  try {
    const res = await api.getNotificationTemplates()
    templates.value = res.data || []
  } catch (error) {
    console.error('Error fetching templates:', error)
    toast.add({ 
      severity: 'error', 
      summary: t('common.messages.error'), 
      detail: t('notifications.errorLoadingTemplates') 
    })
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchTemplates()
})

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

