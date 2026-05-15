<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import axios from 'axios';
import { Search, RefreshCw, Zap, Calendar } from 'lucide-vue-next';
import NewsCard from './components/NewsCard.vue';
import { format, isToday, isYesterday } from 'date-fns';
import { zhCN } from 'date-fns/locale';

const news = ref<any[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

const filters = ref({
  platform: '',
  query: '',
  limit: 100
});

const platforms = [
  { label: '全部来源', value: '' },
  { label: 'Twitter / X', value: 'twitter' },
  { label: 'Reddit', value: 'reddit' },
  { label: 'Hacker News', value: 'hn' },
  { label: 'Product Hunt', value: 'ph' },
];

const fetchNews = async () => {
  loading.value = true;
  try {
    const params = {
      platform: filters.value.platform || undefined,
      query: filters.value.query || undefined,
      limit: filters.value.limit
    };
    const apiUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
    const response = await axios.get(`${apiUrl}/news/`, { params });
    news.value = response.data;
    error.value = null;
  } catch (err: any) {
    error.value = '无法连接到资讯引擎。';
    console.error(err);
  } finally {
    loading.value = false;
  }
};

// 按日期分组
const groupedNews = computed(() => {
  const groups: Record<string, any[]> = {};
  news.value.forEach(item => {
    // 🛡️ 质量过滤：仅显示评分 >= 60 的优质资讯
    if (!item.score || item.score < 60) return;

    const dateKey = format(new Date(item.published_at), 'yyyy-MM-dd');
    if (!groups[dateKey]) groups[dateKey] = [];
    groups[dateKey].push(item);
  });
  return Object.entries(groups).sort((a, b) => b[0].localeCompare(a[0]));
});

const formatDateHeader = (dateStr: string) => {
  const date = new Date(dateStr);
  if (isToday(date)) return '今天 · Today';
  if (isYesterday(date)) return '昨天 · Yesterday';
  return format(date, 'MM月dd日 EEEE', { locale: zhCN });
};

onMounted(fetchNews);
watch(() => filters.value.platform, fetchNews);

let searchTimeout: any;
const handleSearch = () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(fetchNews, 500);
};
</script>

