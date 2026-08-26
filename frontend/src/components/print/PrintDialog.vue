<template>
  <Dialog 
    v-model:visible="isVisible" 
    :header="t('print.dialogTitle')"
    :style="{ width: '500px', maxWidth: '90vw' }"
    :modal="true"
    :closable="true"
    class="print-dialog"
  >
    <div class="print-dialog-content-simple">
      <p>{{ t('print.dialogTitle') }}</p>
      <Button 
        :label="t('common.actions.print')" 
        icon="pi pi-print" 
        @click="handlePrint"
        :loading="isPrinting || loading"
        :disabled="loading || isPrinting || !data"
        severity="primary"
        class="mt-3"
      />
    </div>
  </Dialog>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { usePrint } from '@/composables/usePrint'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'

const { t, locale } = useI18n()
const { print, isPrinting, loading, loadTemplates } = usePrint()

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  data: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:visible', 'printed'])

const isVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      loadTemplates()
    }
  },
  { immediate: true }
)

const handlePrint = async () => {
  if (!props.data) return
  try {
    await print('asset-card', props.data, { language: locale.value })
    emit('printed', { template: 'asset-card', data: props.data })
    isVisible.value = false
  } catch (error) {
    // Error handling already done in usePrint
  }
}
</script>

<style scoped>
.print-dialog-content-simple {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 120px;
  text-align: center;
}
</style>
