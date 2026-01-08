<template>
  <div class="notification-templates-tab">
    <div v-if="loading" class="text-center p-4">
      <ProgressSpinner />
    </div>
    <div v-else>
      <DataTable 
        :value="templates" 
        :emptyMessage="t('notifications.noTemplates')"
        class="p-datatable-sm"
        :paginator="true"
        :rows="10"
      >
        <Column field="name" :header="t('notifications.templateName')" sortable>
          <template #body="{ data }">
            {{ data.name }}
            <Tag v-if="data.tenant_id" value="Override" severity="info" class="ml-2" style="font-size: 0.75rem;" />
          </template>
        </Column>
        <Column field="template_code" :header="t('notifications.templateCode')" sortable />
        <Column field="description" :header="t('notifications.description')" />
        <Column :header="t('notifications.enabled')">
          <template #body="{ data }">
            <Tag :value="data.enabled ? t('common.strings.yes') : t('common.strings.no')" :severity="data.enabled ? 'success' : 'danger'" />
          </template>
        </Column>
        <Column :header="t('common.strings.actions')">
          <template #body="{ data }">
            <div class="flex gap-1">
              <Button 
                v-if="!data.tenant_id"
                icon="pi pi-copy" 
                class="p-button-rounded p-button-text p-button-sm"
                @click="createOverride(data)"
                :title="t('notifications.createOverride')"
              />
              <Button 
                icon="pi pi-pencil" 
                class="p-button-rounded p-button-text p-button-sm"
                @click="editTemplate(data)"
                :title="t('common.actions.edit')"
                :disabled="!data.tenant_id"
              />
              <Button 
                v-if="data.tenant_id && data.tenant_id !== null && data.tenant_id !== ''"
                icon="pi pi-trash" 
                class="p-button-rounded p-button-text p-button-sm p-button-danger"
                @click="deleteOverride(data)"
                :title="t('notifications.deleteOverride')"
              />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- Dialog Editor Template -->
    <Dialog 
      v-model:visible="showEditorDialog" 
      :header="editingTemplate ? t('notifications.editTemplate') : t('notifications.viewTemplate')" 
      modal 
      :closable="true" 
      :dismissableMask="true"
      :style="{ width: '90vw', maxWidth: '900px' }"
    >
      <div v-if="editingTemplate" class="template-editor">
        <div class="template-info mb-4 p-3" style="background: var(--surface-ground); border-radius: 4px;">
          <Message 
            v-if="!canEdit" 
            severity="warn" 
            :closable="false"
            class="mb-3"
          >
            <template #messageicon>
              <i class="pi pi-exclamation-triangle"></i>
            </template>
            <small>{{ t('notifications.systemTemplateReadOnly') }}</small>
          </Message>
          <Message 
            v-else-if="editingTemplate.name && editingTemplate.name.includes('(Override)')" 
            severity="info" 
            :closable="false"
            class="mb-3"
          >
            <template #messageicon>
              <i class="pi pi-info-circle"></i>
            </template>
            <small>{{ t('notifications.overrideTemplateInfo') }}</small>
          </Message>
          <div class="field mb-3">
            <label><strong>{{ t('notifications.templateCode') }}:</strong></label>
            <span class="ml-2">{{ editingTemplate.template_code }}</span>
          </div>
          <div class="field mb-3">
            <label><strong>{{ t('notifications.templateName') }}:</strong></label>
            <InputText 
              v-model="editingTemplate.name" 
              class="w-full mt-1"
              :disabled="!canEdit"
            />
          </div>
          <div class="field mb-3">
            <label><strong>{{ t('notifications.description') }}:</strong></label>
            <InputText 
              v-model="editingTemplate.description" 
              class="w-full mt-1"
              :disabled="!canEdit"
            />
          </div>
          <div class="field">
            <label class="checkbox-label">
              <Checkbox 
                v-model="editingTemplate.enabled" 
                :binary="true" 
                inputId="template_enabled"
                :disabled="!canEdit"
              />
              {{ t('notifications.enabled') }}
            </label>
          </div>
        </div>

        <div class="template-variables mb-4 p-3" style="background: var(--surface-50); border-radius: 4px;">
          <h4 class="mt-0 mb-2">{{ t('notifications.availableVariables') }}</h4>
          <div class="flex flex-wrap gap-2">
            <Tag 
              v-for="varName in availableVariables" 
              :key="varName"
              :value="`{{${varName}}}`"
              severity="info"
              class="cursor-pointer"
              @click="insertVariable(varName)"
            />
          </div>
          <small class="text-color-secondary mt-2 block">{{ t('notifications.clickToInsert') }}</small>
        </div>

        <div class="field mb-4">
          <label for="subject_template"><strong>{{ t('notifications.subjectTemplate') }} *</strong></label>
          <InputText 
            id="subject_template"
            v-model="editingTemplate.subject_template" 
            class="w-full mt-1"
            :disabled="!canEdit"
            :placeholder="subjectPlaceholder"
          />
          <small class="text-color-secondary" v-text="useVariablesText"></small>
        </div>

        <div class="field mb-4">
          <label for="body_template_html"><strong>{{ t('notifications.htmlBodyTemplate') }} *</strong></label>
          <Textarea 
            id="body_template_html"
            v-model="editingTemplate.body_template_html" 
            class="w-full mt-1"
            :disabled="!canEdit"
            :rows="12"
            :placeholder="t('notifications.htmlBodyPlaceholder')"
          />
          <small class="text-color-secondary">{{ t('notifications.htmlSupported') }}</small>
        </div>

        <div class="field mb-4">
          <label for="body_template_text"><strong>{{ t('notifications.textBodyTemplate') }}</strong> ({{ t('common.optional') }})</label>
          <Textarea 
            id="body_template_text"
            v-model="editingTemplate.body_template_text" 
            class="w-full mt-1"
            :disabled="!canEdit"
            :rows="8"
            :placeholder="t('notifications.textBodyPlaceholder')"
          />
          <small class="text-color-secondary">{{ t('notifications.plainTextFallback') }}</small>
        </div>

        <div class="flex justify-content-end gap-2 mt-4">
          <Button 
            :label="t('common.actions.cancel')" 
            icon="pi pi-times" 
            class="p-button-secondary" 
            @click="showEditorDialog = false" 
          />
          <Button 
            v-if="canEdit"
            :label="t('common.actions.save')" 
            icon="pi pi-check" 
            @click="saveTemplate"
            :loading="saving"
          />
        </div>
      </div>
    </Dialog>

    <!-- Confirm Dialog -->
    <BaseConfirmDialog
      v-model:showConfirmDialog="showConfirmDialog"
      :confirmData="confirmData"
      @execute="executeConfirmedAction"
      @close="closeConfirmDialog"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Checkbox from 'primevue/checkbox'
