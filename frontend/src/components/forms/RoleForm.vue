
<template>
  <form @submit.prevent="handleSubmit">
    <div class="p-fluid">
      <!-- Basic role information -->
      <div class="form-section">
        <h3>{{ t('roles.sections.basicInfo') }}</h3>
        <div class="p-field">
          <label for="name">{{ t('common.fields.name') }} *</label>
          <InputText id="name" v-model="form.name" required maxlength="50" />
        </div>
        
        <div class="p-field">
          <label for="description">{{ t('common.fields.description') }}</label>
          <Textarea id="description" v-model="form.description" rows="3" maxlength="255" />
        </div>

        <div class="p-field">
          <label for="parent_role">{{ t('roles.fields.parentRole') }}</label>
          <Dropdown 
            id="parent_role"
            v-model="form.parent_role_id" 
            :options="parentRoleOptions" 
            optionLabel="name" 
            optionValue="id" 
            :placeholder="t('roles.strings.selectParentRole')"
            showClear
          />
          <small v-if="form.parent_role_id" class="p-text-secondary">
            {{ t('roles.strings.inheritanceInfo') }}
          </small>
        </div>

        <div class="p-field">
          <div class="flex align-items-center">
            <Checkbox 
              id="is_inheritable" 
              v-model="form.is_inheritable" 
              :binary="true"
            />
            <label for="is_inheritable" class="ml-2">
              {{ t('roles.fields.inheritable') }}
            </label>
          </div>
          <small class="p-text-secondary">{{ t('roles.strings.inheritableDescription') }}</small>
        </div>

        <div class="p-field">
          <div class="flex align-items-center">
            <Checkbox 
              id="is_active" 
              v-model="form.is_active" 
              :binary="true"
            />
            <label for="is_active" class="ml-2">
              {{ t('common.fields.active') }}
            </label>
          </div>
        </div>
      </div>
      
      <!-- Permission management -->
      <div class="form-section">
        <h3>{{ t('roles.sections.permissions') }}</h3>
        
        <!-- Preview inherited permissions -->
        <div v-if="inheritedPermissions.length > 0" class="inherited-permissions">
          <h4>{{ t('roles.sections.inheritedPermissions') }}</h4>
          <div class="inherited-grid">
            <div v-for="perm in inheritedPermissions" :key="perm.section" class="inherited-item">
              <i class="pi pi-arrow-down text-primary"></i>
              <span class="section-name">{{ t(`roles.permissions.${perm.section}`) }}</span>
              <Tag :value="getPermissionLabel(perm.level)" severity="info" />
            </div>
          </div>
        </div>

        <!-- Direct permissions -->
        <div class="permissions-container">
          <!-- Categoria: Inventario -->
          <div class="permission-category">
            <h4 class="category-title">{{ t('roles.categories.inventory') }}</h4>
            <div class="permissions-grid">
              <div v-for="(section, sectionKey) in getSectionsByCategory('inventory')" :key="sectionKey" class="permission-section">
                <div class="permission-header">
                  <h4>{{ t(`roles.permissions.${sectionKey}`) }}</h4>
                  <div class="permission-summary">
                    <Tag 
                      :value="getPermissionLabel(form.permissions[sectionKey] || 0)" 
                      :severity="getPermissionSeverity(form.permissions[sectionKey] || 0)"
                    />
                    <span v-if="isInherited(sectionKey)" class="inherited-badge">
                      <i class="pi pi-arrow-down"></i> {{ t('roles.strings.inherited') }}
                    </span>
                  </div>
                </div>
                
                <div class="permission-levels">
                  <div v-for="level in section.levels" :key="level.value" class="permission-level">
                    <RadioButton 
                      :id="`${sectionKey}_${level.value}`"
                      :value="level.value"
                      v-model="form.permissions[sectionKey]"
                      :disabled="isInherited(sectionKey) && level.value <= inheritedLevel(sectionKey)"
                    />
                    <label :for="`${sectionKey}_${level.value}`" class="ml-2">
                      {{ level.label }}
                    </label>
                    <small v-if="level.description" class="level-description">
                      {{ level.description }}
                    </small>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Categoria: Gestione Asset -->
          <div class="permission-category">
            <h4 class="category-title">{{ t('roles.categories.asset_management') }}</h4>
            <div class="permissions-grid">
              <div v-for="(section, sectionKey) in getSectionsByCategory('asset_management')" :key="sectionKey" class="permission-section">
                <div class="permission-header">
                  <h4>{{ t(`roles.permissions.${sectionKey}`) }}</h4>
                  <div class="permission-summary">
                    <Tag 
                      :value="getPermissionLabel(form.permissions[sectionKey] || 0)" 
                      :severity="getPermissionSeverity(form.permissions[sectionKey] || 0)"
                    />
                    <span v-if="isInherited(sectionKey)" class="inherited-badge">
                      <i class="pi pi-arrow-down"></i> {{ t('roles.strings.inherited') }}
                    </span>
                  </div>
                </div>
                
                <div class="permission-levels">
                  <div v-for="level in section.levels" :key="level.value" class="permission-level">
                    <RadioButton 
                      :id="`${sectionKey}_${level.value}`"
                      :value="level.value"
                      v-model="form.permissions[sectionKey]"
                      :disabled="isInherited(sectionKey) && level.value <= inheritedLevel(sectionKey)"
                    />
                    <label :for="`${sectionKey}_${level.value}`" class="ml-2">
                      {{ level.label }}
                    </label>
                    <small v-if="level.description" class="level-description">
                      {{ level.description }}
                    </small>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Categoria: Compliance (solo se modulo IEC 62443 abilitato) -->
          <div v-if="isIec62443Enabled" class="permission-category">
            <h4 class="category-title">{{ t('roles.categories.compliance') }}</h4>
            <div class="permissions-grid">
              <div v-for="(section, sectionKey) in getSectionsByCategory('compliance')" :key="sectionKey" class="permission-section">
                <div class="permission-header">
                  <h4>{{ t(`roles.permissions.${sectionKey}`) }}</h4>
                  <div class="permission-summary">
                    <Tag 
                      :value="getPermissionLabel(form.permissions[sectionKey] || 0)" 
                      :severity="getPermissionSeverity(form.permissions[sectionKey] || 0)"
                    />
                    <span v-if="isInherited(sectionKey)" class="inherited-badge">
                      <i class="pi pi-arrow-down"></i> {{ t('roles.strings.inherited') }}
                    </span>
                  </div>
                </div>
                
                <div class="permission-levels">
                  <div v-for="level in section.levels" :key="level.value" class="permission-level">
                    <RadioButton 
                      :id="`${sectionKey}_${level.value}`"
                      :value="level.value"
                      v-model="form.permissions[sectionKey]"
                      :disabled="isInherited(sectionKey) && level.value <= inheritedLevel(sectionKey)"
                    />
                    <label :for="`${sectionKey}_${level.value}`" class="ml-2">
                      {{ level.label }}
                    </label>
                    <small v-if="level.description" class="level-description">
                      {{ level.description }}
                    </small>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Categoria: Sistema -->
          <div class="permission-category">
            <h4 class="category-title">{{ t('roles.categories.system') }}</h4>
            <div class="permissions-grid">
              <div v-for="(section, sectionKey) in getSectionsByCategory('system')" :key="sectionKey" class="permission-section">
                <div class="permission-header">
                  <h4>{{ t(`roles.permissions.${sectionKey}`) }}</h4>
                  <div class="permission-summary">
                    <Tag 
                      :value="getPermissionLabel(form.permissions[sectionKey] || 0)" 
                      :severity="getPermissionSeverity(form.permissions[sectionKey] || 0)"
                    />
                    <span v-if="isInherited(sectionKey)" class="inherited-badge">
                      <i class="pi pi-arrow-down"></i> {{ t('roles.strings.inherited') }}
                    </span>
                  </div>
                </div>
                
                <div class="permission-levels">
                  <div v-for="level in section.levels" :key="level.value" class="permission-level">
                    <RadioButton 
                      :id="`${sectionKey}_${level.value}`"
                      :value="level.value"
                      v-model="form.permissions[sectionKey]"
                      :disabled="isInherited(sectionKey) && level.value <= inheritedLevel(sectionKey)"
                    />
                    <label :for="`${sectionKey}_${level.value}`" class="ml-2">
                      {{ level.label }}
                    </label>
                    <small v-if="level.description" class="level-description">
                      {{ level.description }}
                    </small>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Actions -->
      <div class="flex justify-content-end gap-2 mt-4">
        <Button :label="t('common.actions.cancel')" class="p-button-text" @click="handleCancel" />
        <Button :label="t('common.actions.save')" type="submit" />
      </div>
    </div>
  </form>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTenantFeatures } from '@/composables/useTenantFeatures'
