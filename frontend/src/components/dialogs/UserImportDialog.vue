<template>
  <Dialog :visible="visible" @update:visible="$emit('close')" :header="t('users.userImport.title')" :modal="true" :style="{ width: '60vw' }">
    <div class="mb-3">
      <a :href="templateUrl" download class="p-button p-button-sm p-button-outlined">
        <i class="pi pi-download mr-2" />{{ t('users.userImport.downloadTemplate') }}
      </a>
    </div>
    <div class="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
      <h4 class="text-blue-800 mb-2">{{ t('users.userImport.importantInfo') }}</h4>
      <ul class="text-blue-600 text-sm">
        <li>• {{ t('users.userImport.nameRequired') }}</li>
        <li>• {{ t('users.userImport.emailRequired') }}</li>
        <li>• {{ t('users.userImport.roleRequired') }}</li>
      </ul>
      <p class="text-blue-600 text-sm mt-2">{{ t('users.userImport.tipText') }}</p>
    </div>
    <div class="mb-3">
      <input type="file" accept=".csv,.xlsx" @change="onFileChange" />
    </div>
    <div v-if="loading" class="mb-3">
      <ProgressSpinner style="width:40px;height:40px" />
    </div>
    <div v-if="error" class="mb-3 text-red-600"><pre>{{ error }}</pre></div>
    <div v-if="previewResult">
      <div v-if="previewResult.to_create?.length">
        <h4 class="mb-1">{{ t('users.userImport.toCreate') }}</h4>
        <DataTable :value="previewResult.to_create" scrollable :scrollHeight="'20vh'">
          <Column v-for="col in columns" :key="col.field" :field="col.field" :header="t(col.header)" />
        </DataTable>
      </div>
      <div v-if="previewResult.to_update?.length">
        <h4 class="mt-3 mb-1">{{ t('users.userImport.toUpdate') }}</h4>
        <DataTable :value="previewResult.to_update" scrollable :scrollHeight="'20vh'">
          <Column field="email" :header="t('common.fields.email')" />
          <Column field="diff" :header="t('users.userImport.differences')">
            <template #body="{ data }">
              <ul>
                <li v-for="(change, field) in data.diff" :key="field">
                  <b>{{ field }}</b>: <span style="color: #888">{{ change.old }}</span> → <span style="color: #059669">{{ change.new }}</span>
                </li>
              </ul>
            </template>
          </Column>
        </DataTable>
      </div>
      <div v-if="previewResult.errors?.length">
        <h4 class="mt-3 mb-1 text-red-600">{{ t('users.userImport.errors') }}</h4>
        <ul>
          <li v-for="err in previewResult.errors" :key="err.row">{{ t('users.userImport.row') }} {{ err.row }}: {{ err.error }}</li>
        </ul>
      </div>
    </div>
    <template #footer>
      <Button :label="t('common.actions.cancel')" class="p-button-text" @click="$emit('close')" />
      <Button :label="t('users.userImport.confirm')" :disabled="isConfirmDisabled" @click="confirmImport" />
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import ProgressSpinner from 'primevue/progressspinner'
import api from '../../api/api'

const { t } = useI18n()
defineProps({ visible: Boolean })
const emit = defineEmits(['close', 'imported'])

const templateUrl = '/template_import_user.csv'
const file = ref(null)
const columns = [
  { field: 'name', header: 'common.fields.name' },
  { field: 'email', header: 'common.fields.email' },
  { field: 'role', header: 'users.fields.role' },
  { field: 'is_active', header: 'common.fields.status' }
]
const loading = ref(false)
const error = ref('')
const previewResult = ref(null)

const isConfirmDisabled = computed(() => {
  return !file.value || loading.value || (error.value && error.value.length > 0) ||
    (previewResult.value?.errors?.length > 0)
})

async function onFileChange(e) {
  error.value = ''
  previewResult.value = null
  const f = e.target.files[0]
  if (!f) return
  file.value = f
  loading.value = true
  try {
    const { data } = await api.previewUserImportXlsx(f)
    previewResult.value = data
    if (data.error) {
      error.value = data.error
    } else if (data.errors?.length) {
      error.value = data.errors.map(e => `${t('users.userImport.row')} ${e.row}: ${e.error}`).join('\n')
    }
  } catch {
    error.value = t('users.userImport.readError')
  }
  loading.value = false
}

async function confirmImport() {
  if (!file.value) return
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.confirmUserImportXlsx(file.value)
    emit('imported', data)
  } catch {
    error.value = t('users.userImport.readError')
  }
  loading.value = false
}
</script>

<style scoped>
.text-red-600 { color: #dc2626; }
</style>
