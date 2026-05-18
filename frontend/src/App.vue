<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import axios from 'axios';
import { Search, RefreshCw, Zap, Calendar, ChevronDown, ChevronUp, TrendingUp, BarChart3, X } from 'lucide-vue-next';
import NewsCard from './components/NewsCard.vue';
import { format, isToday, isYesterday } from 'date-fns';
import { zhCN } from 'date-fns/locale';

const news = ref<any[]>([]);
const latestInsight = ref<any>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const showBriefing = ref(true);

// 🔍 灯箱 (Lightbox) 状态
const lightbox = ref({
  isOpen: false,
  mediaUrl: '',
  title: '',
  isVideo: false
});
const lightboxLoading = ref(true);

const openLightbox = (item: any) => {
  if (!item.media_urls || item.media_urls.length === 0) return;
  
  // 🧩 处理编码过的 URL
  const decodeUrl = (url: string) => {
    const txt = document.createElement('textarea');
    txt.innerHTML = url;
    return txt.value;
  };

  // 🔗 智能路径拼接
  const getFullUrl = (url: string) => {
    if (!url) return '';
    const decoded = decodeUrl(url);
    // 如果是相对路径 (/f/ 打头)，自动拼接后端地址
    if (decoded.startsWith('/f/')) {
      const apiUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
      // 如果 apiUrl 是 /api (Netlify 代理模式)，则保持相对路径，让浏览器处理
      if (!apiUrl.startsWith('http')) return decoded;
      return `${apiUrl}${decoded}`;
    }
    return decoded;
  };

  const rawUrl = item.media_urls[0];
  const url = getFullUrl(rawUrl);
  const videoExtensions = ['.mp4', '.webm', '.ogg', '.m3u8', 'video', 'ext_tw_video', 'amplify_video'];
  
  lightboxLoading.value = true;
  lightbox.value = {
    isOpen: true,
    mediaUrl: url,
    title: item.title,
    isVideo: videoExtensions.some(ext => url.toLowerCase().includes(ext))
  };
  document.body.style.overflow = 'hidden';
};

const closeLightbox = () => {
  lightbox.value.isOpen = false;
  document.body.style.overflow = 'auto';
};

// 监听键盘 ESC
onMounted(() => {
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && lightbox.value.isOpen) closeLightbox();
  });
});

const hasMore = ref(true);
const loadingMore = ref(false);