import { useApi } from '../../composables/useApi'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Dropdown from 'primevue/dropdown'
import Checkbox from 'primevue/checkbox'
import RadioButton from 'primevue/radiobutton'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import api from '../../api/api'

const { t } = useI18n()
const { isIec62443Enabled } = useTenantFeatures()
const { execute } = useApi()

const props = defineProps({
  role: {
    type: Object,
    default: null,
  }
})

const emit = defineEmits(['submit', 'cancel'])

const form = ref({
  name: '',
  description: '',
  permissions: {},
  parent_role_id: null,
  is_inheritable: true,
  is_active: true
})

const parentRoleOptions = ref([])

// Helper function per creare livelli standard
const createStandardLevels = () => [
  { value: 0, label: t('roles.permissions.none'), description: t('roles.permissions.noneDescription') },
  { value: 1, label: t('roles.permissions.read'), description: t('roles.permissions.readDescription') },
  { value: 2, label: t('roles.permissions.write'), description: t('roles.permissions.writeDescription') },
  { value: 3, label: t('roles.permissions.delete'), description: t('roles.permissions.deleteDescription') }
]

// Available permission sections with descriptions, organizzate per categoria
const permissionSections = {
  // Inventario
  assets: { levels: [...createStandardLevels(), { value: 4, label: t('roles.permissions.bulk'), description: t('roles.permissions.bulkDescription') }], category: 'inventory' },
  sites: { levels: createStandardLevels(), category: 'inventory' },
  areas: { levels: createStandardLevels(), category: 'inventory' },
  locations: { levels: createStandardLevels(), category: 'inventory' },
  suppliers: { levels: createStandardLevels(), category: 'inventory' },
  contacts: { levels: createStandardLevels(), category: 'inventory' },
  manufacturers: { levels: createStandardLevels(), category: 'inventory' },
  asset_types: { levels: createStandardLevels(), category: 'inventory' },
  asset_statuses: { levels: createStandardLevels(), category: 'inventory' },
  asset_documents: { levels: createStandardLevels(), category: 'inventory' },
  asset_photos: { levels: createStandardLevels(), category: 'inventory' },
  locations_floormap: { levels: createStandardLevels(), category: 'inventory' },
  
  // Gestione Asset
  vulnerabilities: { levels: createStandardLevels(), category: 'asset_management' },
  asset_reviews: { levels: createStandardLevels(), category: 'asset_management' },
  asset_dependencies: { levels: createStandardLevels(), category: 'asset_management' },
  
  // Compliance
  compliance: { levels: createStandardLevels(), category: 'compliance' },
  security_zones: { levels: createStandardLevels(), category: 'compliance' },
  evidence: { levels: createStandardLevels(), category: 'compliance' },
  
  // Sistema
  users: { levels: createStandardLevels(), category: 'system' },
  roles: { levels: createStandardLevels(), category: 'system' },
  audit_logs: { levels: createStandardLevels(), category: 'system' },
  external_log: { levels: createStandardLevels(), category: 'system' },
  network_probes: { levels: createStandardLevels(), category: 'system' },
  utility: { levels: createStandardLevels(), category: 'system' },
  notifications: { levels: createStandardLevels(), category: 'system' },
  sso: { levels: createStandardLevels(), category: 'system' },
  api_keys: { levels: createStandardLevels(), category: 'system' },
  reset_user_password: {
    levels: [
      { value: 0, label: t('roles.permissions.none'), description: t('roles.permissions.noneDescription') },
      { value: 1, label: t('roles.permissions.resetPassword'), description: t('roles.permissions.resetPasswordDescription') }
    ],
    category: 'system'
  }
}