import Tag from 'primevue/tag'
import ProgressSpinner from 'primevue/progressspinner'
import Message from 'primevue/message'
import BaseConfirmDialog from '@/components/base/BaseConfirmDialog.vue'
import api from '@/api/api'
import { useConfirm } from '@/composables/useConfirm'
import itNotifications from '@/locales/it/notifications.json'
import enNotifications from '@/locales/en/notifications.json'

const { t, locale } = useI18n()
const toast = useToast()
const { 
  showConfirmDialog, 
  confirmData, 
  confirmDelete, 
  executeConfirmedAction, 
  closeConfirmDialog 
} = useConfirm()

const templates = ref([])
const loading = ref(false)
const saving = ref(false)
const showEditorDialog = ref(false)
const editingTemplate = ref(null)

// Common variables available in templates
const availableVariables = computed(() => {
  if (!editingTemplate.value) return []
  
  // Get variables from template or use defaults
  return editingTemplate.value.variables || [
    'user_name',
    'asset_name',
    'asset_id',
    'site_name',
    'last_review_date',
    'days_until_review',
    'days_overdue',
    'risk_score',
    'risk_level',
    'asset_url'
  ]
})

const canEdit = computed(() => {
  // Can only edit tenant-specific templates (has tenant_id)
  // System-wide templates (tenant_id = null or undefined) cannot be edited directly
  if (!editingTemplate.value) return false
  // tenant_id can be a string UUID or null/undefined
  const tenantId = editingTemplate.value.tenant_id
  return tenantId !== null && tenantId !== undefined && tenantId !== ''
})

// Placeholder texts - access translations directly to avoid vue-i18n interpolation issues with {{}}
const subjectPlaceholder = computed(() => {
  const translations = locale.value === 'it' ? itNotifications : enNotifications
  return translations.subjectPlaceholder || 'Es: Review asset {{asset_name}} in scadenza'
})

const useVariablesText = computed(() => {
  const translations = locale.value === 'it' ? itNotifications : enNotifications
  return translations.useVariables || 'Usa {{variabile}} per inserire valori dinamici'
})

