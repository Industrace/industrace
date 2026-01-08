<template>
  <router-link :to="clickAction" class="dashboard-card" :class="severityClass">
    <div class="card-icon">
      <i :class="icon"></i>
    </div>
    <div class="card-content">
      <div class="card-value">{{ formattedValue }}</div>
      <div class="card-label">{{ label }}</div>
      <div v-if="subtitle" class="card-subtitle">{{ subtitle }}</div>
    </div>
    <div class="card-arrow">
      <i class="pi pi-arrow-right"></i>
    </div>
  </router-link>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: {
    type: [Number, String],
    required: true
  },
  label: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: null
  },
  icon: {
    type: String,
    required: true
  },
  severity: {
    type: String,
    default: 'info', // info, warning, danger, success
    validator: (value) => ['info', 'warning', 'danger', 'success'].includes(value)
  },
  clickAction: {
    type: String,
    required: true
  }
})

const formattedValue = computed(() => {
  if (typeof props.value === 'number') {
    // Format large numbers
    if (props.value >= 1000) {
      return (props.value / 1000).toFixed(1) + 'k'
    }
    return props.value.toString()
  }
  return props.value
})

const severityClass = computed(() => {
  return `severity-${props.severity}`
})
</script>

<style scoped>
.dashboard-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  text-decoration: none;
  color: inherit;
  transition: all 0.2s ease;
  border-left: 4px solid transparent;
}

.dashboard-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  text-decoration: none;
  color: inherit;
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.severity-info .card-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.severity-warning .card-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.severity-danger .card-icon {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  color: white;
}

.severity-success .card-icon {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  color: white;
}

.severity-info {
  border-left-color: #667eea;
}

.severity-warning {
  border-left-color: #f5576c;
}

.severity-danger {
  border-left-color: #fa709a;
}

.severity-success {
  border-left-color: #43e97b;
}

.card-content {
  flex: 1;
  min-width: 0;
}

.card-value {
  font-size: 2rem;
  font-weight: 700;
  color: #2c3e50;
  line-height: 1;
  margin-bottom: 0.25rem;
}

.card-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 0.25rem;
}

.card-subtitle {
  font-size: 0.75rem;
  color: #6c757d;
  line-height: 1.4;
}

.card-arrow {
  color: #6c757d;
  font-size: 1.25rem;
  flex-shrink: 0;
  transition: transform 0.2s ease;
}

.dashboard-card:hover .card-arrow {
  transform: translateX(4px);
}

@media (max-width: 768px) {
  .dashboard-card {
    padding: 1rem;
  }
  
  .card-value {
    font-size: 1.5rem;
  }
  
  .card-icon {
    width: 40px;
    height: 40px;
    font-size: 1.25rem;
  }
}
</style>

