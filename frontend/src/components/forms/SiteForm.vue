<template>
  <form @submit.prevent="handleSubmit">
    <div class="p-fluid">
      <div class="p-field">
        <label for="name">{{ t('common.fields.name') }}</label>
        <InputText id="name" v-model="form.name" required />
      </div>
      
      <div class="p-field">
        <label for="code">{{ t('common.fields.code') }}</label>
        <InputText id="code" v-model="form.code" required />
      </div>
      
      <div class="p-field">
        <label for="address">{{ t('common.fields.address') }}</label>
        <Textarea id="address" v-model="form.address" rows="3" />
      </div>
      
      <div class="p-field">
        <label for="description">{{ t('common.fields.description') }}</label>
        <Textarea id="description" v-model="form.description" rows="3" />
      </div>
      
      <div class="p-field">
        <label for="parent_id">{{ t('sites.fields.parent') }}</label>
        <Dropdown
          id="parent_id"
          v-model="form.parent_id"
          :options="parentOptionsWithNone"
          optionLabel="name"
          optionValue="id"
          :placeholder="t('common.strings.select')"
          class="w-full"
          :showClear="true"
        />
      </div>

      <div class="p-field">
        <label for="review_interval_months">{{ t('sites.fields.reviewIntervalMonths') }}</label>
        <InputNumber
          id="review_interval_months"
          v-model="form.review_interval_months"
          :min="1"
          :max="120"
          showButtons
          class="w-full"
        />
        <small class="text-600">{{ t('sites.fields.reviewIntervalMonthsHint') }}</small>
      </div>
      
      <div class="flex justify-content-end gap-2 mt-4">
        <Button :label="t('common.actions.cancel')" class="p-button-text" @click="handleCancel" />
        <Button :label="t('common.actions.save')" type="submit" />
      </div>
    </div>
  </form>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import Textarea from 'primevue/textarea'
import Dropdown from 'primevue/dropdown'
import InputNumber from 'primevue/inputnumber'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// Props and events
const props = defineProps({
  site: {
    type: Object,
    default: null,
  },
  sites: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['submit', 'cancel'])

// Form state
const form = ref({
  name: '',
  code: '',
  address: '',
  description: '',
  parent_id: null,
  review_interval_months: null
})

// Watch to update the form when a site is edited
watch(
  () => props.site,
  (site) => {
    if (site) {
      form.value = {
        name: site.name || '',
        code: site.code || '',
        address: site.address || '',
        description: site.description || '',
        parent_id: site.parent_id || null,
        review_interval_months: site.review_interval_months ?? null
      }
    } else {
      form.value = {
        name: '',
        code: '',
        address: '',
        description: '',
        parent_id: null,
        review_interval_months: null
      }
    }
  },
  { immediate: true }
)

const parentOptions = computed(() => {
  if (!props.site || !props.site.id) return props.sites
  return props.sites.filter(s => s.id !== props.site.id)
})

const parentOptionsWithNone = computed(() => {
  const options = [
    { id: null, name: t('sites.messages.noParent') },
    ...parentOptions.value
  ]
  return options
})

// Methods
function handleSubmit() {
  emit('submit', { ...form.value })
}

function handleCancel() {
  emit('cancel')
}
</script>

<style scoped>
.p-field {
  margin-bottom: 1.5rem;
}

.p-field:has(.p-dropdown) {
  margin-bottom: 2rem;
}

.p-dropdown {
  min-height: 2.5rem;
}

.p-dropdown .p-dropdown-label {
  font-size: 1rem;
  padding: 0.75rem 1rem;
}

.p-dropdown .p-dropdown-trigger {
  width: 2.5rem;
}
</style>
