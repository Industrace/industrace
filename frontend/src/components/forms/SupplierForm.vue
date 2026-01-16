<template>
  <form @submit.prevent="handleSubmit">
    <div class="p-fluid">
      <div class="p-field">
        <label for="name">{{ t('common.fields.name') }} *</label>
        <InputText id="name" v-model="form.name" :placeholder="t('suppliers.placeholders.supplierName')" required />
      </div>
      <div class="p-field">
        <label for="description">{{ t('common.description') }}</label>
        <Textarea id="description" v-model="form.description" :placeholder="t('suppliers.placeholders.supplierDescription')" autoResize />
      </div>
      <div class="p-field">
        <label for="vat_number">{{ t('suppliers.fields.vatNumber') }}</label>
        <InputText id="vat_number" v-model="form.vat_number" :placeholder="t('suppliers.placeholders.vatNumber')" />
      </div>
      <div class="p-field">
        <label for="tax_code">{{ t('suppliers.fields.taxCode') }}</label>
        <InputText id="tax_code" v-model="form.tax_code" :placeholder="t('suppliers.placeholders.taxCode')" />
      </div>
      <div class="p-field">
        <label for="address">{{ t('suppliers.fields.address') }}</label>
        <InputText id="address" v-model="form.address" :placeholder="t('suppliers.placeholders.address')" />
      </div>
      <div class="p-field">
        <label for="city">{{ t('suppliers.fields.city') }}</label>
        <InputText id="city" v-model="form.city" :placeholder="t('suppliers.placeholders.city')" />
      </div>
      <div class="p-field">
        <label for="zip_code">{{ t('suppliers.fields.zipCode') }}</label>
        <InputText id="zip_code" v-model="form.zip_code" :placeholder="t('suppliers.placeholders.zipCode')" />
      </div>
      <div class="p-field">
        <label for="province">{{ t('suppliers.fields.province') }}</label>
        <InputText id="province" v-model="form.province" :placeholder="t('suppliers.placeholders.province')" />
      </div>
      <div class="p-field">
        <label for="country">{{ t('suppliers.fields.country') }}</label>
        <InputText id="country" v-model="form.country" :placeholder="t('suppliers.placeholders.country')" />
      </div>
      <div class="p-field">
        <label for="phone">{{ t('suppliers.fields.phone') }}</label>
        <InputText id="phone" v-model="form.phone" :placeholder="t('suppliers.placeholders.phone')" />
      </div>
      <div class="p-field">
          <label for="email">{{ t('suppliers.fields.email') }}</label>
        <InputText id="email" v-model="form.email" :placeholder="t('suppliers.placeholders.email')" />
      </div>
      <div class="p-field">
        <label for="website">{{ t('suppliers.fields.website') }}</label>
        <InputText id="website" v-model="form.website" :placeholder="t('suppliers.placeholders.website')" />
      </div>
      <div class="p-field">
        <label for="notes">{{ t('suppliers.fields.notes') }}</label>
        <Textarea id="notes" v-model="form.notes" :placeholder="t('suppliers.placeholders.notes')" autoResize />
      </div>
      <div class="flex justify-content-end gap-2 mt-4">
        <Button :label="t('common.actions.cancel')" class="p-button-text" @click="emit('cancel')" />
        <Button :label="t('common.actions.save')" type="submit" />
      </div>
    </div>

    <Dialog v-model:visible="showContactDialog" :header="t('suppliers.contacts.new')" :modal="true" :style="{ width: '30vw' }">
      <div class="p-fluid">
        <div class="p-field">
          <label for="contact_name">{{ t('common.fields.name') }} *</label>
          <InputText id="contact_name" v-model="contactForm.name" :placeholder="t('common.placeholders.contactName')" required />
        </div>
        <div class="p-field">
          <label for="contact_email">{{ t('common.fields.email') }} *</label>
          <InputText id="contact_email" v-model="contactForm.email" :placeholder="t('common.placeholders.contactEmail')" required />
        </div>
        <div class="p-field">
          <label for="contact_phone">{{ t('common.fields.phone') }}</label>
          <InputText id="contact_phone" v-model="contactForm.phone" />
        </div>
        <div class="p-field">
          <label for="contact_role">{{ t('common.fields.type') }}</label>
          <InputText id="contact_role" v-model="contactForm.role" />
        </div>
        <div class="flex justify-content-end gap-2 mt-3">
          <Button :label="t('common.actions.cancel')" class="p-button-text" @click="cancelContactDialog" />
          <Button :label="t('common.actions.save')" @click="saveContact" />
        </div>
      </div>
    </Dialog>
  </form>
</template>

<script setup>
import { ref, watch } from 'vue'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  supplier: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['submit', 'cancel'])

const form = ref({
  name: '',
  description: '',
  vat_number: '',
  tax_code: '',
  address: '',
  city: '',
  zip_code: '',
  province: '',
  country: '',
  phone: '',
  email: '',
  website: '',
  notes: '',
  contacts: []
})

watch(() => props.supplier, (newVal) => {
  if (newVal) {
    form.value = {
      name: newVal.name || '',
      description: newVal.description || '',
      vat_number: newVal.vat_number || '',
      tax_code: newVal.tax_code || '',
      address: newVal.address || '',
      city: newVal.city || '',
      zip_code: newVal.zip_code || '',
      province: newVal.province || '',
      country: newVal.country || '',
      phone: newVal.phone || '',
      email: newVal.email || '',
      website: newVal.website || '',
      notes: newVal.notes || '',
      contacts: newVal.contacts ? [...newVal.contacts] : []
    }
  } else {
    form.value = {
      name: '',
      description: '',
      vat_number: '',
      tax_code: '',
      address: '',
      city: '',
      zip_code: '',
      province: '',
      country: '',
      phone: '',
      email: '',
      website: '',
      notes: '',
      contacts: []
    }
  }
}, { immediate: true })

function handleSubmit() {
  emit('submit', { ...form.value })
}

const showContactDialog = ref(false)
const contactForm = ref({ name: '', email: '', phone: '', role: '' })
const editingIndex = ref(null)

function openContactDialog() {
  contactForm.value = { name: '', email: '', phone: '', role: '' }
  editingIndex.value = null
  showContactDialog.value = true
}

function editContact(index) {
  contactForm.value = { ...form.value.contacts[index] }
  editingIndex.value = index
  showContactDialog.value = true
}

function removeContact(index) {
  form.value.contacts.splice(index, 1)
}

function cancelContactDialog() {
  showContactDialog.value = false
}

function saveContact() {
  if (editingIndex.value !== null) {
    form.value.contacts[editingIndex.value] = { ...contactForm.value }
  } else {
    form.value.contacts.push({ ...contactForm.value })
  }
  showContactDialog.value = false
}
</script>
