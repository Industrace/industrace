import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import AssetsFilters from '../../src/components/features/assets/AssetsFilters.vue'

// Mock i18n
const i18n = createI18n({
  legacy: false,
  locale: 'it',
  messages: {
    it: {
      assets: {
        strings: {
          filterbyStatus: 'Filtra per stato',
          filterbySite: 'Filtra per sito',
          filterbyArea: 'Filtra per area',
          filterbyLocation: 'Filtra per posizione',
          advancedFilters: 'Filtri avanzati',
          riskScoreMin: 'Min',
          riskScoreMax: 'Max'
        },
        fields: {
          businessCriticality: 'Criticità Aziendale',
          riskScore: 'Punteggio di Rischio'
        }
      },
      locations: {
        fields: {
          name: 'Posizione'
        }
      },
      common: {
        actions: {
          hide: 'Nascondi'
        }
      }
    }
  }
})

// Mock PrimeVue components
const mockComponents = {
  Dropdown: {
    template: '<select :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot /></select>',
    props: ['modelValue', 'options', 'optionLabel', 'optionValue', 'placeholder', 'showClear'],
    emits: ['update:modelValue']
  },
  Button: {
    template: '<button @click="$emit(\'click\')"><slot /></button>',
    emits: ['click']
  },
  InputNumber: {
    template: '<input type="number" :value="modelValue" @input="$emit(\'update:modelValue\', parseFloat($event.target.value))" />',
    props: ['modelValue', 'placeholder', 'min', 'max', 'mode'],
    emits: ['update:modelValue']
  }
}

describe('AssetsFilters', () => {
  let pinia
  let wrapper
  const mockFilters = {
    status_id: { value: null },
    site_id: { value: null },
    area_id: { value: null },
    location_id: { value: null },
    business_criticality: { value: null },
    risk_score_min: { value: null },
    risk_score_max: { value: null }
  }

  beforeEach(() => {
    pinia = createPinia()
  })

  it('should render base filters', () => {
    wrapper = mount(AssetsFilters, {
      props: {
        filters: mockFilters,
        assetStatusOptions: [],
        sites: [],
        areas: [],
        locations: []
      },
      global: {
        plugins: [pinia, i18n],
        components: mockComponents
      }
    })

    expect(wrapper.find('#filter_status').exists()).toBe(true)
    expect(wrapper.find('#filter_site').exists()).toBe(true)
    expect(wrapper.find('#filter_area').exists()).toBe(true)
  })

  it('should show advanced filters when button is clicked', async () => {
    wrapper = mount(AssetsFilters, {
      props: {
        filters: mockFilters,
        assetStatusOptions: [],
        sites: [],
        areas: [],
        locations: []
      },
      global: {
        plugins: [pinia, i18n],
        components: mockComponents
      }
    })

    // Advanced filters should be hidden initially
    expect(wrapper.find('.filters-advanced').isVisible()).toBe(false)

    // Click the advanced filters button
    const button = wrapper.find('button')
    await button.trigger('click')

    // Advanced filters should be visible now
    expect(wrapper.find('.filters-advanced').isVisible()).toBe(true)
  })

  it('should update filters when dropdown values change', async () => {
    const filters = { ...mockFilters }
    
    wrapper = mount(AssetsFilters, {
      props: {
        filters: filters,
        assetStatusOptions: [{ id: '1', name: 'Active' }],
        sites: [{ id: '1', name: 'Site 1' }],
        areas: [{ id: '1', name: 'Area 1' }],
        locations: []
      },
      global: {
        plugins: [pinia, i18n],
        components: mockComponents
      }
    })

    const statusDropdown = wrapper.find('#filter_status')
    await statusDropdown.setValue('1')

    expect(filters.status_id.value).toBe('1')
  })

  it('should render advanced filters section with all fields', async () => {
    wrapper = mount(AssetsFilters, {
      props: {
        filters: mockFilters,
        assetStatusOptions: [],
        sites: [],
        areas: [],
        locations: [{ id: '1', name: 'Location 1' }]
      },
      global: {
        plugins: [pinia, i18n],
        components: mockComponents
      }
    })

    // Show advanced filters
    const button = wrapper.find('button')
    await button.trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.find('#filter_location').exists()).toBe(true)
    expect(wrapper.find('#filter_business_criticality').exists()).toBe(true)
    expect(wrapper.find('#filter_risk_score_min').exists()).toBe(true)
    expect(wrapper.find('#filter_risk_score_max').exists()).toBe(true)
  })

  it('should have correct business criticality options', () => {
    wrapper = mount(AssetsFilters, {
      props: {
        filters: mockFilters,
        assetStatusOptions: [],
        sites: [],
        areas: [],
        locations: []
      },
      global: {
        plugins: [pinia, i18n],
        components: mockComponents
      }
    })

    // Check that businessCriticalityOptions are defined
    expect(wrapper.vm.businessCriticalityOptions).toBeDefined()
    expect(wrapper.vm.businessCriticalityOptions.length).toBe(4)
    expect(wrapper.vm.businessCriticalityOptions.map(o => o.value)).toEqual(['low', 'medium', 'high', 'critical'])
  })
})
