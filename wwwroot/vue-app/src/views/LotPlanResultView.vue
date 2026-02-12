<template>
  <div class="d-flex flex-wrap align-items-center gap-2 mb-3">
    <h2><i class="fas fa-table"></i> Lot Plan Result</h2>
   
    <!-- 重新載入按鈕 -->
    <button class="btn btn-primary btn-sm" @click="loadData">
      <i class="fas fa-sync"></i> 重新載入
    </button>
  </div>

  <!-- 統計資訊 -->
  <div class="row mb-4" v-if="statistics">
    <div class="col-12">
      <div class="card">
        <div class="card-header">
          <h5 class="card-title mb-0"><i class="fas fa-chart-bar"></i> 排程統計資訊</h5>
        </div>
        <div class="card-body p-0">
          <div class="row g-0">
            <div class="col-md-3 stat-col">
              <div class="mb-2">
                <span class="stat-label">優化類型</span>
                <span class="stat-value">{{ statistics.optimization_type }}</span>
              </div>
              <div class="mb-2">
                <span class="stat-label">計算批數</span>
                <span class="stat-value">{{ statistics.batch_count }}</span>
              </div>
              <div>
                <span class="stat-label">優化目標</span>
                <span class="stat-value">{{ statistics.optimization_goal }}</span>
              </div>
            </div>
            <div class="col-md-3 stat-col">
              <div class="mb-2">
                <span class="stat-label">計算起訖時間</span>
                <span class="stat-value small">{{ formatDateTime(statistics.calculation_start) }} ~ {{ formatDateTime(statistics.calculation_end) }}</span>
              </div>
              <div>
                <span class="stat-label">計算總時間</span>
                <span class="stat-value">{{ statistics.calculation_duration }}</span>
              </div>
            </div>
            <div class="col-md-3 stat-col">
              <div class="mb-2">
                <span class="stat-label">最早投入時間</span>
                <span class="stat-value small">{{ formatDateTime(statistics.earliest_input_time) }}</span>
              </div>
              <div class="mb-2">
                <span class="stat-label">最後產出時間</span>
                <span class="stat-value small">{{ formatDateTime(statistics.latest_output_time) }}</span>
              </div>
              <div>
                <span class="stat-label">總排程時間</span>
                <span class="stat-value">{{ statistics.total_schedule_duration }}</span>
              </div>
            </div>
            <div class="col-md-3 stat-col">
              <span class="stat-label mb-2">延遲統計</span>
              <div class="d-flex flex-wrap gap-1">
                <span class="badge bg-success">提早: {{ statistics.early_count }}</span>
                <span class="badge bg-info">準時: {{ statistics.on_time_count }}</span>
                <span class="badge bg-warning">輕微延遲: {{ statistics.minor_delay_count }}</span>
                <span class="badge bg-danger">嚴重延遲: {{ statistics.major_delay_count }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 過濾器 -->
  <div class="d-flex flex-wrap align-items-center gap-3 mb-3">
    <div class="d-flex align-items-center gap-2">
      <label for="lotFilter" class="fw-semibold mb-0"><i class="fas fa-hashtag"></i> 批號過濾：</label>
      <select id="lotFilter" class="form-select form-select-sm" style="width: 150px;" v-model="selectedLot">
        <option value="ALL">全部</option>
        <option v-for="lot in uniqueLots" :key="lot" :value="lot">{{ lot }}</option>
      </select>
    </div>
    <div class="d-flex align-items-center gap-2">
      <label for="productFilter" class="fw-semibold mb-0"><i class="fas fa-box"></i> 產品過濾：</label>
      <select id="productFilter" class="form-select form-select-sm" style="width: 150px;" v-model="selectedProduct">
        <option value="ALL">全部</option>
        <option v-for="product in uniqueProducts" :key="product" :value="product">{{ product }}</option>
      </select>
    </div>
    <div class="d-flex align-items-center gap-2">
      <label for="statusFilter" class="fw-semibold mb-0"><i class="fas fa-clock"></i> 狀態過濾：</label>
      <select id="statusFilter" class="form-select form-select-sm" style="width: 150px;" v-model="selectedStatus">
        <option value="ALL">全部</option>
        <option value="提早">提早</option>
        <option value="準時">準時</option>
        <option value="輕微延遲">輕微延遲</option>
        <option value="嚴重延遲">嚴重延遲</option>
      </select>
    </div>
  </div>

  <div class="table-container">
    <div class="table-responsive">
      <table class="table table-striped table-hover">
        <thead>
          <tr>
            <th>Lot</th>
            <th>Product</th>
            <th>Priority</th>
            <th>Due Date</th>
            <th>Plan Date</th>
            <th>Delay Time</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in filteredResults" :key="row.Lot">
            <td>{{ row.Lot }}</td>
            <td>{{ row.Product }}</td>
            <td>{{ row.Priority }}</td>
            <td>{{ formatDateTime(row['Due Date']) }}</td>
            <td>{{ formatDateTime(row['Plan Date']) }}</td>
            <td>
              <span :class="getDelayBadgeInfo(row['delay time']).textColor" class="delay-text">
                {{ row['delay time'] }}
              </span>
            </td>
            <td>
              <span class="badge" :class="getDelayBadgeInfo(row['delay time']).badgeClass">
                {{ getDelayBadgeInfo(row['delay time']).statusText }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import api from '../utils/apiConfig'
import { useTheme } from '../composables/useTheme'

interface LotResult {
  Lot: string
  Product: string
  Priority: number
  'Due Date': string
  'Plan Date': string
  'delay time': string
}

interface Statistics {
  optimization_type: number | string
  batch_count: number
  optimization_goal: string
  calculation_start: string
  calculation_end: string
  calculation_duration: string
  earliest_input_time: string
  latest_output_time: string
  total_schedule_duration: string
  early_count: number
  on_time_count: number
  minor_delay_count: number
  major_delay_count: number
}

const { setTheme } = useTheme()
const allResults = ref<LotResult[]>([])
const statistics = ref<Statistics | null>(null)
const selectedLot = ref('ALL')
const selectedProduct = ref('ALL')
const selectedStatus = ref('ALL')

const uniqueLots = computed(() => [...new Set(allResults.value.map(r => r.Lot))].sort())
const uniqueProducts = computed(() => [...new Set(allResults.value.map(r => r.Product))].sort())

const filteredResults = computed(() => {
  return allResults.value.filter(r => {
    const lotMatch = selectedLot.value === 'ALL' || r.Lot === selectedLot.value
    const productMatch = selectedProduct.value === 'ALL' || r.Product === selectedProduct.value
    const statusMatch = selectedStatus.value === 'ALL' || getDelayBadgeInfo(r['delay time']).statusText === selectedStatus.value
    return lotMatch && productMatch && statusMatch
  })
})

const loadData = async () => {
  try {
    const response = await api.get('/api/schedule')
    const data = response.data
    if (data.LotPlanResult) {
      allResults.value = data.LotPlanResult.lot_results || []
      statistics.value = data.LotPlanResult.statistics || null
    } else {
      allResults.value = []
      statistics.value = null
    }
  } catch (error) {
    console.error("資料載入失敗", error)
  }
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-TW')
}

const parseDelayTime = (delayStr: string) => {
  if (!delayStr || delayStr === "0:00") return 0
  const isNegative = delayStr.startsWith('-')
  const cleanStr = isNegative ? delayStr.substring(1) : delayStr
  const parts = cleanStr.split(':').map(Number)
  let days = 0, hours = 0
  if (parts.length === 2) [days, hours] = parts
  else if (parts.length === 3) {
    const [h, m, s] = parts
    days = Math.floor(h / 24)
    hours = h % 24 + m / 60 + s / 3600
  }
  const totalDays = days + hours / 24
  return isNegative ? -totalDays : totalDays
}

const getDelayBadgeInfo = (delayStr: string) => {
  const totalDays = parseDelayTime(delayStr)
  if (totalDays < 0) return { badgeClass: "bg-success", statusText: "提早", textColor: "text-success" }
  if (totalDays === 0) return { badgeClass: "bg-info", statusText: "準時", textColor: "text-info" }
  if (totalDays <= 2) return { badgeClass: "bg-warning", statusText: "輕微延遲", textColor: "text-warning" }
  return { badgeClass: "bg-danger", statusText: "嚴重延遲", textColor: "text-danger" }
}

onMounted(loadData)
</script>

<style scoped>
.stat-col {
  border-right: 1px solid var(--border-color);
  padding: 10px 15px;
}
.stat-col:last-child {
  border-right: none;
}
.stat-label {
  color: #6c757d;
  font-weight: 600;
  font-size: 0.85rem;
  display: block;
  margin-bottom: 2px;
}
.stat-value {
  color: #333;
  font-weight: 500;
}
.table-container {
  background-color: var(--bg-color);
  border-radius: 8px;
  box-shadow: 0 2px 4px var(--shadow);
  padding: 20px;
  margin-top: 20px;
}
</style>
