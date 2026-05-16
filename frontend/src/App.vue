<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import axios from 'axios';
import { Search, RefreshCw, Zap, Calendar, ChevronDown, ChevronUp, TrendingUp, BarChart3 } from 'lucide-vue-next';
import NewsCard from './components/NewsCard.vue';
import { format, isToday, isYesterday } from 'date-fns';
import { zhCN } from 'date-fns/locale';

const news = ref<any[]>([]);
const latestInsight = ref<any>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const showBriefing = ref(true);

const filters = ref({
  platform: '',
  query: '',
  limit: 100
});

const platforms = [
  { label: '全部来源', value: '' },
  { label: 'Twitter / X', value: 'twitter' },
  { label: 'GitHub', value: 'github' },
  { label: 'ArXiv', value: 'arxiv' },
  { label: 'YouTube', value: 'youtube' },
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

// 📈 提取今日热点关键词 (基于最新资讯)
const hotTopics = computed(() => {
  const words: Record<string, number> = {};
  const currentItems = news.value.slice(0, 30);
  currentItems.forEach(item => {
    const matches = item.title.match(/[A-Z]{2,}|AI|GPT|LLM|Sora|Gemini|Claude|DeepSeek/g);
    if (matches) {
      matches.forEach(w => {
        words[w] = (words[w] || 0) + 1;
      });
    }
  });
  return Object.entries(words)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(entry => entry[0]);
});

// 📊 计算各平台分布 (优先使用存档数据)
const platformStats = computed(() => {
  if (latestInsight.value?.stats_json) {
    return latestInsight.value.stats_json;
  }
  const stats: Record<string, number> = {};
  const platforms_list = ['twitter', 'github', 'arxiv', 'youtube', 'reddit', 'hn', 'ph'];
  platforms_list.forEach(p => stats[p] = 0);
  
  news.value.forEach(item => {
    if (stats[item.platform] !== undefined) {
      stats[item.platform]++;
    }
  });
  return stats;
});
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

    <!-- Briefing Center (Top Dashboard) -->
    <section class="max-w-[1000px] mx-auto px-4 md:px-8 pt-8">
      <div class="glass-card rounded-[2.5rem] border border-white/5 bg-[#131316]/50 overflow-hidden">
        <!-- Toggle Header -->
        <button 
          @click="showBriefing = !showBriefing"
          class="w-full flex items-center justify-between px-8 py-5 hover:bg-white/5 transition-colors group"
        >
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
              <TrendingUp class="w-4 h-4" />
            </div>
            <span class="text-sm font-black uppercase tracking-[0.2em] text-white">今日简报 · Daily Briefing</span>
          </div>
          <div class="flex items-center gap-4">
            <div v-if="!showBriefing" class="flex gap-2">
              <span v-for="tag in hotTopics.slice(0, 3)" :key="tag" class="text-[10px] font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-full uppercase">#{{ tag }}</span>
            </div>
            <component :is="showBriefing ? ChevronUp : ChevronDown" class="w-5 h-5 text-text-muted group-hover:text-white" />
          </div>
        </button>

        <!-- Briefing Content -->
        <transition 
          enter-active-class="transition-all duration-500 ease-out" 
          enter-from-class="max-h-0 opacity-0" 
          enter-to-class="max-h-[500px] opacity-100"
          leave-active-class="transition-all duration-400 ease-in"
          leave-from-class="max-h-[500px] opacity-100"
          leave-to-class="max-h-0 opacity-0"
        >
          <div v-if="showBriefing" class="px-8 pb-8 pt-2 grid grid-cols-1 md:grid-cols-2 gap-10 border-t border-white/5">
            <!-- Left: Hot Topics & Summary -->
            <div class="space-y-6">
              <div>
                <h4 class="text-[10px] font-black text-text-muted uppercase tracking-widest mb-4 flex items-center gap-2">
                  <span class="w-1 h-1 bg-primary rounded-full"></span>
                  热门关键词 Trending
                </h4>
                <div class="flex flex-wrap gap-2">
                  <button 
                    v-for="topic in hotTopics" 
                    :key="topic"
                    @click="filters.query = topic; handleSearch()"
                    class="px-4 py-2 bg-white/5 hover:bg-primary/20 border border-white/5 hover:border-primary/30 rounded-xl text-xs font-bold transition-all text-slate-300 hover:text-primary active:scale-95"
                  >
                    # {{ topic }}
                  </button>
                </div>
              </div>
              
              <div class="p-5 rounded-2xl bg-white/5 border border-white/5 italic">
                <p v-if="latestInsight" class="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
                  <span class="not-italic font-black text-[10px] text-primary uppercase block mb-2 opacity-60">AI 深度分析 · AI Analysis ({{ latestInsight.date }})</span>
                  {{ latestInsight.content }}
                </p>
                <p v-else class="text-sm text-slate-400 leading-relaxed">
                  <span class="not-italic font-black text-[10px] text-primary uppercase block mb-2 opacity-60">AI 总览 · AI Summary</span>
                  根据今日 {{ news.length }} 条资讯分析，AI 圈主要聚焦于 
                  <span class="text-white font-bold">{{ hotTopics.slice(0, 2).join(' 和 ') }}</span> 
                  相关进展。整体技术密度极高，建议优先关注评分 90+ 的硬核发布。
                </p>
              </div>
            </div>

            <!-- Right: Pulse Chart (Custom Minimal implementation) -->
            <div>
              <h4 class="text-[10px] font-black text-text-muted uppercase tracking-widest mb-4 flex items-center gap-2">
                <span class="w-1 h-1 bg-primary rounded-full"></span>
                全平台脉冲 Daily Pulse
              </h4>
              <div class="flex items-end justify-between gap-2 h-32 pt-4">
                <div 
                  v-for="(count, platform) in platformStats" 
                  :key="platform"
                  class="flex-1 flex flex-col items-center group/bar"
                >
                  <div 
                    class="w-full bg-primary/20 group-hover/bar:bg-primary/40 rounded-t-lg transition-all duration-700 relative"
                    :style="{ height: `${(count / (Math.max(...Object.values(platformStats)) || 1)) * 100}%` }"
                  >
                    <div class="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px] font-bold text-primary opacity-0 group-hover/bar:opacity-100 transition-opacity">
                      {{ count }}
                    </div>
                  </div>
                  <span class="text-[9px] font-black uppercase text-text-muted mt-2 opacity-50">{{ platform.slice(0, 2) }}</span>
                </div>
              </div>
              <div class="mt-6 flex justify-between items-center text-[10px] text-text-muted font-bold px-2">
                <div class="flex items-center gap-1">
                  <BarChart3 class="w-3 h-3" />
                  各来源活跃度
                </div>
                <span>Update: {{ format(new Date(), 'HH:mm') }}</span>
              </div>
            </div>
          </div>
        </transition>
      </div>
    </section>

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
 { transform: translateX(100%); }
}

.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
tyle>
