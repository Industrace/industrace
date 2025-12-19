<template>
  <section 
    :id="sectionId" 
    class="asset-detail-section"
    :class="{ 'always-visible': !collapsible, 'collapsed': collapsible && !isExpanded }"
  >
    <div 
      v-if="collapsible" 
      class="section-header-collapsible"
      @click="toggleSection"
      :aria-expanded="isExpanded"
      :aria-controls="sectionId"
      role="button"
      tabindex="0"
      @keydown.enter="toggleSection"
      @keydown.space.prevent="toggleSection"
    >
      <div class="section-header-content">
        <h3 class="section-title">
          <i :class="icon" v-if="icon"></i>
          {{ title }}
          <Badge v-if="badge" :value="badge" :severity="badgeSeverity" class="section-badge" />
        </h3>
        <p v-if="description" class="section-description">{{ description }}</p>
      </div>
      <i :class="isExpanded ? 'pi pi-chevron-up' : 'pi pi-chevron-down'" class="expand-icon"></i>
    </div>
    <div v-else class="section-header">
      <h2 class="section-title">
        <i :class="icon" v-if="icon"></i>
        {{ title }}
        <Badge v-if="badge" :value="badge" :severity="badgeSeverity" class="section-badge" />
      </h2>
      <p v-if="description" class="section-description">{{ description }}</p>
    </div>
    
    <div 
      v-show="!collapsible || isExpanded" 
      class="section-content"
      :id="`${sectionId}-content`"
    >
      <slot></slot>
    </div>
  </section>
</template>

<script setup>
import { ref, watch } from 'vue'
import Badge from 'primevue/badge'

const props = defineProps({
  sectionId: {
    type: String,
    required: true
  },
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    default: null
  },
  icon: {
    type: String,
    default: null
  },
  collapsible: {
    type: Boolean,
    default: true
  },
  defaultExpanded: {
    type: Boolean,
    default: false
  },
  badge: {
    type: String,
    default: null
  },
  badgeSeverity: {
    type: String,
    default: 'info'
  }
})

const emit = defineEmits(['expanded', 'collapsed'])

const isExpanded = ref(props.defaultExpanded || !props.collapsible)

const toggleSection = () => {
  if (props.collapsible) {
    isExpanded.value = !isExpanded.value
    if (isExpanded.value) {
      emit('expanded')
    } else {
      emit('collapsed')
    }
  }
}

watch(() => props.defaultExpanded, (newVal) => {
  if (props.collapsible) {
    isExpanded.value = newVal
  }
})
</script>

<style scoped>
.asset-detail-section {
  margin-bottom: 2rem;
  scroll-margin-top: 1rem;
}

.section-header,
.section-header-collapsible {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid var(--surface-border);
}

.section-header-collapsible {
  cursor: pointer;
  user-select: none;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  transition: background 0.2s;
  padding: 1rem;
  margin: -1rem -1rem 1rem -1rem;
  border-radius: 8px;
}

.section-header-collapsible:hover {
  background: var(--surface-hover);
}

.section-header-content {
  flex: 1;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-color);
  margin: 0 0 0.5rem 0;
}

.section-title i {
  color: var(--primary-color);
  font-size: 1.25rem;
}

.section-description {
  color: var(--text-color-secondary);
  font-size: 0.95rem;
  margin: 0;
  line-height: 1.5;
}

.expand-icon {
  color: var(--text-color-secondary);
  font-size: 1rem;
  margin-top: 0.25rem;
  transition: transform 0.2s;
}

.section-header-collapsible[aria-expanded="true"] .expand-icon {
  transform: rotate(180deg);
}

.section-badge {
  margin-left: 0.5rem;
}

.section-content {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.asset-detail-section.collapsed .section-content {
  display: none;
}

@media (prefers-reduced-motion: reduce) {
  .section-content {
    animation: none;
  }
  
  .expand-icon {
    transition: none;
  }
}
</style>

