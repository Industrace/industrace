import { ref } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useI18n } from 'vue-i18n'

/**
 * Composable standardizzato per la gestione delle chiamate API
 * Fornisce loading, errori, dati e gestione errori uniforme
 */
export function useApi() {
  const loading = ref(false)
  const error = ref(null)
  const data = ref(null)
  const toast = useToast()
  const { t } = useI18n()

  /**
   * Esegue una chiamata API con gestione automatica di loading ed errori
   * @param {Function} apiCall - Funzione che restituisce una Promise
   * @param {Object} options - Opzioni aggiuntive
   * @param {string} options.successMessage - Messaggio di successo
   * @param {string} options.errorContext - Contesto per messaggi di errore
   * @param {boolean} options.showToast - Se mostrare toast di successo/errore
   * @returns {Promise} - Risultato della chiamata API
   */
  const execute = async (apiCall, options = {}) => {
    const { 
      successMessage = null, 
      errorContext = '', 
      showToast = true,
      resetData = false 
    } = options

    loading.value = true
    error.value = null
    
    if (resetData) {
      data.value = null
    }

    try {
      const result = await apiCall()
      
      // Controlla se il risultato ha dati prima di assegnarli
      if (result && result.data !== undefined) {
        data.value = result.data
      }
      
      if (showToast && successMessage) {
        toast.add({
          severity: 'success',
          summary: t('common.messages.success'),
          detail: successMessage,
          life: 3000
        })
      }
      
      return result
    } catch (err) {
      error.value = err
      
      if (showToast) {
        // Gestione errori di validazione dettagliati
        // console.log('API Error Response:', err.response?.data)
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
          const message = errorCode ? (t(`core.${errorCode}`) !== `core.${errorCode}` ? t(`core.${errorCode}`) : t('core.generic')) : t('core.generic')
          const fullMessage = errorContext ? `${errorContext}: ${message}` : message
          
          toast.add({
            severity: 'error',
            summary: t('common.error'),
            detail: fullMessage,
            life: 5000
          })
        }
      }
      
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Reset dello stato
   */
  const reset = () => {
    loading.value = false
    error.value = null
    data.value = null
  }

  return { 
    loading, 
    error, 
    data, 
    execute, 
    reset 
  }
} 