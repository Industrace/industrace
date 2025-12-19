<template>
  <div class="contacts-section">
    <div class="contacts-header">
      <h4>{{ t('assets.contacts.title') }}</h4>
      <div class="contacts-actions" v-if="canWrite">
        <Button 
          :label="t('assets.contacts.addContact')" 
          icon="pi pi-plus" 
          size="small"
          @click="showAddContactDialog = true"
        />
      </div>
    </div>

    <!-- Tabs per ruoli -->
    <TabView class="mt-3">
      <TabPanel>
        <template #header>
          <span style="display: flex; align-items: center; gap: 0.4em;">
            <i class="pi pi-users"></i> {{ t('assets.contacts.allContacts') }}
          </span>
        </template>
        <ContactsTable 
          :contacts="contactsWithFullName" 
          :canWrite="canWrite"
          :roleOptions="roleOptions"
          @remove="removeContact"
          @update-role="updateContactRole"
        />
      </TabPanel>
      <TabPanel>
        <template #header>
          <span style="display: flex; align-items: center; gap: 0.4em;">
            <i class="pi pi-star"></i> {{ t('assets.contacts.owners') }}
          </span>
        </template>
        <ContactsTable 
          :contacts="ownersWithFullName" 
          :canWrite="canWrite"
          :roleOptions="roleOptions"
          @remove="removeContact"
          @update-role="updateContactRole"
        />
      </TabPanel>
      <TabPanel>
        <template #header>
          <span style="display: flex; align-items: center; gap: 0.4em;">
            <i class="pi pi-phone"></i> {{ t('assets.contacts.pointsOfContact') }}
          </span>
        </template>
        <ContactsTable 
          :contacts="pointsOfContactWithFullName" 
          :canWrite="canWrite"
          :roleOptions="roleOptions"
          @remove="removeContact"
          @update-role="updateContactRole"
        />
      </TabPanel>
    </TabView>

    <!-- Dialog per aggiungere contatto con ruolo -->
    <Dialog 
      v-model:visible="showAddContactDialog" 
      :header="t('assets.contacts.addContact')" 
      modal 
      :closable="true" 
      :dismissableMask="true"
      style="width: 500px"
    >
      <div class="p-fluid">
        <div class="field">
          <label>{{ t('assets.contacts.selectContact') }}</label>
          <Dropdown
            v-model="selectedContactId"
            :options="availableContacts"
            optionLabel="fullName"
            optionValue="id"
            :placeholder="t('assets.contacts.selectContactPlaceholder')"
            filter
            class="w-full"
          />
        </div>
        <div class="field">
          <label>{{ t('assets.contacts.role') }}</label>
          <Dropdown
            v-model="selectedRole"
            :options="roleOptions"
            optionLabel="label"
            optionValue="value"
            :placeholder="t('assets.contacts.selectRole')"
            class="w-full"
          />
        </div>
        <div class="flex justify-content-end gap-2 mt-3">
          <Button 
            :label="t('common.actions.save')" 
            icon="pi pi-check" 
            class="p-button-sm" 
            @click="addContactWithRole"
            :disabled="!selectedContactId || !selectedRole"
          />
          <Button 
            :label="t('common.actions.cancel')" 
            icon="pi pi-times" 
            class="p-button-secondary p-button-sm" 
            @click="showAddContactDialog = false" 
          />
        </div>
        <div class="flex justify-content-end mt-2">
          <Button 
            :label="t('assets.contacts.createNewContact')" 
            icon="pi pi-plus" 
            class="p-button-text p-button-sm" 
            @click="showContactDialog = true" 
          />
        </div>
      </div>
    </Dialog>

    <!-- Dialog per creare nuovo contatto -->
    <Dialog 
      v-model:visible="showContactDialog" 
      :header="t('assets.contacts.newContact')" 
      modal 
      :closable="true" 
      :dismissableMask="true"
      style="width: 500px"
    >
      <div class="p-fluid">
        <div class="field">
          <label>{{ t('contacts.fields.firstName') }}</label>
          <InputText v-model="newContact.first_name" />
        </div>
        <div class="field">
          <label>{{ t('contacts.fields.lastName') }}</label>
          <InputText v-model="newContact.last_name" />
        </div>
        <div class="field">
          <label>{{ t('common.fields.email') }}</label>
          <InputText v-model="newContact.email" type="email" />
        </div>
        <div class="field">
          <label>{{ t('common.fields.phone') }}</label>
          <InputText v-model="newContact.phone1" />
        </div>
        <div class="field">
          <label>{{ t('common.fields.type') }}</label>
          <InputText v-model="newContact.type" />
        </div>
        <div class="flex justify-content-end gap-2 mt-3">
          <Button 
            :label="t('common.actions.save')" 
            icon="pi pi-check" 
            class="p-button-sm" 
            @click="createContact" 
          />
          <Button 
            :label="t('common.actions.cancel')" 
            icon="pi pi-times" 
            class="p-button-secondary p-button-sm" 
            @click="showContactDialog = false" 
          />
        </div>
      </div>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import ContactsTable from './components/ContactsTable.vue'
import api from '@/api/api'

const props = defineProps({
  assetId: { type: [String, Number], required: true },
  canWrite: { type: Boolean, default: false }
})
const emit = defineEmits(['updated'])
const { t } = useI18n()
const toast = useToast()

