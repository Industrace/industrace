import { describe, it, expect, beforeEach } from 'vitest'
import i18n from '../../src/locales/loader-final.js'

describe('i18n interpolation', () => {
  beforeEach(() => {
    i18n.global.locale.value = 'en'
  })

  it('interpolates footer copyright year', () => {
    expect(i18n.global.t('footer.copyright', { year: 2026 })).toBe(
      '© 2026 Industrace — AGPL v3 License'
    )
  })

  it('interpolates network probes overview counts', () => {
    expect(
      i18n.global.t('networkProbes.overview.activeOfTotal', { active: 0, total: 2 })
    ).toBe('0 active of 2')
  })

  it('interpolates network probe details title', () => {
    expect(i18n.global.t('networkProbes.details.title', { name: 'Labprobe' })).toBe(
      'Details: Labprobe'
    )
  })

  it('interpolates asset network interfaces summary', () => {
    expect(
      i18n.global.t('assets.strings.networkInterfacesSummary', { count: 3 })
    ).toBe('Network interfaces (3)')
  })

  it('interpolates asset risk alert score', () => {
    expect(i18n.global.t('assets.alerts.criticalMessage', { score: '8.50' })).toContain('8.50')
    expect(i18n.global.t('assets.alerts.criticalMessage', { score: '8.50' })).not.toContain('{score}')
    expect(i18n.global.t('assets.alerts.criticalMessage', { score: '8.50' })).not.toContain('{{score}}')
  })

  it('interpolates common bulk action messages', () => {
    expect(i18n.global.t('common.confirmRestore', { count: 5 })).toBe(
      'Are you sure you want to restore 5 items?'
    )
    expect(i18n.global.t('common.actions.selectedItems', { count: 3 })).toBe('3 items selected')
  })

  it('interpolates Italian locale', () => {
    i18n.global.locale.value = 'it'
    expect(i18n.global.t('footer.copyright', { year: 2026 })).toBe(
      '© 2026 Industrace — Licenza AGPL v3'
    )
    expect(
      i18n.global.t('assets.strings.networkInterfacesSummary', { count: 2 })
    ).toBe('Interfacce di Rete (2)')
  })
})
