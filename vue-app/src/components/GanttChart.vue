<template>
  <div ref="ganttContainer" class="gantt-container"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { gantt } from 'dhtmlx-gantt'

interface GanttTask {
  id: number | string
  text: string
  start_date: string
  end_date?: string
  duration?: number
  parent?: number | string
  color?: string
  [key: string]: any
}

interface GanttLink {
  id: number | string
  source: number | string
  target: number | string
  type: string
}

interface GanttData {
  data: GanttTask[]
  links?: GanttLink[]
}

interface Props {
  data: GanttData
  config?: {
    columns?: any[]
    scale_unit?: string
    date_scale?: string
    subscales?: any[]
    scale_height?: number
    xml_date?: string
    show_links?: boolean
    show_progress?: boolean
    layout?: any
    duration_unit?: string
  }
}

const props = withDefaults(defineProps<Props>(), {
  config: () => ({})
})

const ganttContainer = ref<HTMLElement>()
let isInitialized = false

const initGantt = () => {
  if (!ganttContainer.value || isInitialized) return

  // Configure gantt
  Object.assign(gantt.config, {
    xml_date: "%Y-%m-%d %H:%i",
    show_links: true,
    show_progress: false,
    ...props.config
  })

  // Initialize gantt
  gantt.init(ganttContainer.value)
  isInitialized = true
}

const updateGantt = () => {
  if (!isInitialized) return

  gantt.clearAll()
  gantt.parse(props.data)
}

watch(() => props.data, updateGantt, { deep: true })

watch(() => props.config, (newConfig) => {
  if (!isInitialized) return

  Object.assign(gantt.config, newConfig)
  gantt.render()
}, { deep: true })

onMounted(() => {
  initGantt()
  if (props.data.data.length > 0) {
    updateGantt()
  }
})

onUnmounted(() => {
  if (isInitialized) {
    gantt.clearAll()
    isInitialized = false
  }
})

// Expose gantt instance for parent components
defineExpose({
  gantt
})
</script>
