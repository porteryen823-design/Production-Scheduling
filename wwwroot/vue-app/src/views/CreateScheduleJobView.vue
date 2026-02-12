<template>
  <div class="create-schedule-job-view container-fluid mt-4">
    <div class="row">
      <div class="col-12">
        <h1 class="text-center mb-4">Create Schedule Job</h1>
      </div>
    </div>

    <div class="row">
      <div class="col-12">
        <div class="card">
          <div class="card-body">
            <div class="row">
              <div class="col-md-6">
                <label for="scheduleIdInput" class="form-label">ScheduleId</label>
                <input
                  id="scheduleIdInput"
                  v-model="scheduleId"
                  type="text"
                  class="form-control"
                  placeholder="輸入 ScheduleId..."
                />
              </div>
              <div class="col-md-6 d-flex align-items-end gap-2">
                <button
                  @click="generateScheduleId"
                  class="btn btn-primary"
                >
                  自動編碼 ScheduleId
                </button>
                <button
                  @click="showScheduleSelector = true"
                  class="btn btn-info"
                >
                  選取 ScheduleId
                </button>
                <button
                  @click="saveToWorkshop"
                  class="btn btn-success"
                  :disabled="!scheduleId"
                >
                  存入workshop
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="row">
      <!-- Left side: Models -->
      <div class="col-md-6">
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="card-title mb-0">Models List</h5>
            <button
              @click="loadModelsFromDatabase"
              class="btn btn-outline-primary btn-sm"
            >
              從資料庫讀取
            </button>
          </div>
          <div class="card-body">
            <div class="table-responsive">
              <table class="table table-hover table-bordered">
                <thead class="table-dark">
                  <tr>
                    <th>optimization type</th>
                    <th>Name</th>
                    <th>Select</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="model in models" :key="model.SeqNo">
                    <td>{{ model.optimization_type }}</td>
                    <td>{{ model.Name }}</td>
                    <td>
                      <select
                        v-model="model.selected"
                        class="form-select form-select-sm"
                        @change="updateSelection(model)"
                      >
                        <option value="selected">已選取</option>
                        <option value="unselected">未選取</option>
                      </select>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- Right side: Lot Plans -->
      <div class="col-md-6">
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="card-title mb-0">Lot Plans</h5>
            <button
              @click="loadLotsFromDatabase"
              class="btn btn-outline-primary btn-sm"
            >
              從資料庫讀取
            </button>
          </div>
          <div class="card-body">
            <div class="row">
              <div class="col-md-6">
                <label class="form-label">請輸入過濾條件</label>
                <input
                  v-model="productFilter"
                  type="text"
                  class="form-control form-control-sm"
                  placeholder="請輸入過濾條件..."
                />
              </div>
              <div class="col-md-6 d-flex gap-2">
                <button
                  @click="increasePriority"
                  class="btn btn-success btn-sm"
                  :disabled="!productFilter || filteredLots.length === 0"
                >
                  Priority 增加 (+10)
                </button>
                <button
                  @click="decreasePriority"
                  class="btn btn-warning btn-sm"
                  :disabled="!productFilter || filteredLots.length === 0"
                >
                  Priority 下降 (-10)
                </button>
              </div>
            </div>
          </div>
          <div class="card-body">
            <div class="table-responsive">
              <table class="table table-hover table-bordered">
                <thead class="table-dark">
                  <tr>
                    <th>LotId</th>
                    <th>Product</th>
                    <th>Priority</th>
                    <th>DueDate</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(lot, index) in filteredLots" :key="lot.LotId + index">
                    <td>{{ lot.LotId }}</td>
                    <td>{{ lot.Product }}</td>
                    <td>
                      <input
                        v-model.number="lot.Priority"
                        type="number"
                        class="form-control form-control-sm"
                        min="1"
                        max="10"
                      />
                    </td>
                    <td>
                      <input
                        v-model="lot.DueDate"
                        type="datetime-local"
                        class="form-control form-control-sm"
                      />
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Schedule Selection Modal -->
    <div v-if="showScheduleSelector" class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5)">
      <div class="modal-dialog modal-xl">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">選取 ScheduleId</h5>
            <button type="button" class="btn-close" @click="showScheduleSelector = false"></button>
          </div>
          <div class="modal-body">
            <div class="table-responsive">
              <table class="table table-hover table-bordered">
                <thead class="table-dark">
                  <tr>
                    <th>ScheduleId</th>
                    <th>CreateDate</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="schedule in availableSchedules"
                    :key="schedule.ScheduleId"
                    @click="tempScheduleId = schedule.ScheduleId"
                    :class="{'table-primary': tempScheduleId === schedule.ScheduleId}"
                    style="cursor: pointer;"
                  >
                    <td>{{ schedule.ScheduleId }}</td>
                    <td>{{ formatDate(schedule.CreateDate) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <div class="modal-footer">
            <button
              type="button"
              class="btn btn-primary"
              :disabled="!tempScheduleId"
              @click="loadSelectedSchedule"
            >
              載入資料
            </button>
            <button type="button" class="btn btn-secondary" @click="showScheduleSelector = false">關閉</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Debug Logs Section -->
    <div v-if="debugLogs.length > 0" class="row mt-4">
      <div class="col-12">
        <div class="card">
          <div class="card-header">
            <h5 class="card-title mb-0">Debug Logs</h5>
          </div>
          <div class="card-body">
            <button @click="downloadLogs" class="btn btn-secondary btn-sm mb-2">下載 Log 文件</button>
            <pre class="bg-light p-2" style="max-height: 300px; overflow-y: auto;">{{ debugLogs.join('\n') }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useCreateScheduleJobStore } from '../stores/createScheduleJob'
import api from '../utils/apiConfig'

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

const store = useCreateScheduleJobStore()

// Reactive references from store
const models = computed(() => store.models)
const lots = computed(() => store.lots)
const productFilter = computed({
  get: () => store.productFilter,
  set: (value: string) => store.setProductFilter(value)
})
const scheduleId = computed({
  get: () => store.scheduleId,
  set: (value: string) => store.setScheduleId(value)
})
const showScheduleSelector = computed({
  get: () => store.showScheduleSelector,
  set: (value: boolean) => store.setShowScheduleSelector(value)
})
const availableSchedules = computed(() => store.availableSchedules)
const tempScheduleId = computed({
  get: () => store.tempScheduleId,
  set: (value: string | null) => store.setTempScheduleId(value)
})
const debugLogs = computed(() => store.debugLogs)

const filteredLots = computed(() => store.filteredLots)

// Wrapper functions for template events
const openScheduleSelector = () => store.setShowScheduleSelector(true)
const closeScheduleSelector = () => store.setShowScheduleSelector(false)
const selectScheduleId = (scheduleId: string) => store.setTempScheduleId(scheduleId)

onMounted(async () => {
  try {
    // Fetch available schedules
    const response = await api.get('/api/get_plan_model_user_workshop_list')
    const schedulesData = response.data
    store.setAvailableSchedules(schedulesData.map((s: any) => ({
      ScheduleId: s.ScheduleId,
      CreateDate: s.CreateDate
    })))
  } catch (e) {
    console.error('Error fetching data:', e)
  }
})

const loadSelectedSchedule = async () => {
  store.clearDebugLogs() // 清空之前的 log
  const log = (message: string) => {
    store.addDebugLog(message)
  }

  if (!store.tempScheduleId) {
    log('loadSelectedSchedule: tempScheduleId is null or undefined')
    return
  }

  const id = store.tempScheduleId
  log(`loadSelectedSchedule: Starting to load schedule with id: ${id}`)

  try {
    // Fetch specific schedule by ID
    const url = `/api/plan_model_user_workshop/schedule/${id}`
    log(`loadSelectedSchedule: Fetching schedule from: ${url}`)

    const response = await api.get(url)
    const data = response.data
    log(`loadSelectedSchedule: Received data: ${JSON.stringify(data)}`)

    if (!data.ScheduleId) {
      throw new Error('Invalid data: missing ScheduleId')
    }

    store.setScheduleId(data.ScheduleId)
    log(`loadSelectedSchedule: Set scheduleId to: ${data.ScheduleId}`)

    // Update models
    if (data.models) {
      let modelsArray: any[] = []

      if (typeof data.models === 'string') {
        // Parse JSON string if it's a string
        try {
          modelsArray = JSON.parse(data.models)
          log(`loadSelectedSchedule: Parsed models JSON string, count: ${modelsArray.length}`)
        } catch (e) {
          log(`loadSelectedSchedule: Failed to parse models JSON string: ${e}`)
          throw new Error('Invalid data: models JSON string cannot be parsed')
        }
      } else if (Array.isArray(data.models)) {
        modelsArray = data.models
        log(`loadSelectedSchedule: Models is already an array, count: ${modelsArray.length}`)
      } else {
        log(`loadSelectedSchedule: data.models is neither string nor array: ${typeof data.models}`)
        throw new Error('Invalid data: models must be a JSON string or array')
      }

      if (Array.isArray(modelsArray)) {
        log(`loadSelectedSchedule: Updating models, count: ${modelsArray.length}`)
        const mappedModels = modelsArray.map((m: any, index: number) => {
          const mapped = {
            SeqNo: index + 1, // Generate SeqNo based on index
            Select: m.Selected === 'selected' ? 1 : 0,
            optimization_type: m.optimization_type,
            Name: m.Name,
            Description: '', // Default empty
            Remark: '', // Default empty
            selected: m.Selected || 'unselected'
          }
          log(`loadSelectedSchedule: Mapped model: ${mapped.Name} (${mapped.optimization_type}) to selected: ${mapped.selected}`)
          return mapped
        })
        store.setModels(mappedModels)
      } else {
        log(`loadSelectedSchedule: Parsed models is not an array: ${typeof modelsArray}`)
        throw new Error('Invalid data: parsed models is not an array')
      }
    } else {
      log('loadSelectedSchedule: No models in data')
      store.setModels([])
    }

    // Update lots
    if (data.lots) {
      let lotsArray: any[] = []

      if (typeof data.lots === 'string') {
        // Parse JSON string if it's a string
        try {
          lotsArray = JSON.parse(data.lots)
          log(`loadSelectedSchedule: Parsed lots JSON string, count: ${lotsArray.length}`)
        } catch (e) {
          log(`loadSelectedSchedule: Failed to parse lots JSON string: ${e}`)
          throw new Error('Invalid data: lots JSON string cannot be parsed')
        }
      } else if (Array.isArray(data.lots)) {
        lotsArray = data.lots
        log(`loadSelectedSchedule: Lots is already an array, count: ${lotsArray.length}`)
      } else {
        log(`loadSelectedSchedule: data.lots is neither string nor array: ${typeof data.lots}`)
        throw new Error('Invalid data: lots must be a JSON string or array')
      }

      if (Array.isArray(lotsArray)) {
        log(`loadSelectedSchedule: Updating lots, count: ${lotsArray.length}`)
        const mappedLots = lotsArray.map((l: any) => {
          const formattedDate = formatDateForInput(l.DueDate)
          log(`loadSelectedSchedule: Mapped lot: ${l.LotId} (${l.Product}) Priority: ${l.Priority}, DueDate from: ${l.DueDate} to: ${formattedDate}`)
          return {
            ...l,
            DueDate: formattedDate
          }
        })
        store.setLots(mappedLots)
      } else {
        log(`loadSelectedSchedule: Parsed lots is not an array: ${typeof lotsArray}`)
        throw new Error('Invalid data: parsed lots is not an array')
      }
    } else {
      log('loadSelectedSchedule: No lots in data')
      store.setLots([])
    }

    store.setShowScheduleSelector(false)
    store.setTempScheduleId(null) // 清除臨時選定的 ID
    log('loadSelectedSchedule: Successfully loaded schedule')
  } catch (e) {
    const errorMessage = e instanceof Error ? e.message : String(e)
    store.addDebugLog(`loadSelectedSchedule: Error loading schedule: ${errorMessage}`)
    store.addDebugLog(`loadSelectedSchedule: Error details: tempScheduleId=${store.tempScheduleId}, stack=${e instanceof Error ? e.stack : undefined}`)
    console.error('loadSelectedSchedule: Error loading schedule:', e)
    alert('載入 Schedule 失敗: ' + errorMessage)
  }
}

const loadModelsFromDatabase = async () => {
  try {
    console.log('Loading models from database...')
    const response = await api.get('/api/get_plan_models?limit=10')
    const modelsData: PlanModel[] = response.data
    const mappedModels = modelsData.map(model => ({
      ...model,
      selected: model.Select === 1 ? 'selected' : 'unselected'
    }))
    store.setModels(mappedModels)
    console.log(`Successfully loaded ${mappedModels.length} models from database`)
  } catch (e) {
    console.error('Error loading models from database:', e)
    alert('從資料庫讀取 Models 失敗')
  }
}

const loadLotsFromDatabase = async () => {
  try {
    console.log('Loading lots from database...')
    const response = await api.get('/api/get_json/lot_Plan/Lot_Plan.json')
    const lotsData: Lot[] = response.data
    // Format DueDate for datetime-local input
    const mappedLots = lotsData.map(lot => ({
      ...lot,
      DueDate: formatDateForInput(lot.DueDate)
    }))
    store.setLots(mappedLots)
    console.log(`Successfully loaded ${mappedLots.length} lots from database`)
  } catch (e) {
    console.error('Error loading lots from database:', e)
    alert('從資料庫讀取 Lots 失敗')
  }
}

const updateSelection = (model: PlanModel) => {
  console.log('Updated selection for model:', model.SeqNo, model.selected)
}

const generateScheduleId = () => {
  const now = new Date()
  const generatedId = now.getFullYear().toString() +
    (now.getMonth() + 1).toString().padStart(2, '0') +
    now.getDate().toString().padStart(2, '0') +
    now.getHours().toString().padStart(2, '0') +
    now.getMinutes().toString().padStart(2, '0')
  store.setScheduleId(generatedId)
}

const saveToWorkshop = async () => {
  try {
    const modelListData = {
      ScheduleId: store.scheduleId,
      models: store.models.map(model => ({
        Name: model.Name,
        optimization_type: model.optimization_type,
        Selected: model.selected
      })),
      lots: store.lots
    }

    // Save ModelList.json
    const modelResponse = await api.post('/api/save_json', {
      json: modelListData,
      filename: 'ModelList.json'
    })
    if (!modelResponse.ok) {
      throw new Error(`Failed to save ModelList.json: ${modelResponse.status}`)
    }

    alert('已成功存入 workshop')
  } catch (error) {
    console.error('Error saving to workshop:', error)
    alert(`存入 workshop 失敗: ${error instanceof Error ? error.message : String(error)}`)
  }
}

const increasePriority = () => {
  store.increasePriority()
}

const decreasePriority = () => {
  store.decreasePriority()
}

const formatDate = (dateString: string) => {
  try {
    const date = new Date(dateString)
    return date.toLocaleString('zh-TW')
  } catch {
    return dateString
  }
}

const formatDateForInput = (dateString: string) => {
  try {
    const date = new Date(dateString)
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    return `${year}-${month}-${day}T${hours}:${minutes}`
  } catch {
    return dateString
  }
}

const downloadLogs = () => {
  const logContent = store.debugLogs.join('\n')
  const blob = new Blob([logContent], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `debug_log_${new Date().toISOString().replace(/[:.]/g, '-')}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.create-schedule-job-view {
  padding: 20px;
  background-color: #f8f9fa;
  min-height: 100vh;
}

.card {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border: none;
  margin-bottom: 20px;
}

.table {
  margin-bottom: 0;
}

.table-hover tbody tr:hover {
  background-color: rgba(0, 0, 0, 0.075);
}

.form-select {
  min-width: 100px;
}

.modal {
  display: block;
}
</style>