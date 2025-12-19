
import { createRouter, createWebHistory } from 'vue-router'
import Login from './pages/Login.vue'
import Dashboard from './pages/Dashboard.vue'
import Assets from './pages/Assets.vue'
import AssetDetail from './pages/AssetDetail.vue'
import AssetDetailNew from './pages/AssetDetailNew.vue'
import SiteDetail from './pages/SiteDetail.vue'
import Suppliers from './pages/Suppliers.vue'
import SupplierDetail from './pages/SupplierDetail.vue'
import Manufacturers from './pages/Manufacturers.vue'
import ManufacturerDetail from './pages/ManufacturerDetail.vue'
import AssetTypes from './pages/AssetTypes.vue'
import AssetTypeDetail from './pages/AssetTypeDetail.vue'
import Sites from './pages/Sites.vue'
import Areas from './pages/Areas.vue'
import Users from './pages/Users.vue'
import Utility from './pages/Utility.vue'
import AssetStatuses from './pages/AssetStatuses.vue'
import Locations from './pages/Locations.vue'
import Contacts from './pages/Contacts.vue'
import ContactDetail from './pages/ContactDetail.vue'
import AuditLogs from './pages/AuditLogs.vue'
import Roles from './pages/Roles.vue'
import RoleDetails from './pages/RoleDetails.vue'
import Setup from './pages/Setup.vue'
import SetupWizard from './pages/SetupWizard.vue'
import Profile from './pages/Profile.vue'
import NetworkMap from './pages/NetworkMap.vue'
import AssetReviews from './pages/AssetReviews.vue'
import api from './api/api'
import { useAuthStore } from './store/auth'

const routes = [
  { path: '/login', name: 'Login', component: Login },
  { path: '/', name: 'Dashboard', component: Dashboard, meta: { requiresAuth: true } },
  { path: '/assets', name: 'Assets', component: Assets, meta: { requiresAuth: true } },
  { path: '/assets/:id', name: 'AssetDetail', component: AssetDetail, meta: { requiresAuth: true } },
  { path: '/assets-new/:id', name: 'AssetDetailNew', component: AssetDetailNew, meta: { requiresAuth: true } },
  { path: '/asset-reviews', name: 'AssetReviews', component: AssetReviews, meta: { requiresAuth: true } },
  { path: '/notifications', name: 'Notifications', component: () => import('./pages/Notifications.vue'), meta: { requiresAuth: true } },
  { path: '/security-zones', name: 'SecurityZones', component: () => import('./pages/SecurityZones.vue'), meta: { requiresAuth: true } },
  { path: '/security-zones/:id', name: 'SecurityZoneDetail', component: () => import('./pages/SecurityZoneDetail.vue'), meta: { requiresAuth: true } },
  { path: '/conduits', name: 'Conduits', component: () => import('./pages/Conduits.vue'), meta: { requiresAuth: true } },
  { path: '/compliance', name: 'Compliance', component: () => import('./pages/Compliance.vue'), meta: { requiresAuth: true } },
  { path: '/sso-config', name: 'SSOConfig', component: () => import('./pages/SSOConfig.vue'), meta: { requiresAuth: true } },
  { path: '/sites', name: 'Sites', component: Sites, meta: { requiresAuth: true } },
  { path: '/sites/:id', name: 'SiteDetail', component: SiteDetail, meta: { requiresAuth: true } },
  { path: '/areas', name: 'Areas', component: Areas, meta: { requiresAuth: true } },
  { path: '/suppliers', name: 'Suppliers', component: Suppliers, meta: { requiresAuth: true } },
  { path: '/suppliers/:id', name: 'SupplierDetail', component: SupplierDetail, meta: { requiresAuth: true } },
  { path: '/manufacturers', name: 'Manufacturers', component: Manufacturers, meta: { requiresAuth: true } },
  { path: '/manufacturers/:id', name: 'ManufacturerDetail', component: ManufacturerDetail, meta: { requiresAuth: true } },
  { path: '/asset-types', name: 'AssetTypes', component: AssetTypes, meta: { requiresAuth: true } },
  { path: '/asset-types/:id', name: 'AssetTypeDetail', component: AssetTypeDetail, meta: { requiresAuth: true } },  
  { path: '/utility', name: 'Utility', component: Utility, meta: { requiresAuth: true } },
  { path: '/users', name: 'Users', component: Users, meta: { requiresAuth: true } },
  { path: '/users/:id', name: 'UserDetail', component: () => import('./pages/UserDetail.vue'), meta: { requiresAuth: true } },
  { path: '/asset-statuses', name: 'AssetStatuses', component: AssetStatuses, meta: { requiresAuth: true } },
  { path: '/locations', name: 'Locations', component: Locations, meta: { requiresAuth: true } },
  { path: '/contacts', name: 'Contacts', component: Contacts, meta: { requiresAuth: true } },
  { path: '/contacts/:id', name: 'ContactDetail', component: ContactDetail,meta: { requiresAuth: true }  },
  { path: '/audit-logs', name: 'AuditLogs', component: AuditLogs, meta: { requiresAuth: true } },
  { path: '/roles', name: 'Roles', component: Roles, meta: { requiresAuth: true } },
  { path: '/roles/:id', name: 'RoleDetails', component: RoleDetails, meta: { requiresAuth: true } },
  { path: '/setup', name: 'Setup', component: Setup, meta: { requiresAuth: true } },
  { path: '/setup-wizard', name: 'SetupWizard', component: SetupWizard, meta: { requiresAuth: true } },
  { path: '/vulnerability-feeds', name: 'VulnerabilityFeeds', component: () => import('./pages/VulnerabilityFeeds.vue'), meta: { requiresAuth: true } },
  { path: '/vulnerabilities', name: 'Vulnerabilities', component: () => import('./pages/Vulnerabilities.vue'), meta: { requiresAuth: true } },
  { path: '/vulnerabilities/:id', name: 'VulnerabilityDetail', component: () => import('./pages/VulnerabilityDetail.vue'), meta: { requiresAuth: true } },
  { path: '/profile', name: 'Profile', component: Profile, meta: { requiresAuth: true } },
  { path: '/network-map', name: 'NetworkMap', component: NetworkMap, meta: { requiresAuth: true } },
  { path: '/logout', name: 'Logout', beforeEnter: (to, from, next) => {
    const store = useAuthStore()
    store.logout()
    next('/login')
  } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  if (to.meta.requiresAuth) {
    try {
      await api.getCurrentUser()
      next()
    } catch (error) {
      next('/login')
    }
  } else {
    next()
  }
})

export default router