const contacts = ref([])
const owners = ref([])
const pointsOfContact = ref([])
const allContacts = ref([])
const loading = ref(false)
const showAddContactDialog = ref(false)
const showContactDialog = ref(false)
const selectedContactId = ref(null)
const selectedRole = ref(null)
const newContact = ref({ first_name: '', last_name: '', email: '', phone1: '', type: '' })

const roleOptions = computed(() => [
  { label: t('assets.contacts.roles.owner'), value: 'owner' },
  { label: t('assets.contacts.roles.pointOfContact'), value: 'point_of_contact' },
  { label: t('assets.contacts.roles.technical'), value: 'technical' },
  { label: t('assets.contacts.roles.administrative'), value: 'administrative' },
  { label: t('assets.contacts.roles.other'), value: 'other' }
])

function mapContact(contact) {
  const contactData = contact.contact || contact
  return { 
    ...contact, 
    ...contactData,
    fullName: `${contactData.first_name || ''} ${contactData.last_name || ''}`.trim() || contactData.email,
    role: contact.role || 'other',
    contactId: contact.contact_id || contact.id
  }
}

const contactsWithFullName = computed(() =>
  (contacts.value || []).map(mapContact)
)

const ownersWithFullName = computed(() =>
  (owners.value || []).map(mapContact)
)

const pointsOfContactWithFullName = computed(() =>
  (pointsOfContact.value || []).map(mapContact)
)

const availableContacts = computed(() => {
  const assignedIds = new Set(contacts.value.map(c => c.contact_id || c.id))
  return allContacts.value
    .filter(c => !assignedIds.has(c.id))
    .map(c => ({ ...c, fullName: `${c.first_name || ''} ${c.last_name || ''}`.trim() || c.email }))
})

async function fetchContacts() {
  loading.value = true
  try {
    const res = await api.getAssetContacts(props.assetId)
    contacts.value = res.data || []
  } catch (error) {
    console.error('Error fetching contacts:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: t('assets.contacts.errorLoading') })
  } finally {
    loading.value = false
  }
}

async function fetchOwners() {
  try {
    const res = await api.getAssetOwners(props.assetId)
    owners.value = res.data || []
  } catch (error) {
    console.error('Error fetching owners:', error)
  }
}

async function fetchPointsOfContact() {
  try {
    const res = await api.getAssetPointsOfContact(props.assetId)
    pointsOfContact.value = res.data || []
  } catch (error) {
    console.error('Error fetching points of contact:', error)
  }
}

async function fetchAllContacts() {
  try {
    const res = await api.getContacts()
    allContacts.value = res.data || []
  } catch (error) {
    console.error('Error fetching all contacts:', error)
  }
}

async function addContactWithRole() {
  if (!selectedContactId.value || !selectedRole.value) {
    toast.add({ severity: 'warn', summary: t('common.errors.warning'), detail: t('assets.contacts.selectContactAndRole') })
    return
  }

  try {
    await api.addAssetContactWithRole(props.assetId, {
      contact_id: selectedContactId.value,
      role: selectedRole.value
    })
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('assets.contacts.contactAdded') })
    showAddContactDialog.value = false
    selectedContactId.value = null
    selectedRole.value = null
    await Promise.all([fetchContacts(), fetchOwners(), fetchPointsOfContact()])
    emit('updated')
  } catch (error) {
    console.error('Error adding contact:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: error.response?.data?.detail || t('assets.contacts.errorAdding') })
  }
}

async function removeContact(contactId) {
  try {
    await api.deleteAssetContact(props.assetId, contactId)
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('assets.contacts.contactRemoved') })
    await Promise.all([fetchContacts(), fetchOwners(), fetchPointsOfContact()])
    emit('updated')
  } catch (error) {
    console.error('Error removing contact:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: error.response?.data?.detail || t('assets.contacts.errorRemoving') })
  }
}

async function updateContactRole(contactId, newRole) {
  try {
    const contact = contacts.value.find(c => (c.contact_id || c.id) === contactId)
    if (!contact) return

    const contactsData = contacts.value.map(c => ({
      contact_id: c.contact_id || c.id,
      role: (c.contact_id || c.id) === contactId ? newRole : c.role
    }))

    await api.updateAssetContacts(props.assetId, contactsData)
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('assets.contacts.roleUpdated') })
    await Promise.all([fetchContacts(), fetchOwners(), fetchPointsOfContact()])
    emit('updated')
  } catch (error) {
    console.error('Error updating role:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: error.response?.data?.detail || t('assets.contacts.errorUpdatingRole') })
  }
}

async function createContact() {
  try {
    await api.createContact(newContact.value)
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('assets.contacts.contactCreated') })
    showContactDialog.value = false
    newContact.value = { first_name: '', last_name: '', email: '', phone1: '', type: '' }
    await fetchAllContacts()
    showAddContactDialog.value = true
  } catch (error) {
    console.error('Error creating contact:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: error.response?.data?.detail || t('assets.contacts.errorCreating') })
  }
}

onMounted(async () => {
  await Promise.all([
    fetchContacts(),
    fetchOwners(),
    fetchPointsOfContact(),
    fetchAllContacts()
  ])
})

watch(() => props.assetId, async (newId, oldId) => {
  if (newId !== oldId) {
    await Promise.all([
      fetchContacts(),
      fetchOwners(),
      fetchPointsOfContact(),
      fetchAllContacts()
    ])
  }
})
</script>

<style scoped>
.contacts-section { padding: 1rem 0; }
.contacts-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
.contacts-actions { display: flex; align-items: center; gap: 0.5rem; }
</style>
