<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { Zap } from 'lucide-vue-next';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';

const apiUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

const news = ref<any[]>([]);
const latestInsight = ref<any>(null);
const loading = ref(true);
const ready = ref(false);

const fetchReportData = async () => {
  try {
    // 自动处理前缀重叠问题
    const base = apiUrl.endsWith('/api') ? apiUrl.slice(0, -4) : apiUrl;
    const [newsRes, insightRes] = await Promise.all([
      axios.get(`${base}/api/news/`, { params: { limit: 10 } }),
      axios.get(`${base}/api/insights/latest`).catch(() => ({ data: null }))
    ]);
    
    news.value = newsRes.data;
    latestInsight.value = insightRes.data;
  } catch (err) {
    console.error('Failed to fetch report data:', err);
  } finally {
    loading.value = false;
    // 无论成功失败，都发送就绪信号，避免 Playwright 永久等待超时
    setTimeout(() => {
      ready.value = true;
    }, 1000);
  }
};

const formatDate = (dateStr: string) => {
  try {
    return format(new Date(dateStr), 'HH:mm');
  } catch {
    return '00:00';
  }
};

onMounted(fetchReportData);
</script>

<template>
  <div :class="{ 'opacity-100': !loading, 'opacity-0': loading }" class="min-h-screen bg-[#f0f2f5] p-10 transition-opacity duration-500">
    <div id="report-content" class="max-w-[700px] mx-auto bg-white rounded-3xl shadow-2xl overflow-hidden border border-slate-200">
      <!-- Header -->
      <div class="bg-gradient-to-br from-[#1a1a20] to-[#0a0a0c] p-10 text-white relative overflow-hidden">
        <div class="absolute top-0 right-0 w-64 h-64 bg-primary/20 rounded-full blur-[100px] -mr-32 -mt-32"></div>
        <div class="relative z-10">
          <div class="flex items-center gap-4 mb-6">
            <div class="bg-primary p-3 rounded-2xl shadow-lg shadow-primary/30">
              <Zap class="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 class="text-3xl font-black tracking-tighter uppercase">AI NEWS <span class="text-primary">DAILY</span></h1>
              <p class="text-[10px] font-bold tracking-[0.3em] text-slate-400 uppercase">Global Intelligence Report</p>
            </div>
          </div>
          <div class="flex justify-between items-end border-t border-white/10 pt-6">
            <div class="text-2xl font-bold">{{ format(new Date(), 'yyyy年MM月dd日', { locale: zhCN }) }}</div>
            <div class="text-slate-400 font-bold uppercase tracking-widest text-xs">{{ format(new Date(), 'EEEE', { locale: zhCN }) }}</div>
          </div>
        </div>
      </div>

      <!-- Timeline -->
      <div class="p-10">
        <div class="relative">
          <!-- Timeline line -->
          <div class="absolute left-4 top-0 bottom-0 w-[2px] bg-slate-100"></div>

          <div class="space-y-12">
            <div v-for="item in news.slice(0, 8)" :key="item.id" class="relative pl-12 group">
              <!-- Dot -->
              <div class="absolute left-[11px] top-2 w-3 h-3 rounded-full bg-primary ring-4 ring-white z-10 shadow-md"></div>
              
              <div class="space-y-3">
                <div class="flex items-center gap-3">
                  <span class="text-xs font-black text-primary bg-primary/10 px-2 py-1 rounded-md uppercase tracking-wider">
                    {{ formatDate(item.published_at) }}
                  </span>
                  <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                    {{ item.platform }}
                  </span>
                </div>
                
                <h3 class="text-xl font-bold text-slate-800 leading-tight">
                  {{ (item.title || '').replace(/^🐙 |^🏛️ |^🐦 |^📄 |^🎥 |^👤 |^🔥 |^💎 /, '') }}
                </h3>
                
                <p class="text-sm text-slate-500 leading-relaxed line-clamp-3">
                  {{ item.reason || (item.content ? item.content.slice(0, 200) : 'No content available.') }}
                </p>

                <div v-if="item.trending_keywords && item.trending_keywords.length > 0" class="flex gap-2 pt-1">
                  <span v-for="tag in item.trending_keywords.slice(0, 3)" :key="tag" class="text-[9px] font-bold bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full uppercase">
                    #{{ tag }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="bg-slate-50 p-10 border-t border-slate-100 flex justify-between items-center">
        <div class="flex items-center gap-2">
          <div class="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
          <span class="text-[10px] font-black text-slate-400 uppercase tracking-widest">Synthesized by AI News Nexus</span>
        </div>
        <div class="text-[10px] font-bold text-slate-300 uppercase tracking-widest">Generated at {{ format(new Date(), 'HH:mm') }}</div>
      </div>
    </div>

    <!-- Hidden element to signal readiness to Playwright -->
    <div v-if="ready" id="report-ready" class="hidden"></div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');

#report-content {
  font-family: 'Inter', sans-serif;
}
</style>