// Computed properties
const inheritedPermissions = computed(() => {
  if (!form.value.parent_role_id) return []
  
  const parentRole = parentRoleOptions.value.find(r => r.id === form.value.parent_role_id)
  if (!parentRole || !parentRole.permissions) return []
  
  return Object.entries(parentRole.permissions)
    .filter(([section, level]) => level > 0)
    .map(([section, level]) => ({ section, level }))
})

// Initialize permissions for all sections
const initializePermissions = () => {
  const permissions = {}
  Object.keys(permissionSections).forEach(section => {
    permissions[section] = 0
  })
  return permissions
}

// Load available roles for inheritance
const loadParentRoles = async () => {
  await execute(async () => {
    const response = await api.getRoles()
    // Exclude the current role if in edit mode
    const currentRoleId = props.role?.id
    parentRoleOptions.value = response.data.filter(role => role.id !== currentRoleId)
  })
}

// Check if a permission is inherited
const isInherited = (section) => {
  if (!form.value.parent_role_id) return false
  
  const parentRole = parentRoleOptions.value.find(r => r.id === form.value.parent_role_id)
  if (!parentRole || !parentRole.permissions) return false
  
  const parentLevel = parentRole.permissions[section] || 0
  const currentLevel = form.value.permissions[section] || 0
  
  return currentLevel <= parentLevel && parentLevel > 0
}

