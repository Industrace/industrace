<template>
  <Dialog
    :visible="visible"
    @update:visible="$emit('update:visible', $event)"
    :header="t('sso.guide.title')"
    :modal="true"
    :closable="true"
    :draggable="false"
    :style="{ width: 'min(920px, 95vw)' }"
    :contentStyle="{ maxHeight: '75vh', overflow: 'auto' }"
    class="sso-setup-guide-dialog"
  >
    <p class="guide-intro">{{ t('sso.guide.intro') }}</p>

    <section class="guide-section">
      <h3>{{ t('sso.guide.prerequisites.title') }}</h3>
      <ul>
        <li v-for="(item, index) in prerequisiteItems" :key="`pre-${index}`">{{ item }}</li>
      </ul>
    </section>

    <section class="guide-section">
      <h3>{{ t('sso.guide.step1.title') }}</h3>
      <h4>{{ t('sso.guide.step1.register.title') }}</h4>
      <ol>
        <li v-for="(item, index) in step1RegisterItems" :key="`s1r-${index}`">{{ item }}</li>
      </ol>
      <div class="uri-box">
        <span class="uri-label">{{ t('sso.guide.redirectUriLabel') }}</span>
        <code>{{ callbackUri }}</code>
      </div>
      <h4>{{ t('sso.guide.step1.noteInfo.title') }}</h4>
      <ul>
        <li v-for="(item, index) in step1NoteItems" :key="`s1n-${index}`">{{ item }}</li>
      </ul>
    </section>

    <section class="guide-section">
      <h3>{{ t('sso.guide.step2.title') }}</h3>
      <h4>{{ t('sso.guide.step2.redirect.title') }}</h4>
      <ol>
        <li v-for="(item, index) in step2RedirectItems" :key="`s2r-${index}`">{{ item }}</li>
      </ol>
      <h4>{{ t('sso.guide.step2.permissions.title') }}</h4>
      <ol>
        <li v-for="(item, index) in step2PermissionItems" :key="`s2p-${index}`">{{ item }}</li>
      </ol>
    </section>

    <section class="guide-section">
      <h3>{{ t('sso.guide.step3.title') }}</h3>
      <ol>
        <li v-for="(item, index) in step3Items" :key="`s3-${index}`">{{ item }}</li>
      </ol>
    </section>

    <section class="guide-section">
      <h3>{{ t('sso.guide.step4.title') }}</h3>
      <ol>
        <li v-for="(item, index) in step4Items" :key="`s4-${index}`">{{ item }}</li>
      </ol>
      <ul class="field-list">
        <li v-for="(item, index) in step4Fields" :key="`s4f-${index}`">
          <strong>{{ item.label }}</strong> — {{ item.description }}
        </li>
      </ul>
    </section>

    <section class="guide-section">
      <h3>{{ t('sso.guide.step5.title') }}</h3>
      <ol>
        <li v-for="(item, index) in step5Items" :key="`s5-${index}`">{{ item }}</li>
      </ol>
    </section>

    <section class="guide-section">
      <h3>{{ t('sso.guide.step6.title') }}</h3>
      <ol>
        <li v-for="(item, index) in step6Items" :key="`s6-${index}`">{{ item }}</li>
      </ol>
    </section>

    <section class="guide-section">
      <h3>{{ t('sso.guide.troubleshooting.title') }}</h3>
      <Accordion :multiple="true">
        <AccordionTab
          v-for="(issue, index) in troubleshootingIssues"
          :key="`issue-${index}`"
          :header="issue.title"
        >
          <p><strong>{{ t('sso.guide.troubleshooting.cause') }}</strong> {{ issue.cause }}</p>
          <p><strong>{{ t('sso.guide.troubleshooting.solution') }}</strong> {{ issue.solution }}</p>
        </AccordionTab>
      </Accordion>
    </section>

    <section class="guide-section">
      <h3>{{ t('sso.guide.security.title') }}</h3>
      <ul>
        <li v-for="(item, index) in securityItems" :key="`sec-${index}`">{{ item }}</li>
      </ul>
    </section>

    <template #footer>
      <Button :label="t('common.actions.close')" icon="pi pi-times" @click="$emit('update:visible', false)" />
    </template>
  </Dialog>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import Accordion from 'primevue/accordion'
import AccordionTab from 'primevue/accordiontab'

defineProps({
  visible: { type: Boolean, default: false }
})

defineEmits(['update:visible'])

const { t, tm } = useI18n()

const callbackUri = computed(() => {
  if (typeof window === 'undefined') {
    return 'https://yourdomain.com/api/auth/sso/azure_ad/callback'
  }
  return `${window.location.origin}/api/auth/sso/azure_ad/callback`
})

const asList = (key) => {
  const value = tm(key)
  return Array.isArray(value) ? value : []
}

const asFieldList = (key) => {
  const value = tm(key)
  return Array.isArray(value) ? value : []
}

const prerequisiteItems = computed(() => asList('sso.guide.prerequisites.items'))
const step1RegisterItems = computed(() => asList('sso.guide.step1.register.items'))
const step1NoteItems = computed(() => asList('sso.guide.step1.noteInfo.items'))
const step2RedirectItems = computed(() => asList('sso.guide.step2.redirect.items'))
const step2PermissionItems = computed(() => asList('sso.guide.step2.permissions.items'))
const step3Items = computed(() => asList('sso.guide.step3.items'))
const step4Items = computed(() => asList('sso.guide.step4.items'))
const step4Fields = computed(() => asFieldList('sso.guide.step4.fields'))
const step5Items = computed(() => asList('sso.guide.step5.items'))
const step6Items = computed(() => asList('sso.guide.step6.items'))
const securityItems = computed(() => asList('sso.guide.security.items'))
const troubleshootingIssues = computed(() => asFieldList('sso.guide.troubleshooting.issues'))
</script>

<style scoped>
.guide-intro {
  margin-top: 0;
  color: var(--text-color-secondary);
}

.guide-section {
  margin-bottom: 1.5rem;
}

.guide-section h3 {
  margin: 0 0 0.75rem;
  font-size: 1.1rem;
}

.guide-section h4 {
  margin: 1rem 0 0.5rem;
  font-size: 1rem;
}

.guide-section ol,
.guide-section ul {
  margin: 0.25rem 0 0.75rem;
  padding-left: 1.25rem;
}

.guide-section li {
  margin-bottom: 0.35rem;
  line-height: 1.45;
}

.field-list li {
  list-style: disc;
}

.uri-box {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin: 0.75rem 0 1rem;
  padding: 0.75rem;
  border-radius: 6px;
  background: var(--surface-100);
  border: 1px solid var(--surface-border);
}

.uri-label {
  font-size: 0.85rem;
  font-weight: 600;
}

.uri-box code {
  word-break: break-all;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.9rem;
}
</style>
