<template>
  <div class="notification-preferences-tab">
    <div class="mb-3 flex justify-content-end">
      <Button 
        :label="t('notifications.addPreference')" 
        icon="pi pi-plus" 
        @click="showAddDialog = true"
        :disabled="availableTemplates.length === 0"
      />
    </div>
    
    <div v-if="loading" class="text-center p-4">
      <ProgressSpinner />
    </div>
    <div v-else>
      <DataTable 
        :value="preferences" 
        :emptyMessage="t('notifications.noPreferences')"
        class="p-datatable-sm"
      >
        <Column field="notification_type" :header="t('notifications.type')" sortable>
          <template #body="{ data }">
            <span class="font-semibold">{{ getNotificationTypeLabel(data.notification_type) }}</span>
          </template>
        </Column>
        <Column :header="t('notifications.emailEnabled')">
          <template #body="{ data }">
            <InputSwitch v-model="data.email_enabled" @update:modelValue="updatePreference(data, 'email_enabled', $event)" />
          </template>
        </Column>
        <Column :header="t('notifications.inAppEnabled')">
          <template #body="{ data }">
            <InputSwitch v-model="data.in_app_enabled" @update:modelValue="updatePreference(data, 'in_app_enabled', $event)" />
          </template>
        </Column>
        <Column field="frequency" :header="t('notifications.frequency')" sortable>
          <template #body="{ data }">
            <Dropdown
              :modelValue="data.frequency"
              :options="frequencyOptions"
              optionLabel="label"
              optionValue="value"
              @update:modelValue="updatePreference(data, 'frequency', $event)"
              class="w-12rem"
            />
          </template>
        </Column>
        <Column :header="t('notifications.minSeverity')">
          <template #body="{ data }">
            <InputNumber 
              v-model="data.severity_min" 
              :min="0" 
              :max="10"
              @update:modelValue="updatePreference(data, 'severity_min', $event)"
              class="w-8rem"
              :showButtons="true"
            />
          </template>
        </Column>
        <Column :header="t('common.strings.actions')">
          <template #body="{ data }">
            <Button 
              icon="pi pi-trash" 
              class="p-button-rounded p-button-text p-button-danger"
              @click="deletePreference(data)"
              :title="t('notifications.deletePreference')"
            />
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Dialog per aggiungere preferenza -->
    <Dialog 
      v-model:visible="showAddDialog" 
      :header="t('notifications.addPreference')" 
      modal 
      :closable="true" 
      :dismissableMask="true"
      style="width: 500px"
    >
      <div class="p-fluid">
        <div class="field">
          <label for="template">{{ t('notifications.selectTemplate') }} *</label>
          <Dropdown
            id="template"
            v-model="newPreference.notification_type"
            :options="availableTemplates"
            optionLabel="name"
            optionValue="template_code"
            :placeholder="t('notifications.selectTemplatePlaceholder')"
            :class="{ 'p-invalid': errors.template }"
            filter
          />
          <small v-if="errors.template" class="p-error">{{ errors.template }}</small>
        </div>
        <div class="field">
          <label class="checkbox-label">
            <Checkbox v-model="newPreference.email_enabled" :binary="true" inputId="email_enabled" />
            {{ t('notifications.emailEnabled') }}
          </label>
        </div>
        <div class="field">
          <label class="checkbox-label">
            <Checkbox v-model="newPreference.in_app_enabled" :binary="true" inputId="in_app_enabled" />
            {{ t('notifications.inAppEnabled') }}
          </label>
        </div>
        <div class="field">
          <label for="frequency">{{ t('notifications.frequency') }}</label>
          <Dropdown
            id="frequency"
            v-model="newPreference.frequency"
            :options="frequencyOptions"
            optionLabel="label"
            optionValue="value"
            :placeholder="t('notifications.selectFrequency')"
          />
        </div>
        <div class="field">
          <label for="severity_min">{{ t('notifications.minSeverity') }}</label>
          <InputNumber 
            id="severity_min"
            v-model="newPreference.severity_min" 
            :min="0" 
            :max="10"
            class="w-full"
            :showButtons="true"
            :placeholder="t('notifications.minSeverityPlaceholder')"
          />
        </div>
        <div class="flex justify-content-end gap-2 mt-3">
          <Button 
            :label="t('common.actions.add')" 
            icon="pi pi-check" 
            class="p-button-sm" 
            @click="createPreference"
            :loading="creating"
          />
          <Button 
            :label="t('common.actions.cancel')" 
            icon="pi pi-times" 
            class="p-button-secondary p-button-sm" 
            @click="showAddDialog = false" 
          />
        </div>
      </div>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import InputSwitch from 'primevue/inputswitch'
