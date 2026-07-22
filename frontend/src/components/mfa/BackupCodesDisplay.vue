<template>
  <div class="backup-codes">
    <p class="warning">{{ t('mfa.backupCodesWarning') }}</p>
    <ul class="codes-list">
      <li v-for="code in codes" :key="code">
        <code>{{ code }}</code>
      </li>
    </ul>
    <div class="actions">
      <Button
        :label="t('mfa.copyAll')"
        icon="pi pi-copy"
        severity="secondary"
        @click="copyAll"
      />
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'

const props = defineProps({
  codes: {
    type: Array,
    required: true
  }
})

const { t } = useI18n()
const toast = useToast()

async function copyAll() {
  try {
    await navigator.clipboard.writeText(props.codes.join('\n'))
    toast.add({
      severity: 'success',
      summary: t('mfa.copied'),
      life: 2000
    })
  } catch (e) {
    console.error(e)
  }
}
</script>

<style scoped>
.backup-codes {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.warning {
  color: var(--orange-700, #c2410c);
  font-size: 0.9rem;
  margin: 0;
}
.codes-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}
.codes-list code {
  display: block;
  padding: 0.5rem 0.75rem;
  background: var(--surface-100, #f4f4f5);
  border-radius: 4px;
  font-family: ui-monospace, monospace;
  letter-spacing: 0.05em;
}
.actions {
  display: flex;
  gap: 0.5rem;
}
</style>
