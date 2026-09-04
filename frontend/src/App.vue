<template>
  <div class="app-container">
    <Toast />
    <SetupDetector />
    <div v-if="auth.isAuthenticated" class="layout">
      <SidebarMenu />
      <div class="main-content">
        <router-view />
      </div>
    </div>
    <div v-else>
      <router-view />
    </div>
    <GlobalSearchSpotlight />
    <BaseFooter v-if="auth.isAuthenticated" />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './store/auth'

import Toast from 'primevue/toast'
import SidebarMenu from './components/common/SidebarMenu.vue'
import GlobalSearchSpotlight from './components/common/GlobalSearchSpotlight.vue'
import BaseFooter from './components/common/BaseFooter.vue'
import SetupDetector from './components/SetupDetector.vue'

const auth = useAuthStore()

onMounted(async () => {
  if (!auth.isAuthenticated) {
    await auth.fetchUser()
  }
  if (auth.isAuthenticated) {
    auth.startTokenRefresh()
  }
})
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.layout {
  display: flex;
  flex: 1;
  min-height: 0;
}
.main-content {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
}
</style>
