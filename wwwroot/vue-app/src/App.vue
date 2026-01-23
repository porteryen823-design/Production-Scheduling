<template>
  <div id="app">
    <!-- 側邊欄切換按鈕 -->
    <button class="sidebar-toggle" @click="toggleSidebar">
      <i class="fas fa-bars"></i>
    </button>

    <!-- 側邊欄模式切換按鈕 -->
    <button class="sidebar-mode-toggle" @click="toggleSidebarMode" :title="sidebarCollapsed ? '展開側邊欄' : '收起側邊欄'">
      <i :class="sidebarCollapsed ? 'fas fa-angle-right' : 'fas fa-angle-left'"></i>
    </button>

    <!-- 側邊欄 -->
    <div class="sidebar" :class="{ 'sidebar-open': sidebarOpen, 'sidebar-collapsed': sidebarCollapsed }">
      <div class="sidebar-header">
        <router-link class="sidebar-brand" to="/">
          <i class="fas fa-cogs"></i>
          <span class="brand-text" v-show="!sidebarCollapsed">產線排程系統</span>
        </router-link>
      </div>
      <ul class="sidebar-nav">
        <li class="nav-item">
          <router-link class="nav-link" to="/schedule-jobs">
            <i class="fas fa-calendar-alt"></i>
            <span class="nav-text" v-show="!sidebarCollapsed">Schedule Jobs</span>
          </router-link>
        </li>
        <li class="nav-item">
          <router-link class="nav-link" to="/lot-gantt">
            <i class="fas fa-diagram-project"></i>
            <span class="nav-text" v-show="!sidebarCollapsed">Lot 甘特圖</span>
          </router-link>
        </li>
        <li class="nav-item">
          <router-link class="nav-link" to="/machine-gantt">
            <i class="fas fa-cogs"></i>
            <span class="nav-text" v-show="!sidebarCollapsed">機台甘特圖</span>
          </router-link>
        </li>
        <li class="nav-item">
          <router-link class="nav-link" to="/machine-usage">
            <i class="fas fa-chart-gantt"></i>
            <span class="nav-text" v-show="!sidebarCollapsed">機台使用率</span>
          </router-link>
        </li>
        <li class="nav-item">
          <router-link class="nav-link" to="/lot-results">
            <i class="fas fa-table"></i>
            <span class="nav-text" v-show="!sidebarCollapsed">Lot 結果</span>
          </router-link>
        </li>
        <li class="nav-item">
          <router-link class="nav-link" to="/plan-models">
            <i class="fas fa-cogs"></i>
            <span class="nav-text" v-show="!sidebarCollapsed">Plan Models</span>
          </router-link>
        </li>
        <li class="nav-item">
          <router-link class="nav-link" to="/create-schedule-job">
            <i class="fas fa-plus-circle"></i>
            <span class="nav-text" v-show="!sidebarCollapsed">Create Schedule Job</span>
          </router-link>
        </li>
      </ul>
      <!-- 主題切換 -->
      <div class="sidebar-footer">
        <div class="btn-group" role="group" v-show="!sidebarCollapsed">
          <button class="btn btn-secondary btn-sm" @click="setTheme('light')" :class="{ active: currentTheme === 'light' }">
            <i class="fas fa-sun"></i> 亮色
          </button>
          <button class="btn btn-secondary btn-sm" @click="setTheme('dark')" :class="{ active: currentTheme === 'dark' }">
            <i class="fas fa-moon"></i> 暗色
          </button>
        </div>
        <div class="theme-toggle-collapsed" v-show="sidebarCollapsed">
          <button class="btn btn-secondary btn-sm me-1" @click="setTheme('light')" :class="{ active: currentTheme === 'light' }" title="亮色主題">
            <i class="fas fa-sun"></i>
          </button>
          <button class="btn btn-secondary btn-sm" @click="setTheme('dark')" :class="{ active: currentTheme === 'dark' }" title="暗色主題">
            <i class="fas fa-moon"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- 主內容區域 -->
    <main class="main-content" :class="{ 'main-content-shift': sidebarOpen }">
      <router-view />
    </main>

    <!-- 遮罩層，用於點擊關閉側邊欄 -->
    <div v-if="sidebarOpen" class="sidebar-overlay" @click="closeSidebar"></div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useTheme } from './composables/useTheme'

