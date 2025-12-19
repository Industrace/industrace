<template>
  <nav class="asset-detail-sidebar" aria-label="Asset detail navigation">
    <div class="sidebar-header">
      <h2 class="sidebar-title">{{ t('assets.detail.navigation') }}</h2>
    </div>
    <ul class="sidebar-nav" role="list">
      <li v-for="section in sections" :key="section.id" role="listitem">
        <a
          :href="`#${section.id}`"
          :class="['nav-link', { active: activeSection === section.id }]"
          @click.prevent="scrollToSection(section.id)"
          :aria-current="activeSection === section.id ? 'page' : undefined"
        >
          <i :class="section.icon"></i>
          <span>{{ section.label }}</span>
          <Badge v-if="section.badge" :value="section.badge" :severity="section.badgeSeverity" class="nav-badge" />
        </a>
        <ul v-if="section.subsections" class="sub-nav">
          <li v-for="subsection in section.subsections" :key="subsection.id" role="listitem">
            <a
              :href="`#${subsection.id}`"
              :class="['nav-link sub-link', { active: activeSection === subsection.id }]"
              @click.prevent="scrollToSection(subsection.id)"
              :aria-current="activeSection === subsection.id ? 'page' : undefined"
            >
              <span>{{ subsection.label }}</span>
            </a>
          </li>
        </ul>
      </li>
    </ul>
  </nav>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import Badge from 'primevue/badge'

const props = defineProps({
  sections: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['section-change'])

const { t } = useI18n()
const activeSection = ref('overview')

const scrollToSection = (sectionId) => {
  const element = document.getElementById(sectionId)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
    activeSection.value = sectionId
    emit('section-change', sectionId)
  }
}

const handleScroll = () => {
  const sections = props.sections.flatMap(s => 
    s.subsections ? [s, ...s.subsections] : [s]
  )
  
  for (const section of sections) {
    const element = document.getElementById(section.id)
    if (element) {
      const rect = element.getBoundingClientRect()
      if (rect.top <= 100 && rect.bottom >= 100) {
        activeSection.value = section.id
        break
      }
    }
  }
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
  handleScroll() // Check initial position
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.asset-detail-sidebar {
  position: sticky;
  top: 1rem;
  width: 240px;
  background: var(--surface-card);
  border: 1px solid var(--surface-border);
  border-radius: 8px;
  padding: 1rem;
  max-height: calc(100vh - 2rem);
  overflow-y: auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.sidebar-header {
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--surface-border);
}

.sidebar-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-color-secondary);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sidebar-nav {
  list-style: none;
  padding: 0;
  margin: 0;
}

.sidebar-nav > li {
  margin-bottom: 0.25rem;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  color: var(--text-color);
  text-decoration: none;
  border-radius: 6px;
  transition: all 0.2s;
  font-size: 0.95rem;
  cursor: pointer;
}

.nav-link:hover {
  background: var(--surface-hover);
  color: var(--primary-color);
}

.nav-link.active {
  background: var(--primary-color);
  color: white;
  font-weight: 600;
}

.nav-link i {
  font-size: 1rem;
  width: 1.25rem;
  text-align: center;
}

.nav-link span {
  flex: 1;
}

.nav-badge {
  margin-left: auto;
}

.sub-nav {
  list-style: none;
  padding: 0;
  margin: 0.5rem 0 0 0;
  padding-left: 2rem;
}

.sub-link {
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  color: var(--text-color-secondary);
}

.sub-link:hover {
  background: var(--surface-50);
  color: var(--text-color);
}

.sub-link.active {
  background: var(--primary-50);
  color: var(--primary-color);
  font-weight: 500;
}

@media (max-width: 1024px) {
  .asset-detail-sidebar {
    position: relative;
    width: 100%;
    max-height: none;
    margin-bottom: 2rem;
  }
}
</style>

