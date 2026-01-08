<template>
  <div class="role-details-page">
    <div class="page-header flex align-items-center gap-3 mb-4">
      <Button icon="pi pi-arrow-left" class="p-button-text" @click="goBack" />
      <h1 class="m-0">
        <i class="pi pi-lock mr-2" />
        {{ role.id ? t('common.actions.edit') : t('common.actions.create') }}
      </h1>
    </div>

    <Card>
      <template #content>
        <!-- Nome ruolo -->
        <div class="field mb-5">
          <label class="block font-semibold mb-2">{{ t('common.fields.name') }}</label>
          <InputText 
            v-model="role.name" 
            class="w-full" 
            :placeholder="t('common.fields.name')"
            :disabled="loading"
          />
        </div>

        <!-- Permessi -->
        <div class="permissions-container">
          <!-- Categoria: Inventario -->
          <div class="permission-category">
            <h3 class="category-title">{{ t('roles.categories.inventory') }}</h3>
            <div class="permissions-grid">
              <Card v-for="section in sections.filter(s => s.category === 'inventory')" :key="section.key" class="permission-card">
                <template #title>{{ section.label }}</template>
                <template #content>
                  <div class="flex align-items-center gap-3">
                    <Dropdown
                      v-model="role.permissions[section.key]"
                      :options="levels"
                      optionLabel="label"
                      optionValue="value"
                      class="w-full"
                      :disabled="loading"
                    />
                    <Tag 
                      :value="levelLabel(role.permissions[section.key] || 0)" 
                      :severity="levelSeverity(role.permissions[section.key] || 0)"
                      class="min-w-8rem"
                    />
                  </div>
                </template>
              </Card>
            </div>
          </div>

          <!-- Categoria: Gestione Asset -->
          <div class="permission-category">
            <h3 class="category-title">{{ t('roles.categories.asset_management') }}</h3>
            <div class="permissions-grid">
              <Card v-for="section in sections.filter(s => s.category === 'asset_management')" :key="section.key" class="permission-card">
                <template #title>{{ section.label }}</template>
                <template #content>
                  <div class="flex align-items-center gap-3">
                    <Dropdown
                      v-model="role.permissions[section.key]"
                      :options="levels"
                      optionLabel="label"
                      optionValue="value"
                      class="w-full"
                      :disabled="loading"
                    />
                    <Tag 
                      :value="levelLabel(role.permissions[section.key] || 0)" 
                      :severity="levelSeverity(role.permissions[section.key] || 0)"
                      class="min-w-8rem"
                    />
                  </div>
                </template>
              </Card>
            </div>
          </div>

          <!-- Categoria: Compliance -->
          <div class="permission-category">
            <h3 class="category-title">{{ t('roles.categories.compliance') }}</h3>
            <div class="permissions-grid">
              <Card v-for="section in sections.filter(s => s.category === 'compliance')" :key="section.key" class="permission-card">
                <template #title>{{ section.label }}</template>
                <template #content>
                  <div class="flex align-items-center gap-3">
                    <Dropdown
                      v-model="role.permissions[section.key]"
                      :options="levels"
                      optionLabel="label"
                      optionValue="value"
                      class="w-full"
                      :disabled="loading"
                    />
                    <Tag 
                      :value="levelLabel(role.permissions[section.key] || 0)" 
                      :severity="levelSeverity(role.permissions[section.key] || 0)"
                      class="min-w-8rem"
                    />
                  </div>
                </template>
              </Card>
            </div>
          </div>

          <!-- Categoria: Sistema -->
          <div class="permission-category">
            <h3 class="category-title">{{ t('roles.categories.system') }}</h3>
            <div class="permissions-grid">
              <Card v-for="section in sections.filter(s => s.category === 'system')" :key="section.key" class="permission-card">
                <template #title>{{ section.label }}</template>
                <template #content>
                  <div class="flex align-items-center gap-3">
                    <Dropdown
                      v-model="role.permissions[section.key]"
                      :options="levels"
                      optionLabel="label"
                      optionValue="value"
                      class="w-full"
                      :disabled="loading"
                    />
                    <Tag 
                      :value="levelLabel(role.permissions[section.key] || 0)" 
                      :severity="levelSeverity(role.permissions[section.key] || 0)"
                      class="min-w-8rem"
                    />
                  </div>
                </template>
              </Card>
            </div>
          </div>
        </div>

        <!-- Azioni -->
        <div class="flex justify-content-end gap-3 mt-5 pt-4 border-top-1 surface-border">
          <Button 
            :label="t('common.actions.save')" 
            icon="pi pi-save" 
            class="p-button-success" 
            @click="saveRole" 
            :loading="loading"
          />
          <Button 
            :label="t('common.actions.cancel')" 
            icon="pi pi-times" 
            class="p-button-outlined" 
            @click="cancel"
          />
        </div>
      </template>
    </Card>

    <Toast />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Button from 'primevue/button'
import Toast from 'primevue/toast'
import { useToast } from 'primevue/usetoast'
import Card from 'primevue/card'
import Tag from 'primevue/tag'
import api from '../api/api'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const toast = useToast()

const role = ref({ name: '', permissions: {} })
const loading = ref(false)