async function fetchTemplates() {
  loading.value = true
  try {
    const res = await api.getNotificationTemplates()
    templates.value = res.data || []
    
    // Fetch full details for each template
    for (let template of templates.value) {
      try {
        const detailRes = await api.getNotificationTemplate(template.template_code)
        // Merge details, preserving tenant_id from initial response if available
        const merged = { ...template, ...detailRes.data }
        // Ensure tenant_id is preserved (could be string or null)
        if (template.tenant_id !== undefined) {
          merged.tenant_id = template.tenant_id
        }
        Object.assign(template, merged)
        // Debug log to verify tenant_id
        console.log(`Template ${template.template_code}:`, {
          name: template.name,
          tenant_id: template.tenant_id,
          hasTenantId: !!template.tenant_id
        })
      } catch (error) {
        console.error(`Error fetching template ${template.template_code}:`, error)
      }
    }
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

function editTemplate(template) {
  // Create a copy for editing
  editingTemplate.value = { ...template }
  // Debug: log tenant_id to verify it's set
  console.log('Editing template:', {
    template_code: template.template_code,
    name: template.name,
    tenant_id: template.tenant_id,
    canEdit: canEdit.value
  })
  showEditorDialog.value = true
}

async function createOverride(template) {
  if (!template || template.tenant_id) {
    // Already has override or invalid template
    return
  }
  
  try {
    // Create override using dedicated endpoint
    const response = await api.createTemplateOverride(template.template_code)
    
    toast.add({ 
      severity: 'success', 
      summary: t('common.messages.success'), 
      detail: t('notifications.overrideCreated') 
    })
    
    // Refresh templates to show the new override
    await fetchTemplates()
    
    // Find the newly created override and open it for editing
    // Use the response data directly if available, otherwise search in templates
    if (response.data && response.data.tenant_id) {
      // Use the response data which should have the correct tenant_id
      editTemplate(response.data)
    } else {
      // Fallback: search in templates
      const updatedTemplates = templates.value.filter(t => 
        t.template_code === template.template_code && t.tenant_id !== null && t.tenant_id !== undefined
      )
      if (updatedTemplates.length > 0) {
        editTemplate(updatedTemplates[0])
      }
    }
  } catch (error) {
    console.error('Error creating override:', error)
    toast.add({ 
      severity: 'error', 
      summary: t('common.messages.error'), 
      detail: error.response?.data?.detail || t('notifications.errorCreatingOverride') 
    })
  }
}

function deleteOverride(template) {
  if (!template || !template.tenant_id) {
    // Not an override or invalid template
    return
  }
  
  confirmDelete(
    template,
    template.name || template.template_code,
    async () => {
      await api.deleteTemplateOverride(template.template_code)
      toast.add({ 
        severity: 'success', 
        summary: t('common.messages.success'), 
        detail: t('notifications.overrideDeleted') 
      })
      await fetchTemplates()
    },
    {
      successMessage: t('notifications.overrideDeleted'),
      errorContext: t('notifications.errorDeletingOverride')
    }
  )
}

function insertVariable(varName) {
  if (!editingTemplate.value || !canEdit.value) return
  
  const placeholder = `{{${varName}}}`
  
  // Try to insert in the active field (for simplicity, insert in HTML body)
  const textarea = document.getElementById('body_template_html')
  if (textarea) {
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const text = editingTemplate.value.body_template_html
    editingTemplate.value.body_template_html = 
      text.substring(0, start) + placeholder + text.substring(end)
    
    // Set cursor position after inserted variable
    setTimeout(() => {
      textarea.focus()
      textarea.setSelectionRange(start + placeholder.length, start + placeholder.length)
    }, 0)
  }
}

async function saveTemplate() {
  if (!editingTemplate.value || !canEdit.value) return
  
  saving.value = true
  try {
    const response = await api.updateNotificationTemplate(editingTemplate.value.template_code, {
      name: editingTemplate.value.name,
      description: editingTemplate.value.description,
      subject_template: editingTemplate.value.subject_template,
      body_template_html: editingTemplate.value.body_template_html,
      body_template_text: editingTemplate.value.body_template_text,
      enabled: editingTemplate.value.enabled
    })
    
    // Update editingTemplate with response data
    if (response.data) {
      Object.assign(editingTemplate.value, response.data)
    }
    
    toast.add({ 
      severity: 'success', 
      summary: t('common.messages.success'), 
      detail: t('notifications.templateUpdated') 
    })
    
    showEditorDialog.value = false
    await fetchTemplates()
  } catch (error) {
    console.error('Error saving template:', error)
    toast.add({ 
      severity: 'error', 
      summary: t('common.messages.error'), 
      detail: error.response?.data?.detail || t('notifications.errorUpdatingTemplate') 
    })
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchTemplates()
})
</script>

<style scoped>
.template-editor {
  max-height: 80vh;
  overflow-y: auto;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.cursor-pointer {
  cursor: pointer;
}

.block {
  display: block;
}
</style>

