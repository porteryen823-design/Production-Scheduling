import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LotGanttView from '../views/LotGanttView.vue'
import MachineGanttView from '../views/MachineGanttView.vue'
import MachineUsageView from '../views/MachineUsageView.vue'
import LotPlanResultView from '../views/LotPlanResultView.vue'
import ScheduleJobView from '../views/ScheduleJobView.vue'
import PlanModelsView from '../views/PlanModelsView.vue'
import CreateScheduleJobView from '../views/CreateScheduleJobView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/lot-gantt',
      name: 'lot-gantt',
      component: LotGanttView
    },
    {
      path: '/machine-gantt',
      name: 'machine-gantt',
      component: MachineGanttView
    },
    {
      path: '/machine-usage',
      name: 'machine-usage',
      component: MachineUsageView
    },
    {
      path: '/lot-results',
      name: 'lot-results',
      component: LotPlanResultView
    },
    {
      path: '/schedule-jobs',
      name: 'schedule-jobs',
      component: ScheduleJobView
    },
    {
      path: '/plan-models',
      name: 'plan-models',
      component: PlanModelsView
    },
    {
      path: '/create-schedule-job',
      name: 'create-schedule-job',
      component: CreateScheduleJobView
    }
  ]
})

export default router
