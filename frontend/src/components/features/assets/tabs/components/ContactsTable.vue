<template>
  <DataTable 
    :value="contacts" 
    :emptyMessage="t('assets.contacts.noContacts')"
    class="p-datatable-sm"
  >
    <Column field="fullName" :header="t('contacts.fields.fullName')" />
    <Column field="email" :header="t('common.fields.email')" />
    <Column field="phone1" :header="t('common.fields.phone')" />
    <Column :header="t('assets.contacts.role')">
      <template #body="{ data }">
        <div v-if="canWrite" class="flex align-items-center gap-2">
          <Dropdown
            :modelValue="data.role"
            :options="roleOptions"
            optionLabel="label"
            optionValue="value"
            @update:modelValue="handleRoleChange(data.contactId || data.id, $event)"
            class="w-12rem"
          />
        </div>
        <Tag v-else :value="getRoleLabel(data.role)" :severity="getRoleSeverity(data.role)" />
      </template>
    </Column>
    <Column v-if="canWrite" :header="t('common.strings.actions')">
      <template #body="{ data }">
        <Button 
          icon="pi pi-trash" 
          class="p-button-rounded p-button-text p-button-danger" 
          @click="$emit('remove', data.contactId || data.id)" 
          :title="t('assets.contacts.removeContact')" 
        />
      </template>
    </Column>
  </DataTable>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Dropdown from 'primevue/dropdown'

const props = defineProps({
  contacts: { type: Array, default: () => [] },
  canWrite: { type: Boolean, default: false },
  roleOptions: { type: Array, required: true }
})

const emit = defineEmits(['remove', 'update-role'])
const { t } = useI18n()

const getRoleLabel = (role) => {
  const option = props.roleOptions.find(opt => opt.value === role)
  return option ? option.label : role
}

const getRoleSeverity = (role) => {
  const severityMap = {
    'owner': 'success',
    'point_of_contact': 'info',
    'technical': 'warning',
    'administrative': 'secondary',
    'other': null
  }
  return severityMap[role] || null
}

const handleRoleChange = (contactId, newRole) => {
  emit('update-role', contactId, newRole)
}
</script>

<style scoped>
.w-12rem {
  width: 12rem;
}
</style>

