<template>
  <div class="automated-test-container">
    <div class="header">
      <h1><i class="fas fa-vial"></i> 自動化測試控制台</h1>
      <div class="status-badge" :class="statusClass">
        {{ statusText }}
      </div>
    </div>

    <div class="main-layout">
      <!-- 左側腳本列表 -->
      <div class="sidebar-list shadow-sm">
        <h3>測試腳本</h3>
        <div v-if="loading" class="text-center p-3">
          <div class="spinner-border spinner-border-sm" role="status"></div>
          載入中...
        </div>
        <div v-else-if="scripts.length === 0" class="text-muted p-3">
          無可用腳本
        </div>
        <ul v-else class="list-group">
          <li 
            v-for="script in scripts" 
            :key="script.id"
            class="list-group-item list-group-item-action"
            :class="{ active: selectedScript?.id === script.id }"
            @click="selectScript(script)"
          >
            <div class="fw-bold">{{ script.name }}</div>
            <small class="text-truncate d-block">{{ script.description }}</small>
          </li>
        </ul>
        <button class="btn btn-outline-secondary btn-sm mt-3 w-100" @click="fetchScripts" :disabled="isTesting">
          <i class="fas fa-sync"></i> 重新整理
        </button>
      </div>

      <!-- 右側控制與日誌 -->
      <div class="content-area">
        <div class="control-panel shadow-sm mb-3">
          <div class="d-flex align-items-center justify-content-between">
            <div class="selected-info">
              <span v-if="selectedScript" class="badge bg-primary me-2">{{ selectedScript.name }}</span>
              <span v-else class="text-muted">請選擇一個腳本開始測試</span>
            </div>
            <div class="actions">
              <button 
                class="btn btn-success me-2" 
                :disabled="!selectedScript || isTesting"
                @click="startTest"
              >
                <i class="fas fa-play"></i> 執行測試
              </button>
              <button 
                class="btn btn-danger" 
                :disabled="!isTesting"
                @click="stopTest"
              >
                <i class="fas fa-stop"></i> 停止測試
              </button>
            </div>
          </div>
        </div>

        <!-- 日誌顯示區 -->
        <div class="log-container shadow-sm" ref="logContainer">
          <div v-for="(log, index) in logs" :key="index" class="log-line" :class="log.type">
            <span class="log-time">[{{ log.time }}]</span>
            <span class="log-content">{{ log.content }}</span>
          </div>
          <div v-if="logs.length === 0" class="empty-logs">
            等待執行...
          </div>
        </div>
        <div class="d-flex justify-content-end mt-2">
          <button class="btn btn-sm btn-link text-decoration-none" @click="clearLogs">
            <i class="fas fa-trash"></i> 清除日誌
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick } from 'vue';
import { API_BASE_URL } from '../utils/apiConfig';
import api from '../utils/apiConfig';

interface TestScript {
  id: string;
  name: string;
  description: string;
  filename: string;
}

interface LogEntry {
  time: string;
  content: string;
  type: 'log' | 'error' | 'status' | 'finished';
}

const scripts = ref<TestScript[]>([]);
const selectedScript = ref<TestScript | null>(null);
const loading = ref(false);
const isTesting = ref(false);
const logs = ref<LogEntry[]>([]);
const logContainer = ref<HTMLElement | null>(null);
const eventSource = ref<EventSource | null>(null);

const statusText = computed(() => {
  if (isTesting.value) return '測試執行中...';
  if (logs.value.some(l => l.type === 'finished')) return '測試已完成';
  if (logs.value.some(l => l.type === 'error')) return '測試發生錯誤';
  return '準備就緒';
});

const statusClass = computed(() => {
  if (isTesting.value) return 'bg-warning text-dark';
  if (logs.value.some(l => l.type === 'finished')) return 'bg-success';
  if (logs.value.some(l => l.type === 'error')) return 'bg-danger';
  return 'bg-secondary';
});

const fetchScripts = async () => {
  loading.value = true;
  try {
    const response = await api.get('/api/v1/automation/scripts');
    scripts.value = response.data;
  } catch (error) {
    console.error('Failed to fetch scripts:', error);
  } finally {
    loading.value = false;
  }
};

const selectScript = (script: TestScript) => {
  if (!isTesting.value) {
    selectedScript.value = script;
  }
};

const startTest = () => {
  if (!selectedScript.value || isTesting.value) return;

  clearLogs();
  isTesting.value = true;
  
  const apiUrl = `${API_BASE_URL}/api/v1/automation/run-test/${selectedScript.value.filename}`;
  eventSource.value = new EventSource(apiUrl);

  eventSource.value.onmessage = (event) => {
    const data = JSON.parse(event.data);
    addLog(data.content || '', data.type);

    if (data.type === 'finished') {
      stopEventSource();
      isTesting.value = false;
    }
    
    if (data.type === 'error') {
      stopEventSource();
      isTesting.value = false;
    }
  };

  eventSource.value.onerror = (error) => {
    console.error('SSE Error:', error);
    addLog('與伺服器連接中斷或發生錯誤', 'error');
    stopEventSource();
    isTesting.value = false;
  };
};

const stopTest = () => {
  if (eventSource.value) {
    addLog('手動中止測試...', 'status');
    stopEventSource();
    isTesting.value = false;
  }
};

const stopEventSource = () => {
  if (eventSource.value) {
    eventSource.value.close();
    eventSource.value = null;
  }
};

const addLog = (content: string, type: any = 'log') => {
  const time = new Date().toLocaleTimeString();
  logs.value.push({ time, content, type });
  
  // 自動滾動到底部
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight;
    }
  });
};

const clearLogs = () => {
  logs.value = [];
};

onMounted(() => {
  fetchScripts();
});
</script>

<style scoped>
.automated-test-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 40px);
  padding: 10px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.status-badge {
  padding: 5px 15px;
  border-radius: 20px;
  font-weight: bold;
}

.main-layout {
  display: flex;
  flex: 1;
  gap: 20px;
  min-height: 0;
}

.sidebar-list {
  width: 300px;
  background: var(--header-bg);
  border-radius: 8px;
  padding: 15px;
  display: flex;
  flex-direction: column;
}

.content-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.control-panel {
  background: var(--header-bg);
  padding: 15px;
  border-radius: 8px;
}

.log-container {
  flex: 1;
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: 'Consolas', 'Monaco', monospace;
  padding: 15px;
  border-radius: 8px;
  overflow-y: auto;
  font-size: 14px;
}

.log-line {
  margin-bottom: 2px;
  white-space: pre-wrap;
  word-break: break-all;
}

.log-time {
  color: #569cd6;
  margin-right: 10px;
}

.log-line.error { color: #f44336; }
.log-line.status { color: #ce9178; font-weight: bold; }
.log-line.finished { color: #4caf50; font-weight: bold; }

.empty-logs {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  font-style: italic;
}

.list-group-item {
  cursor: pointer;
  border: none;
  background: transparent;
  color: var(--text-color);
  border-radius: 4px !important;
  margin-bottom: 5px;
}

.list-group-item:hover {
  background: rgba(0, 123, 255, 0.1);
}

.list-group-item.active {
  background: #007bff;
  color: white;
}

[data-theme="dark"] .sidebar-list,
[data-theme="dark"] .control-panel {
  background: #252525;
}
</style>
