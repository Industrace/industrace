import { ref } from 'vue'
import { useToast } from 'primevue/usetoast'
import { useI18n } from 'vue-i18n'

/**
 * Composable standardizzato per la gestione delle conferme e azioni distruttive
 * Fornisce conferme, azioni bulk e gestione errori uniforme
 */
export function useConfirm() {
  const showConfirmDialog = ref(false)
  const confirmData = ref(null)
  const toast = useToast()
  const { t } = useI18n()

  /**
   * Mostra dialog di conferma per eliminazione
   * @param {Object} item - Elemento da eliminare
   * @param {string} itemName - Nome dell'elemento
   * @param {Function} onConfirm - Callback da eseguire se confermato
   * @param {Object} options - Opzioni aggiuntive
   */
  const confirmDelete = (item, itemName, onConfirm, options = {}) => {
    const { 
      message = null, 
      successMessage = null,
      errorContext = '',
      hardDelete = false 
    } = options

    const defaultMessage = hardDelete 
      ? t('common.messages.confirmHardDelete', { name: itemName })
      : t('common.messages.deleteConfirm', { name: itemName })

    confirmData.value = {
      type: 'delete',
      item,
      itemName,
      message: message || defaultMessage,
      successMessage: successMessage || t('common.messages.deleted'),
      errorContext,
      onConfirm,
      hardDelete
    }
    
    showConfirmDialog.value = true
  }

  /**
   * Mostra dialog di conferma per azione generica
   * @param {string} type - Tipo di azione
   * @param {string} title - Titolo del dialog
   * @param {string} message - Messaggio di conferma
   * @param {Function} onConfirm - Callback da eseguire se confermato
   * @param {Object} options - Opzioni aggiuntive
   */
  const confirmAction = (type, title, message, onConfirm, options = {}) => {
    const { successMessage = null, errorContext = '' } = options

    confirmData.value = {
      type,
      title,
      message,
      successMessage,
      errorContext,
      onConfirm
    }
    
    showConfirmDialog.value = true
  }

  /**
   * Esegue l'azione confermata
   */
  const executeConfirmedAction = async () => {
    if (!confirmData.value) return

    const { onConfirm, successMessage, errorContext } = confirmData.value

    try {
      await onConfirm()
      
      if (successMessage) {
        toast.add({
          severity: 'success',
          summary: t('common.messages.success'),
          detail: successMessage,
          life: 3000
        })
      }
      
      closeConfirmDialog()
    } catch (error) {
      const errorCode = error.response?.data?.error_code
      const message = errorCode ? (t(`core.${errorCode}`) !== `core.${errorCode}` ? t(`core.${errorCode}`) : t('core.generic')) : t('core.generic')
      const fullMessage = errorContext ? `${errorContext}: ${message}` : message

      toast.add({
        severity: 'error',
        summary: t('common.messages.error'),
        detail: fullMessage,
        life: 5000
      })
    }
  }

  /**
   * Chiude il dialog di conferma
   */
  const closeConfirmDialog = () => {
    showConfirmDialog.value = false
    confirmData.value = null
  }

  /**
   * Gestisce azioni bulk su elementi multipli
   * @param {Array} items - Elementi selezionati
   * @param {string} action - Azione da eseguire
   * @param {Function} onConfirm - Callback da eseguire
   * @param {Object} options - Opzioni aggiuntive
   */
  const confirmBulkAction = (items, action, onConfirm, options = {}) => {
    const { 
      message = null, 
      successMessage = null,
      errorContext = '' 
    } = options

    const defaultMessage = t('common.confirmBulkAction', { 
      action: t(`actions.${action}`), 
      count: items.length 
    })

    confirmData.value = {
      type: 'bulk',
      items,
      action,
      message: message || defaultMessage,
      successMessage: successMessage || t('common.bulkActionCompleted'),
      errorContext,
      onConfirm
    }
    
    showConfirmDialog.value = true
  }

  /**
   * Gestisce il ripristino di elementi dal cestino
   * @param {Array} items - Elementi da ripristinare
   * @param {Function} onConfirm - Callback da eseguire
   */
  const confirmRestore = (items, onConfirm) => {
    const message = t('common.confirmRestore', { count: items.length })
    
    confirmBulkAction(items, 'restore', onConfirm, {
      message,
      successMessage: t('common.restored')
    })
  }

  /**
   * Gestisce la svuotamento del cestino
   * @param {Function} onConfirm - Callback da eseguire
   */
  const confirmEmptyTrash = (onConfirm) => {
    const message = t('common.confirmEmptyTrash')
    
    confirmAction('emptyTrash', t('common.emptyTrash'), message, onConfirm, {
      successMessage: t('common.trashEmptied')
    })
  }

  return {
    showConfirmDialog,
    confirmData,
    confirmDelete,
    confirmAction,
    confirmBulkAction,
    confirmRestore,
    confirmEmptyTrash,
    executeConfirmedAction,
    closeConfirmDialog
  }
} 