const filters = ref({
  platform: '',
  query: '',
  limit: 100,
  skip: 0
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

const fetchNews = async (isLoadMore = false) => {
  if (isLoadMore) {
    loadingMore.value = true;
  } else {
    loading.value = true;
    filters.value.skip = 0;
  }

  try {
    const params = {
      platform: filters.value.platform || undefined,
      query: filters.value.query || undefined,
      limit: filters.value.limit,
      skip: filters.value.skip
    };
    const apiUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
    
    if (isLoadMore) {
      // 仅抓取更多资讯
      const response = await axios.get(`${apiUrl}/news/`, { params });
      const newItems = response.data;
      news.value = [...news.value, ...newItems];
      hasMore.value = newItems.length === filters.value.limit;
    } else {
      // 并行抓取资讯和最新洞察
      const [newsRes, insightRes] = await Promise.all([
        axios.get(`${apiUrl}/news/`, { params }),
        axios.get(`${apiUrl}/insights/latest`).catch(() => ({ data: null }))
      ]);
      
      news.value = newsRes.data;
      latestInsight.value = insightRes.data;
      hasMore.value = news.value.length === filters.value.limit;
      console.log('Briefing Data Received:', latestInsight.value);
    }
    
    error.value = null;
  } catch (err: any) {
    error.value = '无法连接到资讯引擎。';
    console.error(err);
  } finally {
    loading.value = false;
    loadingMore.value = false;
  }
};

const loadMore = () => {
  filters.value.skip += filters.value.limit;
  fetchNews(true);
};

// 按日期分组
const groupedNews = computed(() => {
  const groups: Record<string, any[]> = {};
  news.value.forEach(item => {
    // 🛡️ 质量过滤：降低门槛确保首页有内容 (评分 < 30 的极低质量内容除外)
    if (item.score !== undefined && item.score !== null && item.score < 30) return;

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

onMounted(() => fetchNews(false));
watch(() => filters.value.platform, () => fetchNews(false));

let searchTimeout: any;
const handleSearch = () => {
  clearTimeout(searchTimeout);
  filters.value.skip = 0; // 重置分页
  searchTimeout = setTimeout(() => fetchNews(false), 500);
};

// 📈 提取今日热点关键词 (优先从后端 Insight 获取)
const hotTopics = computed(() => {
  if (latestInsight.value?.hot_topics) {
    return latestInsight.value.hot_topics;
  }
  const words: Record<string, number> = {};
  const currentItems = news.value.slice(0, 30);
  currentItems.forEach(item => {
    const matches = item.title.match(/[A-Z]{2,}|AI|GPT|LLM|Sora|Gemini|Claude|DeepSeek/g);
    if (matches) {
      matches.forEach((w: string) => {
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

const platformFullNames: Record<string, string> = {
  twitter: 'Twitter',
  github: 'GitHub',
  arxiv: 'ArXiv',
  youtube: 'YouTube',
  reddit: 'Reddit',
  hn: 'HackerNews',
  ph: 'ProductHunt'
};

const platformBarColors: Record<string, string> = {
  twitter: 'bg-sky-500',
  github: 'bg-slate-200',
  arxiv: 'bg-red-500',
  youtube: 'bg-red-600',
  reddit: 'bg-orange-500',
  hn: 'bg-orange-400',
  ph: 'bg-orange-600'
};

// 📝 极简 Markdown 渲染逻辑
const renderMarkdown = (text: string) => {
  if (!text) return '';
  return text
    .replace(/### (.*)/g, '<h3 class="text-lg font-bold text-white mb-4 mt-2 border-l-4 border-primary pl-3">$1</h3>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong class="text-primary font-bold">$1</strong>')
    .replace(/\n\n/g, '<br/>')
    .replace(/\n/g, '<br/>');
};
</script>

<template>
  <div class="min-h-screen bg-[#0a0a0c] text-slate-200 selection:bg-primary/30">
    <!-- Top Progress Bar -->
    <div v-if="loading" class="fixed top-0 left-0 h-[2px] bg-primary z-[60] animate-progress shadow-[0_0_10px_#2563eb]"></div>

    <!-- 🌠 Global Lightbox -->
    <transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div v-if="lightbox.isOpen" class="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-10 bg-black/95 backdrop-blur-2xl" @click="closeLightbox">
        <button class="absolute top-6 right-8 text-white/50 hover:text-white transition-all p-2 z-[110] hover:rotate-90">
          <X class="w-10 h-10" /> 
        </button>
        
        <div class="relative max-w-6xl w-full flex flex-col items-center gap-8" @click.stop>
          <div class="w-full aspect-video rounded-3xl overflow-hidden shadow-2xl border border-white/10 bg-black flex items-center justify-center relative">
            <!-- Loading Spinner -->
            <div v-if="lightboxLoading" class="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-[#0a0a0c]">
              <RefreshCw class="w-10 h-10 text-primary animate-spin" />
              <span class="text-xs font-bold text-text-muted uppercase tracking-[0.2em]">正在加载高清资源...</span>
            </div>

            <video 
              v-if="lightbox.isVideo" 
              :src="lightbox.mediaUrl" 
              class="w-full h-full object-contain" 
              controls 
              autoplay
              referrerpolicy="no-referrer"
              @loadedmetadata="lightboxLoading = false"
            ></video>
            <img 
              v-else 
              :src="lightbox.mediaUrl" 
              class="w-full h-full object-contain" 
              alt="Full resolution preview"
              referrerpolicy="no-referrer"
              @load="lightboxLoading = false"
              @error="lightboxLoading = false"
            />
          </div>
          <div class="text-center space-y-2">
            <h2 class="text-xl md:text-2xl font-bold text-white leading-tight px-4">{{ lightbox.title }}</h2>
            <p class="text-sm text-text-muted italic opacity-50">点击背景区域、按 ESC 或 [X] 退出预览</p>
          </div>
        </div>
      </div>
    </transition>

    <!-- Header / Navigation -->
    <header class="sticky top-0 z-50 bg-[#0a0a0c]/80 backdrop-blur-xl border-b border-white/5 py-4 px-4 md:px-8">
      <div class="max-w-[1200px] mx-auto flex flex-col lg:flex-row justify-between items-center gap-6">
        <div class="flex items-center gap-4 group cursor-pointer" @click="() => fetchNews(false)">
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
              @click="() => fetchNews(false)"
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
    <section class="max-w-[1400px] mx-auto px-4 md:px-8 pt-8">
      <div class="glass-card rounded-[2.5rem] border border-white/5 bg-[#131316]/50 overflow-hidden shadow-2xl shadow-primary/5">
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
          enter-to-class="max-h-[800px] opacity-100"
          leave-active-class="transition-all duration-400 ease-in"
          leave-from-class="max-h-[800px] opacity-100"
          leave-to-class="max-h-0 opacity-0"
        >
          <div v-if="showBriefing" class="px-8 pb-10 pt-4 flex flex-col xl:flex-row gap-10 border-t border-white/5 bg-[#1a1a20]/30">
            <!-- 1. Left Column: Hot Topics (1/4) -->
            <div class="xl:w-1/4 space-y-6">
              <h4 class="text-[10px] font-black text-text-muted uppercase tracking-widest mb-4 flex items-center gap-2">
                <span class="w-1 h-1 bg-primary rounded-full"></span>
                热门关键词 Trending
              </h4>
              <div class="flex flex-wrap gap-2">
                <button 
                  v-for="topic in hotTopics" 
                  :key="topic"
                  @click="filters.query = topic; handleSearch()"
                  class="px-3 py-1.5 bg-white/5 hover:bg-primary/20 border border-white/5 hover:border-primary/30 rounded-lg text-[11px] font-bold transition-all text-slate-400 hover:text-primary active:scale-95"
                >
                  # {{ topic }}
                </button>
              </div>
            </div>

            <!-- 2. Middle Column: AI Strategic Briefing (2/4) -->
            <div class="xl:w-2/4 xl:border-x xl:border-white/5 xl:px-10">
              <h4 class="text-[10px] font-black text-text-muted uppercase tracking-widest mb-6 flex items-center gap-2">
                <span class="w-1 h-1 bg-primary rounded-full"></span>
                AI 战略简报 Strategic Insights
              </h4>
              <div class="prose prose-invert max-w-none">
                <div 
                  v-if="latestInsight" 
                  class="text-sm text-slate-300 leading-loose"
                  v-html="renderMarkdown(latestInsight.content)"
                ></div>
                <div v-else class="p-6 rounded-2xl bg-primary/5 border border-primary/10 italic">
                  <p class="text-sm text-primary leading-relaxed">
                    根据今日 {{ news.length }} 条资讯分析，AI 圈主要聚焦于 
                    <span class="text-white font-bold">{{ hotTopics.slice(0, 2).join(' 和 ') }}</span> 
                    相关进展。整体技术密度极高，建议优先关注评分 90+ 的硬核发布。
                  </p>
                </div>
              </div>
            </div>

            <!-- 3. Right Column: Daily Pulse Chart (1/4) -->
            <div class="xl:w-1/4">
              <h4 class="text-[10px] font-black text-text-muted uppercase tracking-widest mb-8 flex items-center gap-2">
                <span class="w-1 h-1 bg-primary rounded-full"></span>
                全平台脉冲 Daily Pulse
              </h4>
              <div class="flex items-end justify-between gap-2 h-36 pt-4 px-2">
                <div 
                  v-for="(count, platform) in platformStats" 
                  :key="platform"
                  class="flex-1 flex flex-col items-center group/bar"
                >
                  <div 
                    class="w-full relative rounded-t-md transition-all duration-700 hover:brightness-125"
                    :class="[platformBarColors[platform] || 'bg-primary/20', count === 0 ? 'opacity-10' : 'opacity-60']"
                    :style="{ height: `${(count / (Math.max(...(Object.values(platformStats) as number[])) || 1)) * 100}%` }"
                  >
                    <div class="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px] font-black text-white opacity-0 group-hover/bar:opacity-100 transition-opacity">
                      {{ count }}
                    </div>
                  </div>
                  <span class="text-[8px] font-black uppercase text-text-muted mt-3 opacity-50 rotate-[-45deg] origin-top-left whitespace-nowrap">
                    {{ platformFullNames[platform] || platform }}
                  </span>
                </div>
              </div>
              <div class="mt-12 flex justify-between items-center text-[9px] text-text-muted font-bold px-2 pt-4 border-t border-white/5">
                <div class="flex items-center gap-1">
                  <BarChart3 class="w-3 h-3" />
                  源活跃度分布
                </div>
                <span>{{ format(new Date(), 'HH:mm') }}</span>
              </div>
            </div>
          </div>
        </transition>
      </div>
    </section>

    <main class="max-w-[1400px] mx-auto px-4 md:px-8 py-10 md:py-16">
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
      <div v-else class="space-y-20">
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

          <div class="flex flex-col gap-4 md:gap-5">
            <NewsCard 
              v-for="item in items" 
              :key="item.id" 
              :item="item" 
              :isFeatured="item.score >= 90"
              class="w-full"
              @expand-media="openLightbox"
            />
          </div>
        </section>

        <!-- 🚀 Load More -->
        <div v-if="hasMore" class="flex justify-center pt-10 pb-20">
          <button 
            @click="loadMore"
            :disabled="loadingMore"
            class="flex items-center gap-3 px-10 py-4 bg-white/5 hover:bg-primary/20 border border-white/10 hover:border-primary/30 rounded-2xl text-sm font-black uppercase tracking-[0.2em] text-slate-400 hover:text-white transition-all active:scale-95 disabled:opacity-50 disabled:pointer-events-none group"
          >
            <RefreshCw v-if="loadingMore" class="w-4 h-4 animate-spin" />
            <ChevronDown v-else class="w-4 h-4 group-hover:translate-y-0.5 transition-transform" />
            {{ loadingMore ? '正在加载...' : '加载更多资讯 · Load More' }}
          </button>
        </div>
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

@keyframes slide-up {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-slide-up {
  animation: slide-up 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

/* 📝 Markdown Rendering Styles */
.prose h3 {
  letter-spacing: -0.025em;
  text-shadow: 0 0 20px rgba(37, 99, 235, 0.2);
}
.prose strong {
  color: #60a5fa;
  background: rgba(37, 99, 235, 0.1);
  padding: 0 4px;
  border-radius: 4px;
}
</style>