import Dropdown from 'primevue/dropdown'
import InputNumber from 'primevue/inputnumber'
import ProgressSpinner from 'primevue/progressspinner'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Checkbox from 'primevue/checkbox'
import api from '@/api/api'

const props = defineProps({
  preferences: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
})

const emit = defineEmits(['refresh'])
const { t } = useI18n()
const toast = useToast()

const showAddDialog = ref(false)
const creating = ref(false)
const availableTemplates = ref([])
const errors = ref({})

const newPreference = ref({
  notification_type: null,
  email_enabled: true,
  in_app_enabled: true,
  frequency: 'immediate',
  severity_min: null
})

const frequencyOptions = computed(() => [
  { label: t('notifications.frequency.immediate'), value: 'immediate' },
  { label: t('notifications.frequency.dailyDigest'), value: 'daily_digest' },
  { label: t('notifications.frequency.weeklyDigest'), value: 'weekly_digest' }
])

const getNotificationTypeLabel = (type) => {
  const labels = {
    'asset_review_due': t('notifications.types.assetReviewDue'),
    'asset_review_overdue': t('notifications.types.assetReviewOverdue'),
    'risk_alert': t('notifications.types.riskAlert')
  }
  return labels[type] || type
}

async function fetchAvailableTemplates() {
  try {
    const res = await api.getNotificationTemplates()
    const existingTypes = props.preferences.map(p => p.notification_type)
    // Filtra solo i template che non hanno già una preferenza
    availableTemplates.value = (res.data || []).filter(t => !existingTypes.includes(t.template_code))
  } catch (error) {
    console.error('Error fetching templates:', error)
    availableTemplates.value = []
  }
}

async function createPreference() {
  errors.value = {}
  
  if (!newPreference.value.notification_type) {
    errors.value.template = t('notifications.templateRequired')
    return
  }

  creating.value = true
  try {
    await api.createNotificationPreference(newPreference.value)
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('notifications.preferenceCreated') })
    showAddDialog.value = false
    // Reset form
    newPreference.value = {
      notification_type: null,
      email_enabled: true,
      in_app_enabled: true,
      frequency: 'immediate',
      severity_min: null
    }
    await fetchAvailableTemplates()
    emit('refresh')
  } catch (error) {
    console.error('Error creating preference:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: error.response?.data?.detail || t('notifications.errorCreating') })
  } finally {
    creating.value = false
  }
}

async function deletePreference(preference) {
  if (!confirm(t('notifications.confirmDeletePreference'))) return
  
  try {
    await api.deleteNotificationPreference(preference.id)
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('notifications.preferenceDeleted') })
    await fetchAvailableTemplates()
    emit('refresh')
  } catch (error) {
    console.error('Error deleting preference:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: error.response?.data?.detail || t('notifications.errorDeleting') })
  }
}

async function updatePreference(preference, field, value) {
  try {
    await api.updateNotificationPreference(preference.id, { [field]: value })
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('notifications.preferenceUpdated') })
    emit('refresh')
  } catch (error) {
    console.error('Error updating preference:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: error.response?.data?.detail || t('notifications.errorUpdating') })
    // Revert change
    emit('refresh') // Refresh to get correct values
  }
}

// Watch per aggiornare i template disponibili quando cambiano le preferenze
watch(() => props.preferences, () => {
  fetchAvailableTemplates()
}, { immediate: true })

onMounted(() => {
  fetchAvailableTemplates()
})
</script>

<style scoped>
.w-12rem {
  width: 12rem;
}

.w-8rem {
  width: 8rem;
}
</style>