const sections = [
  // Sezioni esistenti - Inventario
  { key: 'assets', label: t('roles.sections.assets'), category: 'inventory' },
  { key: 'sites', label: t('roles.sections.sites'), category: 'inventory' },
  { key: 'areas', label: t('roles.sections.areas'), category: 'inventory' },
  { key: 'locations', label: t('roles.sections.locations'), category: 'inventory' },
  { key: 'suppliers', label: t('roles.sections.suppliers'), category: 'inventory' },
  { key: 'contacts', label: t('roles.sections.contacts'), category: 'inventory' },
  { key: 'manufacturers', label: t('roles.sections.manufacturers'), category: 'inventory' },
  { key: 'asset_types', label: t('roles.sections.asset_types'), category: 'inventory' },
  { key: 'asset_statuses', label: t('roles.sections.asset_statuses'), category: 'inventory' },
  { key: 'asset_documents', label: t('roles.sections.asset_documents'), category: 'inventory' },
  { key: 'asset_photos', label: t('roles.sections.asset_photos'), category: 'inventory' },
  { key: 'locations_floormap', label: t('roles.sections.locations_floormap'), category: 'inventory' },
  
  // Sezioni esistenti - Sistema
  { key: 'users', label: t('roles.sections.users'), category: 'system' },
  { key: 'roles', label: t('roles.sections.roles'), category: 'system' },
  { key: 'audit_logs', label: t('roles.sections.audit_logs'), category: 'system' },
  { key: 'utility', label: t('roles.sections.utility'), category: 'system' },
  { key: 'reset_user_password', label: t('roles.sections.reset_user_password'), category: 'system' },
  
  // Nuove sezioni - Gestione Asset
  { key: 'vulnerabilities', label: t('roles.sections.vulnerabilities'), category: 'asset_management' },
  { key: 'asset_reviews', label: t('roles.sections.asset_reviews'), category: 'asset_management' },
  { key: 'asset_dependencies', label: t('roles.sections.asset_dependencies'), category: 'asset_management' },
  
  // Nuove sezioni - Compliance
  { key: 'compliance', label: t('roles.sections.compliance'), category: 'compliance' },
  { key: 'security_zones', label: t('roles.sections.security_zones'), category: 'compliance' },
  { key: 'evidence', label: t('roles.sections.evidence'), category: 'compliance' },
  
  // Nuove sezioni - Sistema
  { key: 'notifications', label: t('roles.sections.notifications'), category: 'system' },
  { key: 'sso', label: t('roles.sections.sso'), category: 'system' },
  { key: 'api_keys', label: t('roles.sections.api_keys'), category: 'system' },
]

const levels = [
  { label: t('roles.levels.none'), value: 0 },
  { label: t('roles.levels.read'), value: 1 },
  { label: t('roles.levels.write'), value: 2 },
  { label: t('roles.levels.delete'), value: 3 },
]

function levelLabel(val) {
  const found = levels.find(l => l.value === val)
  return found ? found.label : '-'
}

function levelSeverity(val) {
  switch (val) {
    case 0: return 'secondary'
    case 1: return 'info'
    case 2: return 'success'
    case 3: return 'danger'
    default: return 'secondary'
  }
}

function goBack() {
  router.back()
}

onMounted(async () => {
  const roleId = route.params.id
  if (roleId) {
    loading.value = true
    try {
      const response = await api.getRole(roleId)
      role.value = response.data
    } catch (error) {
      toast.add({ severity: 'error', summary: t('common.error'), detail: t('roles.fetchError'), life: 3000 })
      router.push({ name: 'Roles' })
    } finally {
      loading.value = false
    }
  } else {
    // Nuovo ruolo: inizializza permessi a 0
    role.value = {
      name: '',
      permissions: Object.fromEntries(sections.map(s => [s.key, 0]))
    }
  }
  
  // Assicurati che tutti i permessi siano inizializzati
  sections.forEach(section => {
    if (!(section.key in role.value.permissions)) {
      role.value.permissions[section.key] = 0
    }
  })
})

async function saveRole() {
  if (!role.value.name) {
    toast.add({ severity: 'warn', summary: t('common.messages.warning'), detail: t('roles.strings.nameRequired'), life: 3000 })
    return
  }
  loading.value = true
  try {
    if (role.value.id) {
      await api.updateRole(role.value.id, { name: role.value.name, permissions: role.value.permissions })
      toast.add({ severity: 'success', summary: t('common.messages.success'), detail: t('roles.strings.updated'), life: 2000 })
    } else {
      await api.createRole({ name: role.value.name, permissions: role.value.permissions })
      toast.add({ severity: 'success', summary: t('common.messages.success'), detail: t('roles.strings.created'), life: 2000 })
    }
    router.push({ name: 'Roles' })
  } catch (error) {
    toast.add({ severity: 'error', summary: t('common.messages.error'), detail: t('roles.strings.saveError'), life: 3000 })
  } finally {
    loading.value = false
  }
}

function cancel() {
  router.push({ name: 'Roles' })
}
</script>

<style scoped>
.role-details-page {
  padding: 1rem;
  max-width: 1000px;
  margin: 0 auto;
}

.page-header {
  border-bottom: 1px solid var(--surface-border);
  padding-bottom: 1rem;
}

.permissions-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.permission-category {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.category-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--primary-color);
  margin: 0;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid var(--surface-border);
}

.permissions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.permission-card {
  transition: all 0.2s;
}

.permission-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}
</style> 