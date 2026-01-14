<template>
  <div class="btn-group me-3" role="group">
    <button
      v-for="scale in scales"
      :key="scale.value"
      class="btn btn-outline-primary btn-sm"
      :class="{ active: currentScale === scale.value }"
      @click="$emit('scale-change', scale.value)"
    >
      <i :class="scale.icon"></i> {{ scale.label }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'

interface ScaleOption {
  value: string
  label: string
  icon: string
}

const scales: ScaleOption[] = [
  { value: 'hour', label: '小時', icon: 'fas fa-clock' },
  { value: 'day', label: '天', icon: 'fas fa-calendar-day' },
  { value: 'week', label: '週', icon: 'fas fa-calendar-week' },
  { value: 'month', label: '月', icon: 'fas fa-calendar-alt' }
]

defineProps<{
  currentScale: string
}>()

defineEmits<{
  'scale-change': [scale: string]
}>()
</script>

<style scoped>
.btn-group .btn.active {
  background-color: var(--bs-primary);
  border-color: var(--bs-primary);
}
</style>
