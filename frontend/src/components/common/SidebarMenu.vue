<template>
  <nav :class="['modern-sidebar', { collapsed }]">
    <div class="sidebar-header">
      <img src="/src/static/industrace_square.png" alt="Industrace" class="logo" v-if="!collapsed" />
      <button class="collapse-btn" @click="collapsed = !collapsed">
        <i :class="collapsed ? 'pi pi-angle-right' : 'pi pi-angle-left'"></i>
      </button>
    </div>
    
    <div class="sidebar-sections">
      <div v-for="section in menuSections" :key="section.label" class="sidebar-section">
        <div class="section-title" v-if="!collapsed">{{ section.label }}</div>
        <router-link v-for="item in section.items" :key="item.label" :to="item.to" class="sidebar-link" :title="item.label">
          <i :class="['pi', item.icon, 'sidebar-icon']"></i>
          <span v-if="!collapsed">{{ item.label }}</span>
        </router-link>
      </div>
    </div>
    <div class="sidebar-lang" v-if="!collapsed">
      <label for="sidebar_language_select" class="sr-only">Lingua</label>
      <span class="lang-flag" v-if="locale === 'it'">🇮🇹</span>
      <span class="lang-flag" v-else>🇬🇧</span>
      <select id="sidebar_language_select" v-model="locale" @change="changeLocale" class="lang-select" aria-label="Lingua">
        <option value="it">Italiano</option>
        <option value="en">English</option>
      </select>
    </div>
    <div class="sidebar-logout">
      <router-link to="/logout" class="sidebar-link logout-link" :title="t('menu.navigation.logout')">
        <i class="pi pi-sign-out sidebar-icon"></i>
        <span v-if="!collapsed">{{ t('menu.navigation.logout') }}</span>
      </router-link>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { usePermissions } from '@/composables/usePermissions'
import { useAuthStore } from '@/store/auth'

const { t, locale } = useI18n()
const router = useRouter()
const collapsed = ref(false)
const { canRead, userPermissions, accessibleSections, refreshUserPermissions } = usePermissions()
const authStore = useAuthStore()

const menuSections = computed(() => {
  const sections = []

  // Sezione Dashboard (sempre prima)
  sections.push({
    label: 'Dashboard',
    items: [
      { label: t('menu.navigation.dashboard'), icon: 'pi-chart-bar', to: '/' }
    ]
  })

  // Sezione Inventario (prima di Gestione)
  const inventoryItems = []
  if (canRead('sites')) inventoryItems.push({ label: t('menu.navigation.sites'), icon: 'pi-building', to: '/sites' })
  if (canRead('areas')) inventoryItems.push({ label: t('menu.navigation.areas'), icon: 'pi-sitemap', to: '/areas' })
  if (canRead('locations')) inventoryItems.push({ label: t('menu.navigation.locations'), icon: 'pi-map', to: '/locations' })
  if (canRead('suppliers')) inventoryItems.push({ label: t('menu.navigation.suppliers'), icon: 'pi-briefcase', to: '/suppliers' })
  if (canRead('manufacturers')) inventoryItems.push({ label: t('menu.navigation.manufacturers'), icon: 'pi-cog', to: '/manufacturers' })
  if (canRead('contacts')) inventoryItems.push({ label: t('menu.navigation.contacts'), icon: 'pi-id-card', to: '/contacts' })
  if (canRead('assets')) inventoryItems.push({ label: t('menu.navigation.assets'), icon: 'pi-server', to: '/assets' })
  
  if (inventoryItems.length > 0) {
    sections.push({
      label: t('menu.section.registry'),
      items: inventoryItems
    })
  }

  // Sezione ISA/IEC 62443
  const isa62443Items = []
  if (canRead('security_zones')) isa62443Items.push({ label: t('menu.navigation.securityZones'), icon: 'pi-shield', to: '/security-zones' })
  if (canRead('compliance')) isa62443Items.push({ label: t('menu.navigation.conduits'), icon: 'pi-link', to: '/conduits' })
  if (canRead('compliance')) isa62443Items.push({ label: t('menu.navigation.compliance'), icon: 'pi-check-circle', to: '/compliance' })
  
  if (isa62443Items.length > 0) {
    sections.push({
      label: t('menu.section.isa62443'),
      items: isa62443Items
    })
  }

  // Sezione Management
  const managementItems = []
  if (canRead('asset_reviews')) managementItems.push({ label: t('menu.navigation.assetReviews'), icon: 'pi-calendar', to: '/asset-reviews' })
  if (canRead('vulnerabilities')) managementItems.push({ label: t('menu.navigation.vulnerabilities'), icon: 'pi-exclamation-triangle', to: '/vulnerabilities' })
  if (canRead('asset_types')) managementItems.push({ label: t('menu.navigation.assettypes'), icon: 'pi-tags', to: '/asset-types' })
  if (canRead('asset_statuses')) managementItems.push({ label: t('menu.navigation.assetstatuses'), icon: 'pi-list', to: '/asset-statuses' })
  
  if (managementItems.length > 0) {
    sections.push({
      label: t('menu.section.management'),
      items: managementItems
    })
  }

  // Sezione Users rimossa - ora accessibile dal Setup

  // Sezione Utility
  const utilityItems = []
  utilityItems.push({ label: t('menu.navigation.networkMap'), icon: 'pi-sitemap', to: '/network-map' }) // Mappa di rete
  utilityItems.push({ label: t('menu.navigation.profile'), icon: 'pi-user', to: '/profile' }) // Profilo sempre visibile
  if (canRead('notifications')) utilityItems.push({ label: t('menu.navigation.notifications'), icon: 'pi-bell', to: '/notifications' })
  if (canRead('utility')) utilityItems.push({ label: t('menu.navigation.pcap'), icon: 'pi-upload', to: '/utility' })
  if (canRead('audit_logs')) utilityItems.push({ label: t('menu.navigation.auditLogs'), icon: 'pi-history', to: '/audit-logs' })
  
  if (utilityItems.length > 0) {
    sections.push({
      label: t('menu.navigation.utility'),
      items: utilityItems
    })
  }

  // Sezione Setup (solo per admin)
  if (canRead('users')) {
    sections.push({
      label: t('menu.navigation.setup'),
      items: [
        { label: t('menu.navigation.setup'), icon: 'pi-wrench', to: '/setup' }
      ]
    })
  }

  return sections
})

