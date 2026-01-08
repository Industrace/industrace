<template>
  <div class="section-header">
    <div class="header-icon">
      <i :class="icon"></i>
    </div>
    <div class="header-content">
      <h2 class="header-title">{{ title }}</h2>
      <p class="header-description">{{ description }}</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    required: true
  },
  icon: {
    type: String,
    required: true
  }
})
</script>

<style scoped>
.section-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f0f0f0;
}

.header-icon {
  width: 48px;
  height: 48px;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  flex-shrink: 0;
}

.header-content {
  flex: 1;
}

.header-title {
  margin: 0 0 0.25rem 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: #2c3e50;
}

.header-description {
  margin: 0;
  font-size: 0.9rem;
  color: #6c757d;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .section-header {
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .header-title {
    font-size: 1.25rem;
  }
}
</style>

