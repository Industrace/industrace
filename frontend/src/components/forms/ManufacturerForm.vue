
<template>
  <form @submit.prevent="handleSubmit">
    <div class="p-fluid">
      <!-- Manufacturer name -->
      <div class="p-field">
        <label for="name">{{ t('common.fields.name') }}</label>
        <InputText id="name" v-model="form.name" required />
      </div>

      <!-- Description -->
      <div class="p-field">
        <label for="description">{{ t('common.fields.description') }}</label>
        <Textarea id="description" v-model="form.description" autoResize />
      </div>

      <!-- Actions -->
      <div class="flex justify-content-end gap-2 mt-4">
        <Button :label="t('common.actions.cancel')" class="p-button-text" @click="emit('cancel')" />
        <Button :label="t('common.actions.save')" type="submit" />
      </div>
    </div>

  </form>
</template>

<script setup>
import { ref, watch } from 'vue'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Button from 'primevue/button'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  manufacturer: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['submit', 'cancel'])

const form = ref({
  name: '',
  description: ''
})

watch(() => props.manufacturer, (newVal) => {
  if (newVal) {
    form.value = {
      name: newVal.name || '',
      description: newVal.description || ''
    }
  } else {
    form.value = {
      name: '',
      description: ''
    }
  }
}, { immediate: true })

function handleSubmit() {
  emit('submit', { ...form.value })
}

</script> 