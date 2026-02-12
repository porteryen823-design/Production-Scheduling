<template>
  <div class="container-fluid">
    <div class="row justify-content-center">
      <div class="col-12 text-center mb-5" style="margin-left: 6rem;">
        <h1 class="display-4">歡迎使用 產線排程系統</h1>
        <hr class="my-4">
      </div>
    </div>

    <div class="row">
      <!-- Schedule Jobs -->
      <div class="col-md-4 mb-4">
        <div class="card h-100">
          <router-link to="/schedule-jobs" class="card-body text-center" style="text-decoration: none; color: inherit;">
            <i class="fas fa-calendar-alt fa-3x text-primary mb-3"></i>
            <h5 class="card-title">Schedule Jobs</h5>
            <p class="card-text">查看排程任務和計劃摘要</p>
          </router-link>
        </div>
      </div>

      <!-- Lot Gantt -->
      <div class="col-md-4 mb-4">
        <div class="card h-100">
          <router-link to="/lot-gantt" class="card-body text-center" style="text-decoration: none; color: inherit;">
            <i class="fas fa-chart-gantt fa-3x text-success mb-3"></i>
            <h5 class="card-title">Lot 甘特圖</h5>
            <p class="card-text">查看批次排程的甘特圖</p>
          </router-link>
        </div>
      </div>

      <!-- Machine Gantt -->
      <div class="col-md-4 mb-4">
        <div class="card h-100">
          <router-link to="/machine-gantt" class="card-body text-center" style="text-decoration: none; color: inherit;">
            <i class="fas fa-cogs fa-3x text-info mb-3"></i>
            <h5 class="card-title">Machine 甘特圖</h5>
            <p class="card-text">查看機台排程的甘特圖</p>
          </router-link>
        </div>
      </div>

      <!-- Machine Usage -->
      <div class="col-md-4 mb-4">
        <div class="card h-100">
          <router-link to="/machine-usage" class="card-body text-center" style="text-decoration: none; color: inherit;">
            <i class="fas fa-chart-bar fa-3x text-warning mb-3"></i>
            <h5 class="card-title">Machine 使用率</h5>
            <p class="card-text">查看機台使用率統計</p>
          </router-link>
        </div>
      </div>

      <!-- Lot Results -->
      <div class="col-md-4 mb-4">
        <div class="card h-100">
          <router-link to="/lot-results" class="card-body text-center" style="text-decoration: none; color: inherit;">
            <i class="fas fa-list fa-3x text-danger mb-3"></i>
            <h5 class="card-title">Lot 結果</h5>
            <p class="card-text">查看批次排程結果</p>
          </router-link>
        </div>
      </div>

      <!-- Plan Models -->
      <div class="col-md-4 mb-4">
        <div class="card h-100">
          <router-link to="/plan-models" class="card-body text-center" style="text-decoration: none; color: inherit;">
            <i class="fas fa-cogs fa-3x text-secondary mb-3"></i>
            <h5 class="card-title">Plan Models</h5>
            <p class="card-text">查看計劃模型設定</p>
          </router-link>
        </div>
      </div>
    </div>

    <div class="row">
      <!-- Create Schedule Job -->
      <div class="col-md-4 mb-4">
        <div class="card h-100">
          <router-link to="/create-schedule-job" class="card-body text-center" style="text-decoration: none; color: inherit;">
            <i class="fas fa-plus-circle fa-3x text-warning mb-3"></i>
            <h5 class="card-title">Create Schedule Job</h5>
            <p class="card-text">創建新的排程任務</p>
          </router-link>
        </div>
      </div>

      <!-- Automated Test -->
      <div class="col-md-4 mb-4">
        <div class="card h-100">
          <router-link to="/automated-test" class="card-body text-center" style="text-decoration: none; color: inherit;">
            <i class="fas fa-vial fa-3x text-primary mb-3"></i>
            <h5 class="card-title">自動化測試</h5>
            <p class="card-text">執行排程壓力測試與模擬連動</p>
          </router-link>
        </div>
      </div>
    </div>

    <div class="row justify-content-center mt-4">
      <div class="col-12 text-center">
        <p class="text-muted">本系統使用 Vue 3, TypeScript, Bootstrap 5 和 dhtmlxGantt 進行視覺化。</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Home View
</script>

<style scoped>
.card-body:hover {
  background-color: #f8f9fa;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.card-body {
  transition: all 0.3s ease;
}
</style>