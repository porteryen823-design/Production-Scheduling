import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface PlanModel {
  SeqNo: number
  Select: number
  optimization_type: number
  Name: string
  Description: string
  Remark: string
  selected: string
}

interface Lot {
  LotId: string
  Product: string
  Priority: number
  DueDate: string
  Operations?: any[]
}

interface ScheduleInfo {
  ScheduleId: string
  CreateDate: string
}

export const useCreateScheduleJobStore = defineStore('createScheduleJob', () => {
  // State
  const models = ref<PlanModel[]>([])
  const lots = ref<Lot[]>([])
  const productFilter = ref<string>('')
  const scheduleId = ref<string>('')
  const showScheduleSelector = ref(false)
  const availableSchedules = ref<ScheduleInfo[]>([])
  const tempScheduleId = ref<string | null>(null)
  const debugLogs = ref<string[]>([])

  // Getters
  const filteredLots = computed(() => {
    if (!productFilter.value) {
      return lots.value
    }
    return lots.value.filter(lot =>
      lot.Product.toLowerCase().includes(productFilter.value.toLowerCase()) ||
      lot.LotId.toLowerCase().includes(productFilter.value.toLowerCase())
    )
  })

  // Actions
  const setModels = (newModels: PlanModel[]) => {
    models.value = newModels
  }

  const setLots = (newLots: Lot[]) => {
    lots.value = newLots
  }

  const setProductFilter = (filter: string) => {
    productFilter.value = filter
  }

  const setScheduleId = (id: string) => {
    scheduleId.value = id
  }

  const setShowScheduleSelector = (show: boolean) => {
    showScheduleSelector.value = show
  }

  const setAvailableSchedules = (schedules: ScheduleInfo[]) => {
    availableSchedules.value = schedules
  }

  const setTempScheduleId = (id: string | null) => {
    tempScheduleId.value = id
  }

  const addDebugLog = (message: string) => {
    const timestamp = new Date().toISOString()
    const logMessage = `[${timestamp}] ${message}`
    debugLogs.value.push(logMessage)
    console.log(logMessage)
  }

  const clearDebugLogs = () => {
    debugLogs.value = []
  }

  const increasePriority = () => {
    filteredLots.value.forEach(lot => {
      lot.Priority += 10
    })
  }

  const decreasePriority = () => {
    filteredLots.value.forEach(lot => {
      lot.Priority -= 10
    })
  }

  return {
    // State
    models,
    lots,
    productFilter,
    scheduleId,
    showScheduleSelector,
    availableSchedules,
    tempScheduleId,
    debugLogs,

    // Getters
    filteredLots,

    // Actions
    setModels,
    setLots,
    setProductFilter,
    setScheduleId,
    setShowScheduleSelector,
    setAvailableSchedules,
    setTempScheduleId,
    addDebugLog,
    clearDebugLogs,
    increasePriority,
    decreasePriority
  }
})