function changeLocale(e) {
  locale.value = e.target.value
  localStorage.setItem('user-lang', e.target.value)
}
</script>

<style scoped>
.modern-sidebar {
  width: 260px;
  min-height: 100vh;
  background: #23272f;
  color: #fff;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: width 0.2s;
  border-right: 1px solid #23272f;
}
.modern-sidebar.collapsed {
  width: 70px;
}
.sidebar-header {
  display: flex;
  align-items: center;
  padding: 1.2rem 1rem 1rem 1rem;
  gap: 0.7rem;
  border-bottom: 1px solid #2d323c;
}
.logo {
  width: 150px;
  height: 150px;
}
.app-title {
  font-size: 1.3rem;
  font-weight: bold;
  letter-spacing: 1px;
}
.collapse-btn {
  background: none;
  border: none;
  color: #fff;
  margin-left: auto;
  font-size: 1.2rem;
  cursor: pointer;
}
.sidebar-sections {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin-top: 1.5rem;
}
.sidebar-section {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}
.section-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: #b0b4bb;
  margin: 0 0 0.5rem 1.2rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}
.sidebar-link {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.7rem 1.2rem;
  color: #fff;
  text-decoration: none;
  border-radius: 6px;
  transition: background 0.15s, color 0.15s;
  font-size: 1.05rem;
}
.sidebar-link:hover, .sidebar-link.router-link-exact-active {
  background: #3a4050;
  color: #ffd700;
}
.sidebar-icon {
  font-size: 1.3rem;
  min-width: 1.3rem;
  text-align: center;
}
.sidebar-lang {
  padding: 0 1rem 2rem 1rem;
  margin-top: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.7rem;
}
.lang-select {
  width: 100%;
  padding: 0.4rem 0.7rem;
  border-radius: 6px;
  border: 1px solid #2d323c;
  background: #23272f;
  color: #fff;
  font-size: 1rem;
}
.lang-flag {
  font-size: 1.2rem;
  margin-right: 0.4rem;
}
.sidebar-logout {
  margin-bottom: 1.5rem;
  padding: 0 1rem;
}
.logout-link {
  color: #ff7675;
}
.logout-link:hover {
  background: #2d323c;
  color: #fff;
}

/* Screen reader only class */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.modern-sidebar.collapsed .app-title,
.modern-sidebar.collapsed .section-title,
.modern-sidebar.collapsed .sidebar-link span {
  display: none;
}
.modern-sidebar.collapsed .sidebar-link {
  justify-content: center;
  padding-left: 0.5rem;
  padding-right: 0.5rem;
}
</style> 