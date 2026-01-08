import { ref, watch } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useI18n } from 'vue-i18n'

/**
 * Composable standardizzato per la gestione dei form
 * Fornisce validazione, gestione errori e stato del form
 */
export function useForm(initialData = {}, validationSchema = null) {
  const form = ref({ ...initialData })
  const errors = ref({})
  const isSubmitting = ref(false)
  const isDirty = ref(false)
  const toast = useToast()
  const { t } = useI18n()

  /**
   * Reset del form ai valori iniziali
   */
  const reset = () => {
    form.value = { ...initialData }
    errors.value = {}
    isDirty.value = false
    isSubmitting.value = false
  }

  /**
   * Aggiorna il form con nuovi dati
   * @param {Object} newData - Nuovi dati per il form
   */
  const setForm = (newData) => {
    form.value = { ...newData }
    isDirty.value = false
  }

  /**
   * Validazione base del form
   * @returns {boolean} - True se valido
   */
  const validate = () => {
    errors.value = {}
    
    if (!validationSchema) {
      return true
    }

    try {
      validationSchema.validateSync(form.value, { abortEarly: false })
      return true
    } catch (validationErrors) {
      validationErrors.inner.forEach(error => {
        errors.value[error.path] = error.message
      })
      return false
    }
  }

  /**
   * Validazione di un campo specifico
   * @param {string} field - Nome del campo
   * @returns {boolean} - True se valido
   */
  const validateField = (field) => {
    if (!validationSchema) {
      return true
    }

    try {
      validationSchema.validateSyncAt(field, form.value)
      delete errors.value[field]
      return true
    } catch (error) {
      errors.value[field] = error.message
      return false
    }
  }

  /**
   * Esegue il submit del form
   * @param {Function} apiCall - Funzione API da chiamare
   * @param {Object} options - Opzioni aggiuntive
   * @returns {Promise} - Risultato della chiamata API
   */
  const submit = async (apiCall, options = {}) => {
    const { 
      successMessage = null, 
      errorContext = '',
      validateBeforeSubmit = true 
    } = options

    if (validateBeforeSubmit && !validate()) {
      toast.add({
        severity: 'warn',
        summary: t('common.messages.warning'),
        detail: t('form.validationError'),
        life: 3000
      })
      return null
    }

    isSubmitting.value = true

    try {
      const result = await apiCall(form.value)
      
      if (successMessage) {
        toast.add({
          severity: 'success',
          summary: t('common.messages.success'),
          detail: successMessage,
          life: 3000
        })
      }

      isDirty.value = false
      return result
    } catch (err) {
               // Gestione errori di validazione dettagliati dal backend
         if (err.response?.data?.validation_errors) {
           const validationErrors = err.response.data.validation_errors
           // Mappa gli errori di validazione ai campi del form
           validationErrors.forEach(error => {
             const field = error.field.split(' -> ').pop() // Prendi solo l'ultimo campo
             // Se abbiamo un error_code, usiamo la traduzione
            if (error.error_code) {
              const translated = t(`core.${error.error_code}`)
              errors.value[field] = translated !== `core.${error.error_code}` ? translated : error.message || t('core.generic')
            } else {
              errors.value[field] = error.message || t('core.generic')
            }
           })
         } else if (err.response?.data?.errors) {
        errors.value = err.response.data.errors
      }

               // Mostra toast con messaggi di errore
         if (err.response?.data?.validation_errors) {
           const validationErrors = err.response.data.validation_errors
           const errorMessages = validationErrors.map(error => {
             // Se abbiamo un error_code, usiamo la traduzione
            if (error.error_code) {
              const translated = t(`core.${error.error_code}`)
              return `${error.field}: ${translated !== `core.${error.error_code}` ? translated : error.message || t('core.generic')}`
            }
            // Altrimenti usiamo il messaggio originale
            return `${error.field}: ${error.message || t('core.generic')}`
           }).join('\n')

           toast.add({
             severity: 'error',
             summary: t('common.error'),
             detail: errorMessages,
             life: 8000
           })
         } else {
        const errorCode = err.response?.data?.error_code
        const translated = errorCode ? t(`core.${errorCode}`) : null
        const message = translated && translated !== `core.${errorCode}` ? translated : (errorCode ? t('core.generic') : t('core.generic'))
        const fullMessage = errorContext ? `${errorContext}: ${message}` : message

        toast.add({
          severity: 'error',
          summary: t('common.error'),
          detail: fullMessage,
          life: 5000
        })
      }

      throw err
    } finally {
      isSubmitting.value = false
    }
  }

  /**
   * Controlla se il form è valido
   */
  const isValid = () => {
    return Object.keys(errors.value).length === 0
  }

  /**
   * Controlla se il form è stato modificato
   */
  const hasChanges = () => {
    return isDirty.value
  }

  // Watch per tracciare modifiche
  watch(form, () => {
    isDirty.value = true
  }, { deep: true })

  return {
    form,
    errors,
    isSubmitting,
    isDirty,
    isValid,
    hasChanges,
    reset,
    setForm,
    validate,
    validateField,
    submit
  }
} 