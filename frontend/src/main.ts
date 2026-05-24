import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import './style.css'
import App from './App.vue'
import Home from './views/Home.vue'
import ReportsList from './views/ReportsList.vue'
import ReportTemplate from './components/ReportTemplate.vue'
import Landing from './views/Landing.vue'

const routes = [
  { path: '/', component: Landing },
  { path: '/app', component: Home },
  { path: '/reports-list', component: ReportsList },
  { path: '/report', component: ReportTemplate }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const app = createApp(App)
app.use(router)
app.mount('#app')
