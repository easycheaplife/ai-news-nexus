import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import './style.css'
import App from './App.vue'
import Home from './views/Home.vue'
import ReportsList from './views/ReportsList.vue'
import ReportTemplate from './components/ReportTemplate.vue'
import Landing from './views/Landing.vue'
import Wiki from './views/Wiki.vue'
import Whitepapers from './views/Whitepapers.vue'

const routes = [
  { path: '/', component: Landing },
  { path: '/app', component: Home },
  { path: '/reports-list', component: ReportsList },
  { path: '/report', component: ReportTemplate },
  { path: '/wiki', component: Wiki },
  { path: '/whitepapers', component: Whitepapers }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const app = createApp(App)
app.use(router)
app.mount('#app')