const { currentTheme, setTheme } = useTheme()
const sidebarOpen = ref(false)
const sidebarCollapsed = ref(false)

const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value
}

const closeSidebar = () => {
  sidebarOpen.value = false
}

const toggleSidebarMode = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}
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

/* 側邊欄樣式 */
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  width: 280px;
  background-color: var(--header-bg);
  transform: translateX(-100%);
  transition: all 0.3s ease;
  z-index: 1000;
  padding: 1rem 0;
  box-shadow: 2px 0 5px var(--shadow);
  display: flex;
  flex-direction: column;
}

.sidebar-open {
  transform: translateX(0);
}

.sidebar-collapsed {
  width: 70px;
}

.sidebar-toggle {
  position: fixed;
  top: 1rem;
  left: 1rem;
  z-index: 1001;
  background: var(--bg-color);
  border: 1px solid var(--border-color);
  padding: 0.5rem;
  border-radius: 4px;
  cursor: pointer;
  color: var(--text-color);
  transition: background-color 0.3s, color 0.3s;
}

.sidebar-toggle:hover {
  background: var(--header-bg);
}

.sidebar-header {
  padding: 0 1rem 1rem;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-brand {
  color: var(--text-color);
  text-decoration: none;
  font-size: 1.25rem;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0;
  flex: 1;
  min-width: 0;
}

.sidebar-brand:hover {
  color: var(--text-color);
  text-decoration: none;
}

.brand-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-mode-toggle {
  position: fixed;
  top: 4rem;
  left: 1rem;
  z-index: 1001;
  background: var(--bg-color);
  border: 1px solid var(--border-color);
  padding: 0.25rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  color: var(--text-color);
  transition: background-color 0.3s;
  width: 2rem;
}

.sidebar-mode-toggle:hover {
  background: var(--bg-color);
}

.sidebar-nav {
  flex: 1;
  list-style: none;
  padding: 0;
  margin: 0;
}

.sidebar-nav .nav-item {
  margin: 0;
}

.sidebar-nav .nav-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  color: var(--text-color);
  text-decoration: none;
  transition: background-color 0.3s;
  border: none;
  background: none;
  width: 100%;
  text-align: left;
  justify-content: flex-start;
}

.sidebar-collapsed .sidebar-nav .nav-link {
  justify-content: center;
  padding: 0.75rem;
}

.sidebar-nav .nav-link:hover {
  background-color: var(--bg-color);
  color: var(--text-color);
}

.sidebar-nav .nav-link.router-link-active {
  background-color: #007bff;
  color: white;
}

.nav-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  min-width: 0;
}

.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid var(--border-color);
}

.theme-toggle-collapsed {
  display: flex;
  justify-content: center;
}

.main-content {
  margin-left: 0;
  transition: margin-left 0.3s ease;
  padding: 1rem;
  min-height: 100vh;
}

.main-content-shift {
  margin-left: 280px;
}

.sidebar-open.sidebar-collapsed ~ .main-content.main-content-shift {
  margin-left: 70px;
}

.sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 999;
  display: none;
}

/* 移動設備適應 */
@media (max-width: 768px) {
  .sidebar {
    width: 250px;
  }

  .sidebar-collapsed {
    width: 60px;
  }

  .main-content-shift {
    margin-left: 250px;
  }

  .sidebar-open.sidebar-collapsed ~ .main-content.main-content-shift {
    margin-left: 60px;
  }

  .sidebar-overlay {
    display: block;
  }
}
</style>