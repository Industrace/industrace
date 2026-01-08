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
          //console.log('[AUTH] Token refresh eseguito')
  } catch (err) {
    // console.log(err)
    console.warn('[AUTH] Token refresh fallito')
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

async function login(email, password) {
  try {
    await api.login(email, password)
    await fetchUser()
    isAuthenticated.value = true
    startTokenRefresh()
    router.push('/')
  } catch (error) {
    throw error
  }
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
        console.warn('Failed to fetch user, but suppressing logout (token may still be valid):', error)
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
  stopTokenRefresh()
  
  // Remove token from localStorage (critical for logout to work properly)
  // The persist plugin will handle clearing the store state automatically
  // but we need to manually clear the token since it's not part of the store
  localStorage.removeItem('access_token')
  
  router.push('/login')
}
  return { user, isAuthenticated, login, logout, fetchUser,startTokenRefresh,stopTokenRefresh }
}, {
  persist: true   
}
)
