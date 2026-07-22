// auth.js
// Store per la gestione dell'autenticazione
// Utilizza defineStore per creare lo store
// Utilizza ref per creare le variabili reactive
// Utilizza router per navigare tra le pagine
// Utilizza api per effettuare le richieste all'API
// Utilizza pinia-plugin-persistedstate per salvare lo stato nel localStorage

import { defineStore } from 'pinia'
import { ref } from 'vue'
import router from '../router'
import api from '../api/api'

export const useAuthStore = defineStore('auth', () => {

let refreshIntervalId = null
let lastActivity = Date.now()

function setupActivityListeners() {
  ['click', 'mousemove', 'keydown'].forEach(event => {
    window.addEventListener(event, () => {
      lastActivity = Date.now()
    })
  })
}

function startTokenRefresh(intervalMinutes = 5) {
  if (refreshIntervalId !== null) return // già avviato

  setupActivityListeners()
  refreshIntervalId = setInterval(async () => {
    const minutesSinceLastActivity = (Date.now() - lastActivity) / 1000 / 60
    if (!isAuthenticated.value || minutesSinceLastActivity > 10) return

    try {
      await api.refresh()
  } catch (err) {
    // Token refresh failed, logout user
    logout()
    }
  }, intervalMinutes * 60 * 1000)
}

function stopTokenRefresh() {
  if (refreshIntervalId !== null) {
    clearInterval(refreshIntervalId)
    refreshIntervalId = null
  }
}


  const user = ref(null)
  const isAuthenticated = ref(false)
  const mfaPending = ref(false)

async function login(email, password) {
  try {
    const data = await api.login(email, password)
    if (data?.mfa_required && data?.mfa_token) {
      mfaPending.value = true
      sessionStorage.setItem('mfa_token', data.mfa_token)
      return { mfaRequired: true }
    }
    if (data?.mfa_setup_required && data?.mfa_setup_token) {
      sessionStorage.setItem('mfa_setup_token', data.mfa_setup_token)
      return { mfaSetupRequired: true }
    }
    await fetchUser()
    isAuthenticated.value = true
    mfaPending.value = false
    startTokenRefresh()
    return { mfaRequired: false }
  } catch (error) {
    const body = error.response?.data
    if (body?.mfa_setup_required && body?.mfa_setup_token) {
      sessionStorage.setItem('mfa_setup_token', body.mfa_setup_token)
      return { mfaSetupRequired: true }
    }
    throw error
  }
}

async function verifyMfa(mfaToken, code) {
  await api.verifyMfa(mfaToken, code)
  mfaPending.value = false
  await fetchUser()
  isAuthenticated.value = true
  startTokenRefresh()
}

  async function fetchUser(suppressLogout = false) {
    try {
      const response = await api.getCurrentUser()
      user.value = response.data
      isAuthenticated.value = true
    } catch (error) {
      // Only logout if suppressLogout is false
      // This is useful for SSO where we have a valid token but fetchUser might fail temporarily
      if (!suppressLogout) {
        logout()
      } else {
        // Just log the error but don't logout
        // Keep isAuthenticated as is - if we have a token, the router guard will verify it
        // Don't change isAuthenticated - let the router guard verify the token
      }
    }
  }

async function logout() {
  try {
    await api.logout()
  } catch (e) {
    // anche se fallisce, prosegui col logout locale
  }
  // Clear all authentication data
  user.value = null
  isAuthenticated.value = false
  mfaPending.value = false
  sessionStorage.removeItem('mfa_token')
  sessionStorage.removeItem('mfa_setup_token')
  stopTokenRefresh()
  
  router.push('/login')
}
  return {
    user,
    isAuthenticated,
    mfaPending,
    login,
    verifyMfa,
    logout,
    fetchUser,
    startTokenRefresh,
    stopTokenRefresh
  }
}, {
  persist: true   
}
)
