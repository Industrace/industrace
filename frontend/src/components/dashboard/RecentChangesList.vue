<template>
  <div class="recent-changes-list">
    <div v-if="loading" class="loading">
      <i class="pi pi-spin pi-spinner"></i>
    </div>
    <div v-else-if="changes.length === 0" class="no-data">
      {{ t('dashboard.change.noRecentChanges') }}
    </div>
    <div v-else class="changes-container">
      <div
        v-for="change in changes"
        :key="change.asset_id"
        class="change-item"
      >
        <div class="change-icon">
          <i :class="change.change_type === 'created' ? 'pi pi-plus-circle' : 'pi pi-sync'"></i>
        </div>
        <div class="change-content">
          <router-link :to="`/assets/${change.asset_id}`" class="change-link">
            {{ change.asset_name }}
          </router-link>
          <div class="change-meta">
            <span class="change-type">
              {{ change.change_type === 'created' ? t('dashboard.change.created') : t('dashboard.change.updated') }}
            </span>
            <span class="change-time">{{ formatTimeAgo(change.timestamp) }}</span>
          </div>
        </div>
      </div>
      <div class="view-all">
        <router-link :to="viewAllLink" class="view-all-link">
          {{ t('dashboard.actions.viewAll') }}
          <i class="pi pi-arrow-right"></i>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  changes: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const viewAllLink = computed(() => {
  // Link to assets page (sorted by updated_at desc to show recent changes first)
  return '/assets?sort=updated_at&order=desc'
})

const formatTimeAgo = (timestamp) => {
  if (!timestamp) return ''
  
  const now = new Date()
  const time = new Date(timestamp)
  const diffMs = now - time
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  
  if (diffMins < 1) {
    return t('dashboard.change.justNow')
  } else if (diffMins < 60) {
    return t('dashboard.change.minutesAgo', { count: diffMins })
  } else if (diffHours < 24) {
    return t('dashboard.change.hoursAgo', { count: diffHours })
  } else {
    return t('dashboard.change.daysAgo', { count: diffDays })
  }
}
</script>

<style scoped>
.recent-changes-list {
  min-height: 200px;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: #6c757d;
}

.loading i {
  font-size: 2rem;
}

.no-data {
  text-align: center;
  padding: 2rem;
  color: #6c757d;
  font-style: italic;
}

.changes-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.change-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 0.5rem;
  transition: background 0.2s ease;
}

.change-item:hover {
  background: #e9ecef;
}

.change-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #667eea;
  color: white;
  font-size: 0.875rem;
  flex-shrink: 0;
}

.change-content {
  flex: 1;
  min-width: 0;
}

.change-link {
  display: block;
  font-weight: 600;
  color: #2c3e50;
  text-decoration: none;
  margin-bottom: 0.25rem;
}

.change-link:hover {
  color: #667eea;
  text-decoration: underline;
}

.change-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: #6c757d;
}

.change-type {
  text-transform: capitalize;
}

.change-time {
  color: #adb5bd;
}

.view-all {
  margin-top: 0.5rem;
  padding-top: 0.75rem;
  border-top: 1px solid #e9ecef;
}

.view-all-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.875rem;
  transition: gap 0.2s ease;
}

.view-all-link:hover {
  gap: 0.75rem;
  text-decoration: none;
}
</style>

