<template>
  <div class="plan-models-view container-fluid py-4">
    <div class="row mb-4">
      <div class="col-12">
        <h2 class="display-6 text-primary border-bottom pb-2">
          <i class="fas fa-cogs me-2"></i>Plan Models 設定
        </h2>
      </div>
    </div>

    <div class="row">
      <!-- 左側：表格列表 -->
      <div class="col-lg-6">
        <div class="card shadow-sm mb-4">
          <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
            <h5 class="mb-0"><i class="fas fa-list me-2"></i>模型列表</h5>
            <span class="badge bg-light text-primary">{{ planModels.length }} 筆資料</span>
          </div>
          <div class="card-body p-0">
            <div class="table-responsive">
              <table class="table table-hover mb-0">
                <thead class="table-light">
                  <tr>
                    <th class="ps-3">SeqNo</th>
                    <th>Select</th>
                    <th>優化類型</th>
                    <th>名稱</th>
                    <th>描述</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="model in planModels"
                    :key="model.SeqNo"
                    :class="{ 'table-primary': selectedModel?.SeqNo === model.SeqNo }"
                    @click="selectModel(model)"
                    class="clickable-row"
                  >
                    <td class="ps-3 fw-bold">{{ model.SeqNo }}</td>
                    <td>
                      <span :class="model.Select === 1 ? 'badge bg-success' : 'badge bg-secondary'">
                        {{ model.Select === 1 ? '已選取' : '未選取' }}
                      </span>
                    </td>
                    <td><span class="badge bg-info text-dark">{{ model.optimization_type }}</span></td>
                    <td class="fw-semibold">{{ model.Name }}</td>
                    <td class="text-muted small">{{ model.Description }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Remark 區塊 -->
        <div class="card shadow-sm">
          <div class="card-header bg-dark text-white">
            <h5 class="mb-0"><i class="fas fa-comment-alt me-2"></i>備註 (Remark)</h5>
          </div>
          <div class="card-body">
            <textarea
              :value="selectedModel?.Remark"
              class="form-control bg-light"
              rows="10"
              readonly
              placeholder="點選上方列表查看備註..."
              style="font-family: 'Consolas', 'Monaco', monospace; resize: none; border: none;"
            ></textarea>
          </div>
          <div class="card-footer text-muted small" v-if="selectedModel">
            最後更新：{{ selectedModel.Name }} (SeqNo: {{ selectedModel.SeqNo }})
          </div>
        </div>
      </div>

      <!-- 右側：圖形顯示 -->
      <div class="col-lg-6">
        <div class="card shadow-sm sticky-top" style="top: 2px;">
          <div class="card-header bg-secondary text-white text-center">
            <h5 class="mb-0"><i class="fas fa-project-diagram me-2"></i>優化類型示意圖</h5>
          </div>
          <div class="card-body text-center bg-white p-4">
            <div class="img-container border rounded p-2 bg-light mb-3">
              <img
                src="/images/optimization_type.png"
                alt="Optimization Type Diagram"
                class="img-fluid"
                style="max-height: 600px; object-fit: contain;"
              />
            </div>
            <p class="text-muted small mb-0">
              <i class="fas fa-info-circle me-1"></i>
              此圖表顯示不同優化類型的邏輯架構
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../utils/apiConfig'

interface PlanModel {
  SeqNo: number
  Select: number
  optimization_type: number
  Name: string
  Description: string
  Remark: string
}

const planModels = ref<PlanModel[]>([])
const selectedModel = ref<PlanModel | null>(null)

onMounted(async () => {
  try {
    // 這裡我們暫時對應到 FastAPI 的 /api/v1/simulation-data 如果找不到 get_plan_models
    // 或者我們先修復 Port 錯誤
    const response = await api.get('/api/get_plan_models?limit=10')
    const data: PlanModel[] = response.data
    planModels.value = data
    if (data.length > 0) {
      selectedModel.value = data[0] // 初始選定第一筆
    }
  } catch (e) {
    console.error('Error fetching plan models:', e)
  }
})

const selectModel = (model: PlanModel) => {
  selectedModel.value = model
}
</script>

<style scoped>
.plan-models-view {
  padding: 20px;
}
</style>