#!/usr/bin/env node

/**
 * Validates i18n translation files:
 * - flags unintended {{var}} syntax (vue-i18n expects {var})
 * - reports placeholder names in locale strings
 * - warns when t('key', { params }) in source may be missing matching placeholders
 */

const fs = require('fs')
const path = require('path')

const LOCALES_DIR = path.join(__dirname, '../src/locales')
const SRC_DIR = path.join(__dirname, '../src')
const LANGUAGES = ['en', 'it']
const LOADED_LOCALE_FILES = new Set([
  'common', 'dashboard', 'assets', 'assettypes', 'assetstatuses', 'contacts', 'footer',
  'menu', 'login', 'manufacturers', 'suppliers', 'sites', 'areas', 'locations', 'pcap',
  'setup', 'auditlog', 'profile', 'networkMap', 'print', 'roles', 'users', 'globalsearch',
  'assetReviews', 'notifications', 'isa62443', 'assetDependencies', 'vulnerabilities',
  'sso', 'networkProbes', 'discoveredDevices', 'core'
])

const INTENTIONAL_DOUBLE_BRACE_KEYS = new Set([
  'notifications.useVariables',
  'notifications.subjectPlaceholder'
])

function flattenObject(obj, prefix = '') {
  const flattened = {}
  for (const key in obj) {
    if (!Object.prototype.hasOwnProperty.call(obj, key)) continue
    const newKey = prefix ? `${prefix}.${key}` : key
    const value = obj[key]
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      Object.assign(flattened, flattenObject(value, newKey))
    } else if (typeof value === 'string') {
      flattened[newKey] = value
    }
  }
  return flattened
}

function loadLocaleMessages(lang) {
  const messages = {}
  for (const file of LOADED_LOCALE_FILES) {
    const filePath = path.join(LOCALES_DIR, lang, `${file}.json`)
    if (!fs.existsSync(filePath)) continue
    const data = JSON.parse(fs.readFileSync(filePath, 'utf8'))
    Object.assign(messages, flattenObject(data, file))
  }
  return messages
}

function extractPlaceholders(value) {
  const names = new Set()
  const single = value.matchAll(/\{([a-zA-Z_][a-zA-Z0-9_]*)\}/g)
  for (const match of single) names.add(match[1])
  return names
}

function findDoubleBraceIssues(messages) {
  const issues = []
  for (const [key, value] of Object.entries(messages)) {
    if (typeof value !== 'string') continue
    const doubles = [...value.matchAll(/\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}/g)]
    for (const match of doubles) {
      if (!INTENTIONAL_DOUBLE_BRACE_KEYS.has(key)) {
        issues.push({ key, placeholder: match[1], value })
      }
    }
  }
  return issues
}

function walkSourceFiles(dir, files = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      if (entry.name !== 'node_modules') walkSourceFiles(fullPath, files)
    } else if (/\.(vue|js)$/.test(entry.name)) {
      files.push(fullPath)
    }
  }
  return files
}

function extractBalancedBlock(source, startIndex) {
  if (source[startIndex] !== '{') return null
  let depth = 0
  for (let i = startIndex; i < source.length; i++) {
    const ch = source[i]
    if (ch === '{') depth++
    else if (ch === '}') {
      depth--
      if (depth === 0) return source.slice(startIndex, i + 1)
    }
  }
  return null
}

function extractTopLevelParamNames(block) {
  const inner = block.slice(1, -1)
  const names = []
  let depth = 0
  for (let i = 0; i < inner.length; i++) {
    const ch = inner[i]
    if (ch === '{') depth++
    else if (ch === '}') depth--
    else if (depth === 0) {
      const match = inner.slice(i).match(/^([a-zA-Z_][a-zA-Z0-9_]*)\s*:/)
      if (match) {
        names.push(match[1])
        i += match[0].length - 1
      }
    }
  }
  return names
}

function extractTranslationCalls(source) {
  const calls = []
  const patterns = [/\bt\(\s*['"`]([^'"`]+)['"`]\s*,/g, /\$t\(\s*['"`]([^'"`]+)['"`]\s*,/g]
  for (const pattern of patterns) {
    let match
    while ((match = pattern.exec(source)) !== null) {
      const key = match[1]
      const afterComma = source.slice(match.index + match[0].length)
      const blockStart = afterComma.search(/\{/)
      if (blockStart === -1) continue
      const block = extractBalancedBlock(afterComma, blockStart)
      if (!block) continue
      calls.push({ key, params: extractTopLevelParamNames(block) })
    }
  }
  return calls
}

function main() {
  let hasErrors = false

  console.log('Validating i18n translations...\n')

  for (const lang of LANGUAGES) {
    const messages = loadLocaleMessages(lang)
    const doubleBraceIssues = findDoubleBraceIssues(messages)
    if (doubleBraceIssues.length > 0) {
      hasErrors = true
      console.error(`[${lang}] Invalid {{var}} placeholder syntax:`)
      for (const issue of doubleBraceIssues) {
        console.error(`  - ${issue.key}: use {${issue.placeholder}} instead of {{${issue.placeholder}}}`)
      }
      console.error('')
    }
  }

  const enMessages = loadLocaleMessages('en')
  const sourceFiles = walkSourceFiles(SRC_DIR)
  const paramWarnings = []

  for (const file of sourceFiles) {
    const source = fs.readFileSync(file, 'utf8')
    for (const call of extractTranslationCalls(source)) {
      const message = enMessages[call.key]
      if (typeof message !== 'string') continue
      const expected = extractPlaceholders(message)
      if (expected.size === 0) continue
      const provided = new Set(call.params)
      for (const name of expected) {
        if (!provided.has(name)) {
          paramWarnings.push({
            file: path.relative(path.join(__dirname, '..'), file),
            key: call.key,
            missing: name,
            expected: [...expected],
            provided: [...provided]
          })
        }
      }
    }
  }

  if (paramWarnings.length > 0) {
    hasErrors = true
    console.error('Translation calls missing interpolation params (checked against en):')
    const seen = new Set()
    for (const warning of paramWarnings) {
      const id = `${warning.file}:${warning.key}:${warning.missing}`
      if (seen.has(id)) continue
      seen.add(id)
      console.error(
        `  - ${warning.file}: t('${warning.key}') missing '{${warning.missing}}' (expected: ${warning.expected.join(', ')})`
      )
    }
    console.error('')
  }

  if (hasErrors) {
    process.exit(1)
  }

  console.log('All i18n translation checks passed.')
}

main()