<template>
  <div class="min-h-screen bg-[#0a0a0c] text-slate-200 selection:bg-primary/30">
    <!-- Top Progress Bar -->
    <div v-if="loading" class="fixed top-0 left-0 h-[2px] bg-primary z-[60] animate-progress shadow-[0_0_10px_#2563eb]"></div>

    <!-- Header / Navigation -->
    <header class="sticky top-0 z-50 bg-[#0a0a0c]/80 backdrop-blur-xl border-b border-white/5 py-4 px-4 md:px-8">
      <div class="max-w-[1200px] mx-auto flex flex-col lg:flex-row justify-between items-center gap-6">
        <div class="flex items-center gap-4 group cursor-pointer" @click="fetchNews">
          <div class="relative">
            <div class="absolute inset-0 bg-primary/20 blur-xl group-hover:bg-primary/40 transition-all"></div>
            <div class="relative bg-gradient-to-br from-primary to-blue-600 p-2.5 rounded-2xl shadow-2xl">
              <Zap class="w-6 h-6 text-white" />
            </div>
          </div>
          <div>
            <h1 class="text-xl md:text-2xl font-black tracking-tighter text-white">
              AI NEWS <span class="text-primary">NEXUS</span>
            </h1>
            <p class="text-[10px] text-text-muted font-bold tracking-[0.2em] uppercase opacity-50">Global Intelligence Hub</p>
          </div>
        </div>

        <div class="flex flex-col sm:flex-row flex-1 max-w-3xl w-full items-center gap-3">
          <!-- Search Bar -->
          <div class="relative flex-1 w-full group">
            <Search class="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted group-focus-within:text-primary transition-colors" />
            <input 
              v-model="filters.query"
              @input="handleSearch"
              type="text" 
              placeholder="搜索全球 AI 资讯、论文、模型..." 
              class="w-full bg-white/5 border border-white/10 rounded-2xl py-3 pl-11 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all placeholder:text-text-muted/40"
            >
          </div>
          
          <!-- Platform Filter -->
          <div class="flex w-full sm:w-auto items-center gap-3">
            <div class="flex bg-white/5 p-1 rounded-2xl border border-white/10 overflow-x-auto no-scrollbar scroll-smooth">
              <button 
                v-for="p in platforms" 
                :key="p.value"
                @click="filters.platform = p.value"
                :class="[
                  'px-4 py-2 text-xs font-bold rounded-xl whitespace-nowrap transition-all duration-300',
                  filters.platform === p.value ? 'bg-primary text-white shadow-lg shadow-primary/20' : 'text-text-muted hover:text-white hover:bg-white/5'
                ]"
              >
                {{ p.label }}
              </button>
            </div>

            <button 
              @click="fetchNews"
              class="p-3 rounded-2xl bg-white/5 hover:bg-white/10 transition-all border border-white/10 text-text-muted hover:text-primary active:scale-95"
              title="刷新数据"
            >
              <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loading }" />
            </button>
          </div>
        </div>
      </div>
    </header>

    <main class="max-w-[1000px] mx-auto px-4 md:px-8 py-10 md:py-16">
      <!-- Welcome Message -->
      <div v-if="!news.length && !loading" class="text-center py-20 animate-fade-in">
        <div class="inline-block p-6 rounded-full bg-white/5 mb-6 border border-white/5">
          <Calendar class="w-12 h-12 text-text-muted opacity-20" />
        </div>
        <h2 class="text-2xl font-bold text-white mb-2">未发现相关内容</h2>
        <p class="text-text-muted max-w-xs mx-auto">请尝试调整筛选条件或搜索关键词，查看更多资讯。</p>
      </div>

      <!-- Loading State -->
      <div v-if="loading && !news.length" class="space-y-12 animate-pulse">
        <div v-for="i in 2" :key="i">
          <div class="h-6 w-48 bg-white/5 rounded-lg mb-8"></div>
          <div class="space-y-6">
            <div v-for="j in 3" :key="j" class="h-32 bg-white/5 rounded-3xl border border-white/10"></div>
          </div>
        </div>
      </div>

      <!-- News Feed (Date Grouped) -->
      <div v-else class="space-y-16">
        <section v-for="[date, items] in groupedNews" :key="date" class="relative">
          <!-- Date Header -->
          <div class="sticky top-[88px] z-40 bg-[#0a0a0c]/80 backdrop-blur-md py-4 mb-8 -mx-4 px-4">
            <div class="flex items-center gap-4">
              <h2 class="text-lg md:text-xl font-bold text-white tracking-tight flex items-center gap-3">
                <span class="w-1.5 h-6 bg-primary rounded-full"></span>
                {{ formatDateHeader(date) }}
              </h2>
              <div class="h-[1px] flex-1 bg-white/5 mx-4"></div>
              <span class="text-xs font-medium text-text-muted italic">{{ items.length }} 条资讯</span>
            </div>
          </div>

          <div class="grid grid-cols-1 gap-6 md:gap-8">
            <NewsCard 
              v-for="item in items" 
              :key="item.id" 
              :item="item" 
            />
          </div>
        </section>
      </div>
    </main>

    <!-- Background Decoration -->
    <div class="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      <div class="absolute top-0 right-0 w-[800px] h-[800px] bg-primary/5 rounded-full blur-[150px] opacity-30"></div>
      <div class="absolute bottom-0 left-0 w-[600px] h-[600px] bg-blue-600/5 rounded-full blur-[130px] opacity-20"></div>
    </div>
  </div>
</template>

<style>
.animate-progress {
  animation: progress 2s ease-in-out infinite;
  width: 100%;
}

@keyframes progress {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
