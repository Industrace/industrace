import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '@/api/api'
import { useToast } from 'primevue/usetoast'

export function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

/**
 * Print composable — PDF generation is server-side only (ReportLab).
 */
export function usePrint() {
  const { t, locale } = useI18n()
  const toast = useToast()

  const templates = ref([])
  const loading = ref(false)
  const isPrinting = ref(false)
  const selectedTemplate = ref(null)

  const getTemplateName = (template) => {
    if (template.name_translations && template.name_translations[locale.value]) {
      return template.name_translations[locale.value]
    }
    return template.name || template.key
  }

  const getTemplateDescription = (template) => {
    if (template.description_translations && template.description_translations[locale.value]) {
      return template.description_translations[locale.value]
    }
    return template.description || ''
  }

  const availableTemplates = computed(() => {
    return templates.value.map(template => template.key)
  })

  const getTemplate = (key) => {
    return templates.value.find(template => template.key === key)
  }

  const loadTemplates = async () => {
    try {
      loading.value = true
      const response = await api.getPrintTemplates()
      templates.value = response.data
    } catch (error) {
      toast.add({
        severity: 'error',
        summary: t('common.messages.error'),
        detail: t('print.templates.loadError'),
        life: 3000
      })
    } finally {
      loading.value = false
    }
  }

  const generatePrint = async (assetId, templateId, options = {}) => {
    const response = await api.generatePrint(assetId, templateId, options)
    return response.data
  }

  const downloadPrint = async (printId) => {
    const response = await api.downloadPrint(printId)
    return response.data
  }

  /** Generate asset PDF via backend and trigger browser download. */
  const print = async (templateKey, data, options = {}) => {
    try {
      isPrinting.value = true

      if (!templates.value.length) {
        await loadTemplates()
      }

      const template = getTemplate(templateKey)
      if (!template) {
        throw new Error(t('print.templates.notFound'))
      }

      const templateOptions = template.options || {}
      const finalOptions = { ...templateOptions, ...options }

      const response = await generatePrint(data.id, template.id, finalOptions)

      if (response.print_id) {
        const blob = await downloadPrint(response.print_id)
        downloadBlob(
          blob,
          `asset-${data.name}-${new Date().toISOString().split('T')[0]}.pdf`
        )
      }

      toast.add({
        severity: 'success',
        summary: t('common.messages.success'),
        detail: t('print.generation.success'),
        life: 3000
      })
    } catch (error) {
      toast.add({
        severity: 'error',
        summary: t('common.messages.error'),
        detail: t('print.generation.error'),
        life: 3000
      })
      throw error
    } finally {
      isPrinting.value = false
    }
  }

  return {
    templates,
    loading,
    isPrinting,
    selectedTemplate,
    availableTemplates,
    getTemplate,
    getTemplateName,
    getTemplateDescription,
    loadTemplates,
    generatePrint,
    downloadPrint,
    downloadBlob,
    print,
  }
}
