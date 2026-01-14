<template>
  <div class="d-flex flex-wrap align-items-center gap-2 mb-3">
    <h2><i class="fas fa-cogs"></i> Machine Usage 甘特圖</h2>

  

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

interface MachineSegment {
  LotId: string
  Step: string
  Product: string
  Start: string
  End: string
}

interface MachineData {
  Machine: string
  Segments: MachineSegment[]
}

interface GanttTask {
  id: number | string
  text: string
  start_date?: string | Date
  end_date?: string | Date
  open?: boolean
  parent?: number | string
  lot?: string
  step?: string
  product?: string
}

const { setTheme } = useTheme()
const allData = ref<MachineData[]>([])
const filteredData = ref<MachineData[]>([])
const currentScale = ref('day')
const selectedMachine = ref('ALL')
const ganttRef = ref<any>(null)

const uniqueMachines = computed(() => {
  return [...new Set(allData.value.map(d => d.Machine))].sort()
})

const ganttData = computed(() => {
  const tasks: GanttTask[] = []
  let taskId = 1

  filteredData.value.forEach(machine => {
    const machineId = taskId++
    tasks.push({
      id: machineId,
      text: machine.Machine,
      open: true
    })

    if (machine.Segments) {
      machine.Segments.forEach(seg => {
        tasks.push({
          id: taskId++,
          text: `${seg.LotId} (${seg.Step})`,
          start_date: formatDate(seg.Start),
          end_date: formatDate(seg.End),
          parent: machineId,
          lot: seg.LotId,
          step: seg.Step,
          product: seg.Product
        })
      })
    }
  })

  return { data: tasks, links: [] }
})

const ganttConfig = computed(() => ({
  xml_date: "%Y-%m-%d %H:%i:%s",
  layout: {
    css: "gantt_container",
    rows: [
      {
        cols: [
          { view: "grid", width: 300, scrollY: "scrollVer" },
          { view: "timeline", scrollX: "scrollHor", scrollY: "scrollVer" },
          { view: "scrollbar", id: "scrollVer" }
        ]
      },
      { view: "scrollbar", id: "scrollHor", height: 20 }
    ]
  },
  scale_unit: gantt.config.scale_unit,
  date_scale: gantt.config.date_scale,
  subscales: gantt.config.subscales,
  scale_height: gantt.config.scale_height
}))

const loadData = async () => {
  try {
    const response = await axios.get<MachineData[]>(`http://127.0.0.1:5000/get_json/machine_usage.json`)
    allData.value = response.data
    applyFilter()
  } catch (error) {
    console.error("載入數據時發生錯誤:", error)
  }
}

const applyFilter = () => {
  filteredData.value = (selectedMachine.value === "ALL")
    ? allData.value
    : allData.value.filter(d => d.Machine === selectedMachine.value)
}

const handleScaleChange = (scale: string) => {
  currentScale.value = scale
  setGanttScale(scale)
}

onMounted(() => {
  gantt.templates.task_text = function (start, end, task) {
    return task.text
  }
  
  setGanttScale(currentScale.value)
  loadData()
})
</script>
