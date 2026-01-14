<template>
  <div id="app">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
      <div class="container-fluid">
        <router-link class="navbar-brand" to="/">
          <i class="fas fa-cogs"></i> 產線排程系統
        </router-link>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav me-auto">
            <li class="nav-item">
              <router-link class="nav-link" to="/schedule-jobs">
                <i class="fas fa-calendar-alt"></i> Schedule Jobs
              </router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/lot-gantt">
                <i class="fas fa-diagram-project"></i> Lot 甘特圖
              </router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/machine-gantt">
                <i class="fas fa-cogs"></i> 機台甘特圖
              </router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/machine-usage">
                <i class="fas fa-chart-gantt"></i> 機台使用率
              </router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/lot-results">
                <i class="fas fa-table"></i> Lot 結果
              </router-link>
            </li>
          </ul>
          <!-- 主題切換 -->
          <div class="d-flex">
            <div class="btn-group" role="group">
              <button class="btn btn-secondary btn-sm" @click="setTheme('light')" :class="{ active: currentTheme === 'light' }">
                <i class="fas fa-sun"></i> 亮色
              </button>
              <button class="btn btn-secondary btn-sm" @click="setTheme('dark')" :class="{ active: currentTheme === 'dark' }">
                <i class="fas fa-moon"></i> 暗色
              </button>
            </div>
          </div>
        </div>

      </div>
    </nav>

  

    <main class="container-fluid mt-3">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useTheme } from './composables/useTheme'

const { currentTheme, setTheme } = useTheme()
</script>

<style>
/* Global theme variables */
:root {
  --bg-color: #ffffff;
  --text-color: #000000;
  --header-bg: #f8f9fa;
  --border-color: #dee2e6;
  --shadow: rgba(0, 0, 0, 0.1);
}


[data-theme="dark"] {
  --bg-color: #121212;
  --text-color: #ffffff;
  --header-bg: #1e1e1e;
  --border-color: #333333;
  --shadow: rgba(0, 0, 0, 0.3);
}

html, body {
  height: 100%;
  padding: 0;
  margin: 0;
  background-color: var(--bg-color);
  color: var(--text-color);
  transition: background-color 0.3s, color 0.3s;
}

.gantt-container {
  width: 100%;
  height: calc(100vh - 200px);
  background-color: var(--bg-color);
  border-radius: 8px;
  box-shadow: 0 2px 4px var(--shadow);
  transition: background-color 0.3s, box-shadow 0.3s;
}
</style>