// Get the inherited level for a section
const inheritedLevel = (section) => {
  if (!form.value.parent_role_id) return 0
  
  const parentRole = parentRoleOptions.value.find(r => r.id === form.value.parent_role_id)
  if (!parentRole || !parentRole.permissions) return 0
  
  return parentRole.permissions[section] || 0
}

// Get the label for a permission level
const getPermissionLabel = (level) => {
  if (level === 0) return t('roles.permissions.none')
  if (level === 1) return t('roles.permissions.read')
  if (level === 2) return t('roles.permissions.write')
  if (level === 3) return t('roles.permissions.delete')
  if (level === 4) return t('roles.permissions.bulk')
  return t('roles.permissions.none')
}

// Get the severity for a permission level
const getPermissionSeverity = (level) => {
  if (level === 0) return 'secondary'
  if (level === 1) return 'info'
  if (level === 2) return 'warning'
  if (level === 3) return 'danger'
  if (level === 4) return 'success'
  return 'secondary'
}

// Get sections by category
const getSectionsByCategory = (category) => {
  const result = {}
  Object.entries(permissionSections).forEach(([key, section]) => {
    if (section.category === category) {
      result[key] = section
    }
  })
  return result
}

// Watch to update the form when a role is edited
watch(
  () => props.role,
  (role) => {
    if (role) {
      form.value = {
        name: role.name || '',
        description: role.description || '',
        permissions: { ...role.permissions } || initializePermissions(),
        parent_role_id: role.parent_role_id || null,
        is_inheritable: role.is_inheritable !== false,
        is_active: role.is_active !== false
      }
    } else {
      form.value = {
        name: '',
        description: '',
        permissions: initializePermissions(),
        parent_role_id: null,
        is_inheritable: true,
        is_active: true
      }
    }
  },
  { immediate: true }
)

// Methods
function handleSubmit() {
  emit('submit', { ...form.value })
}

function handleCancel() {
  emit('cancel')
}

// Load roles on mount
onMounted(() => {
  loadParentRoles()
})
</script>

<style scoped>
.form-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #fafafa;
}

.form-section h3 {
  margin: 0 0 1.5rem 0;
  color: #333;
  font-size: 1.2rem;
  font-weight: 600;
}

.p-field {
  margin-bottom: 1.5rem;
}

.inherited-permissions {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #e3f2fd;
  border-radius: 6px;
  border-left: 4px solid #2196f3;
}

.inherited-permissions h4 {
  margin: 0 0 1rem 0;
  color: #1976d2;
  font-size: 1rem;
}

.inherited-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.5rem;
}

.inherited-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: white;
  border-radius: 4px;
}

.section-name {
  font-weight: 500;
  flex: 1;
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
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--primary-color);
  margin: 0 0 0.5rem 0;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid var(--surface-border);
}

.permissions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.permission-section {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1rem;
  background: white;
}

.permission-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #f0f0f0;
}

.permission-header h4 {
  margin: 0;
  color: #333;
  font-size: 1rem;
  font-weight: 600;
}

.permission-summary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.inherited-badge {
  font-size: 0.8rem;
  color: #2196f3;
  font-weight: 500;
}

.permission-levels {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.permission-level {
  display: flex;
  align-items: flex-start;
  padding: 0.5rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.permission-level:hover {
  background: #f5f5f5;
}

.permission-level label {
  font-size: 0.9rem;
  color: #555;
  cursor: pointer;
  margin-left: 0.5rem;
  flex: 1;
}

.level-description {
  display: block;
  margin-left: 1.5rem;
  margin-top: 0.25rem;
  font-size: 0.8rem;
  color: #666;
  font-style: italic;
}
</style> 