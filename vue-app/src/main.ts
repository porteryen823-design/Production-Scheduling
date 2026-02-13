import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/main.css' // 假設我們需要一個基本的 CSS 文件

// 引入 dhtmlxgantt 的 CSS
import 'dhtmlx-gantt/codebase/dhtmlxgantt.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

app.mount('#app')
