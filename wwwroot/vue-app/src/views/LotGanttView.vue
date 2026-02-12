<template>
  <div class="d-flex flex-wrap align-items-center gap-2 mb-3">
    <h2><i class="fas fa-diagram-project"></i> Lot Process 甘特圖</h2>


    <!-- 視圖切換 -->
    <ScaleSelector :current-scale="currentScale" @scale-change="handleScaleChange" />

    <!-- 產品過濾器 -->
    <div class="d-flex align-items-center gap-2">
      <label for="productFilter" class="fw-semibold mb-0">
        <i class="fas fa-filter"></i> 產品過濾：
      </label>
      <select id="productFilter" class="form-select form-select-sm" style="width: 150px;" v-model="selectedProduct" @change="applyFilter">
        <option value="ALL">全部</option>
        <option v-for="product in uniqueProducts" :key="product" :value="product">{{ product }}</option>
      </select>
    </div>
  </div>

  <GanttChart :data="ganttData" :config="ganttConfig" ref="ganttRef" />
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import api from '../utils/apiConfig'
import { useTheme } from '../composables/useTheme'
import { setGanttScale, generateColorPool, parseDate } from '../utils/ganttUtils'
import GanttChart from '../components/GanttChart.vue'
import ScaleSelector from '../components/ScaleSelector.vue'
import { gantt } from 'dhtmlx-gantt'

interface LotTask {
  LotId: string
  Product: string
  Priority: number
  StepIdx: number
  Step: string
  Machine: string
  Start: string
  End: string
  Booking: number
}

interface GanttTask {
  id: number | string
  text: string
  start_date: Date | string
  end_date?: Date | string
  duration?: number
  parent?: number | string
  color?: string
  type?: string
  lot?: string
  step?: string
  product?: string
}

const { setTheme } = useTheme()
const allData = ref<LotTask[]>([])
const filteredData = ref<LotTask[]>([])
const currentScale = ref('day')
const selectedProduct = ref('ALL')
const productColorMap = ref<Record<string, string>>({})
const ganttRef = ref<any>(null)

const colorPool = generateColorPool()

const uniqueProducts = computed(() => {
  return [...new Set(allData.value.map(d => d.Product))].sort()
})

const ganttData = computed(() => {
  const tasks: GanttTask[] = []
  const links: any[] = []
  let taskId = 1
  const lotParentMap: Record<string, number> = {}
  const taskMap: Record<string, number> = {}
  const lots = [...new Set(filteredData.value.map(d => d.LotId))]

  lots.forEach(lotId => {
    const lotProduct = filteredData.value.find(d => d.LotId === lotId)?.Product || ""
    const bgColor = productColorMap.value[lotProduct] || "#6c757d"

    const id = taskId++
    tasks.push({
      id: id,
      text: lotId,
      open: false,
      type: "project",
      color: bgColor,
      product: lotProduct
    })
    lotParentMap[lotId] = id
  })

  filteredData.value.forEach(row => {
    const id = taskId++
    const color = productColorMap.value[row.Product] || "#cccccc"
    tasks.push({
      id: id,
      text: `${row.Step} (${row.Machine})`,
      start_date: parseDate(row.Start),
      end_date: parseDate(row.End),
      color: color,
      parent: lotParentMap[row.LotId],
      lot: row.LotId,
      step: row.Step,
      product: row.Product
    })
    taskMap[`${row.LotId}_${row.Step}`] = id
  })

  lots.forEach(lotId => {
    const lotOps = filteredData.value.filter(d => d.LotId === lotId)
    lotOps.sort((a, b) => parseDate(a.Start).getTime() - parseDate(b.Start).getTime())
    for (let i = 0; i < lotOps.length - 1; i++) {
      const fromId = taskMap[`${lotOps[i].LotId}_${lotOps[i].Step}`]
      const toId = taskMap[`${lotOps[i + 1].LotId}_${lotOps[i + 1].Step}`]
      if (fromId && toId) {
        links.push({ id: taskId++, source: fromId, target: toId, type: "0" })
      }
    }
  })

  return { data: tasks, links: links }
})

const ganttConfig = computed(() => ({
  columns: [
    { name: "text", label: "批次 / 工序", tree: true, width: 200 },
    { name: "start_date", label: "開始時間", align: "center", width: 150 }
  ],
  xml_date: "%Y-%m-%d %H:%i",
  show_links: true,
  show_progress: false,
  scale_unit: gantt.config.scale_unit,
  date_scale: gantt.config.date_scale,
  subscales: gantt.config.subscales,
  scale_height: gantt.config.scale_height
}))

const loadData = async () => {
  try {
    const response = await api.get('/api/schedule')
    const data = (response.data as any).LotStepResult || []

    // 建立 product → color 映射
    const uniqueProducts = [...new Set(data.map(d => d.Product))]
    uniqueProducts.forEach((p, i) => {
      productColorMap.value[p] = colorPool[i % colorPool.length]
    })

    allData.value = data
    applyFilter()
  } catch (error) {
    console.error("資料載入失敗", error)
    alert("資料載入失敗")
  }
}

const applyFilter = () => {
  filteredData.value = (selectedProduct.value === "ALL")
    ? allData.value
    : allData.value.filter(d => d.Product === selectedProduct.value)
}

const handleScaleChange = (scale: string) => {
  currentScale.value = scale
  setGanttScale(scale)
}

onMounted(() => {
  // 初始化 dhtmlxgantt 的模板和配置
  gantt.plugins({ tooltip: true })
  gantt.templates.tooltip_text = function (start, end, task) {
    const format = gantt.date.date_to_str("%Y-%m-%d %H:%i")
    return `<b>${task.text}</b><br>${format(start)} ~ ${format(end)}`
  }
  gantt.templates.task_class = function (start, end, task) {
    if (task.type === "project") {
      // 讓 Lot 節點的顏色應用到樹狀結構上
      setTimeout(() => {
        const el = gantt.getTaskNode(task.id)
        if (el) {
          const treeContent = el.querySelector(".gantt_tree_content")
          if (treeContent) {
            (treeContent as HTMLElement).style.backgroundColor = task.color || ''
          }
        }
      }, 0)
    }
    return ""
  }

  // 設置初始縮放
  setGanttScale(currentScale.value)
  loadData()
})
</script>
