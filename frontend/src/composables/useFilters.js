import { ref, computed } from 'vue'

/**
 * Composable standardizzato per la gestione dei filtri e ricerca
 * Fornisce filtri globali, specifici e ricerca con persistenza
 */
export function useFilters(initialFilters = {}, storageKey = null, initialColumns = []) {
  const filters = ref({ ...initialFilters })
  const globalSearch = ref('')
  const selectedColumns = ref(initialColumns)
  const sortField = ref('')
  const sortOrder = ref(1) // 1 per ascendente, -1 per discendente

  /**
   * Carica filtri salvati dal localStorage
   */
  const loadSavedFilters = () => {
    if (!storageKey) return

    try {
      const saved = localStorage.getItem(`${storageKey}_filters`)
      if (saved) {
        const parsed = JSON.parse(saved)
        filters.value = { ...filters.value, ...parsed }
      }

      const savedColumns = localStorage.getItem(`${storageKey}_columns`)
      if (savedColumns) {
        selectedColumns.value = JSON.parse(savedColumns)
      }
    } catch (error) {
      console.warn('Errore nel caricamento filtri salvati:', error)
    }
  }

  /**
   * Salva filtri nel localStorage
   */
  const saveFilters = () => {
    if (!storageKey) return

    try {
      localStorage.setItem(`${storageKey}_filters`, JSON.stringify(filters.value))
      localStorage.setItem(`${storageKey}_columns`, JSON.stringify(selectedColumns.value))
    } catch (error) {
      console.warn('Errore nel salvataggio filtri:', error)
    }
  }

  /**
   * Reset dei filtri ai valori iniziali
   */
  const resetFilters = () => {
    filters.value = { ...initialFilters }
    globalSearch.value = ''
    sortField.value = ''
    sortOrder.value = 1
    saveFilters()
  }

  /**
   * Applica filtro specifico
   * @param {string} field - Campo da filtrare
   * @param {any} value - Valore del filtro
   */
  const setFilter = (field, value) => {
    filters.value[field] = value
    saveFilters()
  }

  /**
   * Rimuove un filtro specifico
   * @param {string} field - Campo da rimuovere
   */
  const clearFilter = (field) => {
    delete filters.value[field]
    saveFilters()
  }

  /**
   * Imposta la ricerca globale
   * @param {string} value - Valore di ricerca
   */
  const setGlobalSearch = (value) => {
    globalSearch.value = value
  }

  /**
   * Imposta l'ordinamento
   * @param {string} field - Campo per l'ordinamento
   * @param {number} order - Direzione (1 o -1)
   */
  const setSort = (field, order = 1) => {
    sortField.value = field
    sortOrder.value = order
  }

  /**
   * Filtra i dati in base ai filtri applicati
   * @param {Array} data - Dati da filtrare
   * @param {Array} searchFields - Campi per la ricerca globale
   * @returns {Array} - Dati filtrati
   */
  const filterData = (data, searchFields = []) => {
    let filtered = [...data]

    // Filtro globale
    if (globalSearch.value) {
      const search = globalSearch.value.toLowerCase()
      filtered = filtered.filter(item => {
        return searchFields.some(field => {
          const value = getNestedValue(item, field)
          return value && value.toString().toLowerCase().includes(search)
        })
      })
    }

    // Filtri specifici
    Object.entries(filters.value).forEach(([field, filterValue]) => {
      if (filterValue !== null && filterValue !== undefined && filterValue !== '') {
        filtered = filtered.filter(item => {
          const value = getNestedValue(item, field)
          
          if (typeof filterValue === 'object' && filterValue.matchMode) {
            return applyFilterMatch(value, filterValue.value, filterValue.matchMode)
          }
          
          return value === filterValue
        })
      }
    })

    // Ordinamento
    if (sortField.value) {
      filtered.sort((a, b) => {
        const aValue = getNestedValue(a, sortField.value)
        const bValue = getNestedValue(b, sortField.value)
        
        if (aValue < bValue) return -1 * sortOrder.value
        if (aValue > bValue) return 1 * sortOrder.value
        return 0
      })
    }

    return filtered
  }

  /**
   * Ottiene il valore di un campo annidato (es: 'user.name')
   * @param {Object} obj - Oggetto
   * @param {string} path - Percorso del campo
   * @returns {any} - Valore del campo
   */
  const getNestedValue = (obj, path) => {
    return path.split('.').reduce((current, key) => {
      return current && current[key] !== undefined ? current[key] : null
    }, obj)
  }

  /**
   * Applica il match mode per i filtri
   * @param {any} value - Valore da confrontare
   * @param {any} filterValue - Valore del filtro
   * @param {string} matchMode - Modalità di confronto
   * @returns {boolean} - True se match
   */
  const applyFilterMatch = (value, filterValue, matchMode) => {
    if (value === null || value === undefined) return false

    const strValue = value.toString().toLowerCase()
    const strFilter = filterValue.toString().toLowerCase()

    switch (matchMode) {
      case 'contains':
        return strValue.includes(strFilter)
      case 'startsWith':
        return strValue.startsWith(strFilter)
      case 'endsWith':
        return strValue.endsWith(strFilter)
      case 'equals':
        return strValue === strFilter
      case 'notEquals':
        return strValue !== strFilter
      case 'in':
        return Array.isArray(filterValue) && filterValue.includes(value)
      case 'notIn':
        return Array.isArray(filterValue) && !filterValue.includes(value)
      default:
        return strValue.includes(strFilter)
    }
  }

  /**
   * Ottiene i parametri per le chiamate API
   * @returns {Object} - Parametri per l'API
   */
  const getApiParams = () => {
    const params = {}
    
    // Extract values from filter objects
    Object.entries(filters.value).forEach(([key, filterObj]) => {
      if (key === 'global') {
        return
      }
      if (filterObj && typeof filterObj === 'object' && 'value' in filterObj) {
        // Filter object with value property
        if (filterObj.value !== null && filterObj.value !== undefined && filterObj.value !== '') {
          params[key] = filterObj.value
        }
      } else if (filterObj !== null && filterObj !== undefined && filterObj !== '') {
        // Direct value
        params[key] = filterObj
      }
    })
    
    const searchValue = filters.value.global?.value ?? globalSearch.value
    if (searchValue) {
      params.global_search = searchValue
    }
    
    if (sortField.value) {
      params.sort_by = sortField.value
      params.sort_order = sortOrder.value === 1 ? 'asc' : 'desc'
    }

    return params
  }

  // Carica filtri salvati all'inizializzazione
  loadSavedFilters()

  return {
    filters,
    globalSearch,
    selectedColumns,
    sortField,
    sortOrder,
    resetFilters,
    setFilter,
    clearFilter,
    setGlobalSearch,
    setSort,
    filterData,
    getApiParams,
    saveFilters
  }
} 