<template>
  <div class="d-flex flex-wrap align-items-center gap-2 mb-3">
    <h2><i class="fas fa-chart-gantt"></i> Machine Usage Gantt - Split Tasks</h2>



    <!-- 視圖切換 -->
    <ScaleSelector :current-scale="currentScale" @scale-change="handleScaleChange" />

    <!-- 機台過濾器 -->
    <div class="d-flex align-items-center gap-2">
      <label for="machineFilter" class="fw-semibold mb-0">
        <i class="fas fa-filter"></i> 機台過濾：
      </label>
      <select id="machineFilter" class="form-select form-select-sm" style="width: 150px;" v-model="selectedMachine" @change="applyFilter">
        <option value="ALL">全部</option>
        <option v-for="machine in uniqueMachines" :key="machine" :value="machine">{{ machine }}</option>
      </select>
    </div>
  </div>

  <GanttChart :data="ganttData" :config="ganttConfig" ref="ganttRef" />
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useTheme } from '../composables/useTheme'
import { setGanttScale, formatDate } from '../utils/ganttUtils'
import GanttChart from '../components/GanttChart.vue'
import ScaleSelector from '../components/ScaleSelector.vue'
import { gantt } from 'dhtmlx-gantt'

interface GanttTask {
  id: number | string
  text: string
  start_date: string
  end_date?: string
  duration?: number
  parent?: number | string | null
  color?: string
  title?: string
}

const { setTheme } = useTheme()
const allData = ref<GanttTask[]>([])
const filteredData = ref<GanttTask[]>([])
const currentScale = ref('day')
const selectedMachine = ref('ALL')
const ganttRef = ref<any>(null)

const uniqueMachines = computed(() => {
  return [...new Set(allData.value.filter(d => d.parent === null || d.parent === undefined).map(d => d.text))].sort()
})

const ganttData = computed(() => {
  const formattedData = filteredData.value.map(task => {
    const formattedTask: any = {
      ...task,
      start_date: formatDate(task.start_date)
    }
    if (task.duration !== undefined) {
      delete formattedTask.end_date
    } else {
      formattedTask.end_date = formatDate(task.end_date || '')
    }
    return formattedTask
  })
  return { data: formattedData, links: [] }
})

const ganttConfig = computed(() => ({
  duration_unit: "hour",
  date_format: "%Y-%m-%d %H:%i",
  columns: [
    { name: "text", label: "Machine", tree: true, width: 200 },
    { name: "start_date", label: "Start", align: "center" }
  ],
  scale_unit: gantt.config.scale_unit,
  date_scale: gantt.config.date_scale,
  subscales: gantt.config.subscales,
  scale_height: gantt.config.scale_height
}))

const loadData = async () => {
  try {
    const response = await axios.get<any>(`http://127.0.0.1:5000/get_json/gantt/machineTaskSegment_New.json`)
    let rawData: GanttTask[] = []
    if (Array.isArray(response.data)) {
      rawData = response.data
    } else if (response.data && response.data.data) {
      rawData = response.data.data
    }
    allData.value = rawData
    applyFilter()
  } catch (error) {
    console.error("載入數據時發生錯誤:", error)
  }
}

const applyFilter = () => {
  filteredData.value = (selectedMachine.value === "ALL")
    ? allData.value
    : allData.value.filter(d => d.parent === selectedMachine.value || d.text === selectedMachine.value)
}

const handleScaleChange = (scale: string) => {
  currentScale.value = scale
  setGanttScale(scale)
}

onMounted(() => {
  gantt.plugins({ tooltip: true })
  gantt.templates.tooltip_text = function(start, end, task) {
    const startStr = gantt.date.date_to_str("%Y-%m-%d %H:%i")(start)
    const endStr = gantt.date.date_to_str("%Y-%m-%d %H:%i")(end)
    return "<b>" + task.text + "</b><br/>Start: " + startStr + "<br/>End: " + endStr
  }

  gantt.templates.task_class = function (start, end, task) {
    let cssClass = ""
    if (task.color) {
      cssClass += "task-" + task.color
    }
    return cssClass
  }

  setGanttScale(currentScale.value)
  loadData()
})
</script>
