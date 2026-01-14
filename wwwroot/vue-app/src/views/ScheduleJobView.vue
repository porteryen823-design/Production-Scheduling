<template>
  <div class="schedule-job-view container-fluid mt-4">
    <div class="row">
      <div class="col-12">
        <h1 class="text-center mb-4">Schedule Jobs</h1>
      </div>
    </div>

    <div class="row">
      <!-- Left side: Tables -->
      <div class="col-md-6">
        <div class="row mb-4">
          <div class="col-12">
            <div class="card">
              <div class="card-header">
                <h5 class="card-title mb-0">Schedule Jobs List</h5>
              </div>
              <div class="card-body">
                <div class="table-responsive">
                  <table class="table table-hover table-bordered">
                    <thead class="table-dark">
                      <tr>
                        <th>ScheduleId</th>
                        <th>CreateDate</th>
                        <th>CreateUser</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="job in paginatedJobs"
                        :key="job.ScheduleId"
                        :class="{ 'table-active': selectedJob?.ScheduleId === job.ScheduleId }"
                        @click="selectJob(job)"
                        class="clickable-row"
                      >
                        <td>{{ job.ScheduleId }}</td>
                        <td>{{ formatDate(job.CreateDate) }}</td>
                        <td>{{ job.CreateUser }}</td>
                        <td>
                          <button
                            class="btn btn-primary btn-sm"
                            @click.stop="selectJob(job)"
                          >
                            選擇
                          </button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <nav aria-label="Schedule Jobs pagination">
                  <ul class="pagination justify-content-center">
                    <li class="page-item" :class="{ disabled: currentPage === 1 }">
                      <button class="page-link" @click="prevPage" :disabled="currentPage === 1">Previous</button>
                    </li>
                    <li class="page-item disabled">
                      <span class="page-link">{{ currentPage }} / {{ totalPages }}</span>
                    </li>
                    <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                      <button class="page-link" @click="nextPage" :disabled="currentPage === totalPages">Next</button>
                    </li>
                  </ul>
                </nav>
              </div>
            </div>
          </div>
        </div>

        <div class="row">
          <div class="col-12">
            <div class="card">
              <div class="card-header">
                <h5 class="card-title mb-0">
                  Lot Plans
                  <small v-if="selectedJob" class="text-muted">({{ selectedJob.ScheduleId }})</small>
                </h5>
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
                      <tr
                        v-for="(lot, index) in paginatedLots"
                        :key="lot.LotId + lot.Product + index"
                        :class="{ 'table-active': selectedLotIndex === getGlobalIndex(index) }"
                        @click="selectLot(getGlobalIndex(index))"
                        class="clickable-row"
                      >
                        <td>{{ lot.LotId }}</td>
                        <td>{{ lot.Product }}</td>
                        <td>{{ lot.Priority }}</td>
                        <td>{{ formatDate(lot.DueDate) }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <nav aria-label="Lot Plans pagination">
                  <ul class="pagination justify-content-center">
                    <li class="page-item" :class="{ disabled: lotCurrentPage === 1 }">
                      <button class="page-link" @click="prevLotPage" :disabled="lotCurrentPage === 1">Previous</button>
                    </li>
                    <li class="page-item disabled">
                      <span class="page-link">{{ lotCurrentPage }} / {{ lotTotalPages }}</span>
                    </li>
                    <li class="page-item" :class="{ disabled: lotCurrentPage === lotTotalPages }">
                      <button class="page-link" @click="nextLotPage" :disabled="lotCurrentPage === lotTotalPages">Next</button>
                    </li>
                  </ul>
                </nav>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right side: PlanSummary -->
      <div class="col-md-6">
        <div class="card h-100">
          <div class="card-header">
            <h5 class="card-title mb-0">Plan Summary</h5>
          </div>
          <div class="card-body">
            <textarea
              v-model="displayedPlanSummary"
              class="form-control"
              rows="20"
              readonly
              style="font-family: monospace; resize: none;"
            ></textarea>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

interface ScheduleJob {
  ScheduleId: string
  CreateDate: string
  CreateUser: string
  LotPlan: string
  PlanSummary: string
}

interface Lot {
  LotId: string
  Product: string
  Priority: number
  DueDate: string
  Operations?: any[]
}

const jobs = ref<ScheduleJob[]>([])
const lots = ref<Lot[]>([])
const currentPage = ref(1)
const pageSize = 10
const lotCurrentPage = ref(1)
const lotPageSize = 10
const selectedLotIndex = ref<number | null>(null)
const selectedJob = ref<ScheduleJob | null>(null)
const displayedPlanSummary = ref<string>('')

onMounted(async () => {
  try {
    const response = await fetch('http://localhost:5000/get_schedule_jobs')
    const data: ScheduleJob[] = await response.json()
    jobs.value = data

    // 合併所有 LotPlan
    const allLots: Lot[] = []
    for (const job of data) {
      try {
        const lotPlan: Lot[] = JSON.parse(job.LotPlan)
        allLots.push(...lotPlan)
      } catch (e) {
        console.error('Error parsing LotPlan:', e)
      }
    }
    lots.value = allLots
  } catch (e) {
    console.error('Error fetching data:', e)
  }
})

const totalPages = computed(() => Math.ceil(jobs.value.length / pageSize))
const paginatedJobs = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return jobs.value.slice(start, start + pageSize)
})

const filteredLots = computed(() => {
  if (!selectedJob.value) return lots.value
  try {
    return JSON.parse(selectedJob.value.LotPlan)
  } catch {
    return []
  }
})

const lotTotalPages = computed(() => Math.ceil(filteredLots.value.length / lotPageSize))
const paginatedLots = computed(() => {
  const start = (lotCurrentPage.value - 1) * lotPageSize
  return filteredLots.value.slice(start, start + lotPageSize)
})

const prevPage = () => {
  if (currentPage.value > 1) currentPage.value--
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) currentPage.value++
}

const prevLotPage = () => {
  if (lotCurrentPage.value > 1) lotCurrentPage.value--
}

const nextLotPage = () => {
  if (lotCurrentPage.value < lotTotalPages.value) lotCurrentPage.value++
}

const selectJob = (job: ScheduleJob) => {
  selectedJob.value = job
  selectedLotIndex.value = null
  lotCurrentPage.value = 1
  displayedPlanSummary.value = job.PlanSummary
}

const selectLot = (globalIndex: number) => {
  selectedLotIndex.value = globalIndex
}

const getGlobalIndex = (localIndex: number) => {
  return (lotCurrentPage.value - 1) * lotPageSize + localIndex
}

const formatDate = (dateString: string) => {
  try {
    const date = new Date(dateString)
    return date.toLocaleString('zh-TW')
  } catch {
    return dateString
  }
}
</script>

<style scoped>
.schedule-job-view {
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

.clickable-row {
  cursor: pointer;
}

.table-active {
  background-color: rgba(0, 123, 255, 0.1) !important;
}

.pagination {
  margin-top: 15px;
}

.btn-primary {
  background-color: #007bff;
  border-color: #007bff;
}

.btn-primary:hover {
  background-color: #0056b3;
  border-color: #0056b3;
}

.card-title {
  color: #495057;
}

.form-control {
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
}

.form-control:focus {
  background-color: #fff;
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}
</style>