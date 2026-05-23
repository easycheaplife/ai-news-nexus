<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { Zap, Target, BookOpen, Quote } from 'lucide-vue-next';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

const apiUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

const news = ref<any[]>([]);
const groupedNews = ref<any[]>([]);
const latestInsight = ref<any>(null);
const loading = ref(true);
const ready = ref(false);

const renderMarkdown = (text: string) => {
  if (!text) return '';
  const html = marked.parse(text);
  return DOMPurify.sanitize(html as string);
};

const fetchReportData = async () => {
  try {
    // 自动处理前缀重叠问题
    const base = apiUrl.endsWith('/api') ? apiUrl.slice(0, -4) : apiUrl;
    const today = format(new Date(), 'yyyy-MM-dd');
    const [newsRes, insightRes] = await Promise.all([
      axios.get(`${base}/api/news/`, { params: { limit: 20 } }),
      axios.get(`${base}/api/insights/${today}`).catch(() => 
        axios.get(`${base}/api/insights/latest`).catch(() => ({ data: null }))
      )
    ]);
    
    const rawNews = newsRes.data;
    news.value = rawNews;
    latestInsight.value = insightRes.data;

    // 🧠 执行话题聚类逻辑
    const clusters: Record<string, any> = {};
    const standalone: any[] = [];

    rawNews.forEach((item: any) => {
      if (item.cluster_id) {
        if (!clusters[item.cluster_id]) {
          clusters[item.cluster_id] = {
            id: item.cluster_id,
            items: [],
            // 尝试从标题中提取可能的聚类名称（如果后端没给 TopicCluster 详情的话）
            title: item.cluster_id.length < 30 ? item.cluster_id : '相关话题聚合', 
            latest_time: item.published_at
          };
        }
        clusters[item.cluster_id].items.push(item);
        if (item.published_at > clusters[item.cluster_id].latest_time) {
          clusters[item.cluster_id].latest_time = item.published_at;
        }
      } else {
        standalone.push(item);
      }
    });

    // 排序并合并
    const sortedClusters = Object.values(clusters).sort((a: any, b: any) => 
      new Date(b.latest_time).getTime() - new Date(a.latest_time).getTime()
    );

    // 最终展示结构：有聚类的排前面，没聚类的排后面
    groupedNews.value = [
      ...sortedClusters.map(c => ({ type: 'cluster', ...c })),
      ...standalone.slice(0, 5).map(i => ({ type: 'standalone', item: i }))
    ].slice(0, 10); // 总共取 Top 10

  } catch (err) {
    console.error('Failed to fetch report data:', err);
  } finally {
    loading.value = false;
    // 无论成功失败，都发送就绪信号，避免 Playwright 永久等待超时
    setTimeout(() => {
      ready.value = true;
    }, 1500);
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

      <!-- Strategic Briefing (New Section) -->
      <div v-if="latestInsight && latestInsight.content" class="p-10 pb-0">
        <div class="bg-slate-50 rounded-2xl p-8 border border-slate-100 relative">
          <div class="absolute top-4 right-6 opacity-10">
            <Quote class="w-12 h-12" />
          </div>
          <div class="flex items-center gap-2 mb-4">
            <Target class="w-4 h-4 text-primary" />
            <h2 class="text-xs font-black uppercase tracking-widest text-slate-400">今日战略简报 · Strategic Briefing</h2>
          </div>
          <div class="prose prose-sm prose-slate max-w-none prose-headings:text-slate-800 prose-p:text-slate-600 prose-strong:text-primary markdown-content" v-html="renderMarkdown(latestInsight.content)">
          </div>
        </div>
      </div>

      <!-- Timeline -->
      <div class="p-10">
        <div class="flex items-center gap-2 mb-8">
          <BookOpen class="w-4 h-4 text-primary" />
          <h2 class="text-xs font-black uppercase tracking-widest text-slate-400">核心资讯 · Top Intelligence</h2>
        </div>
        
        <div class="relative">
          <!-- Timeline line -->
          <div class="absolute left-4 top-0 bottom-0 w-[2px] bg-slate-100"></div>

          <div class="space-y-12">
            <template v-for="(group, gIdx) in groupedNews" :key="gIdx">
              <!-- Cluster Group -->
              <div v-if="group.type === 'cluster'" class="relative pl-12">
                <!-- Cluster Indicator -->
                <div class="absolute left-[11px] top-2 w-3 h-3 rounded-full bg-primary ring-4 ring-white z-10 shadow-md"></div>
                <div class="absolute left-[-2px] top-6 bottom-[-48px] w-1 bg-primary/10 rounded-full"></div>
                
                <div class="space-y-6">
                  <!-- Cluster Header -->
                  <div class="flex items-center gap-2">
                    <span class="text-[10px] font-black text-white bg-primary px-2 py-0.5 rounded uppercase tracking-widest">Topic Group</span>
                    <h3 class="text-lg font-black text-slate-900 tracking-tight">{{ group.title }}</h3>
                  </div>

                  <!-- Items in Cluster -->
                  <div class="space-y-8">
                    <div v-for="item in group.items" :key="item.id" class="space-y-3">
                      <div class="flex items-center gap-3">
                        <span class="text-[10px] font-black text-primary/60 border border-primary/20 px-1.5 py-0.5 rounded uppercase tracking-wider">
                          {{ formatDate(item.published_at) }}
                        </span>
                        <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                          {{ item.platform }}
                        </span>
                      </div>
                      
                      <h4 class="text-base font-bold text-slate-800 leading-snug">
                        {{ (item.title || '').replace(/^🐙 |^🏛️ |^🐦 |^📄 |^🎥 |^👤 |^🔥 |^💎 /, '') }}
                      </h4>
                      
                      <p class="text-sm text-slate-500 leading-relaxed">
                        {{ item.reason || (item.content ? item.content.slice(0, 500) : '') }}
                      </p>

                      <!-- Core Takeaways -->
                      <div v-if="item.takeaways && item.takeaways.length > 0" class="bg-slate-50/50 rounded-lg p-3 space-y-1 border border-slate-100/50">
                        <div v-for="(point, idx) in item.takeaways.slice(0, 5)" :key="idx" class="flex gap-2 text-[12px] text-slate-600">
                          <span class="text-primary/60 font-bold">•</span>
                          <span>{{ point }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Standalone Item -->
              <div v-else class="relative pl-12">
                <div class="absolute left-[11px] top-2 w-3 h-3 rounded-full bg-slate-300 ring-4 ring-white z-10 shadow-sm"></div>
                
                <div class="space-y-3">
                  <div class="flex items-center gap-3">
                    <span class="text-[10px] font-black text-slate-400 bg-slate-100 px-2 py-0.5 rounded uppercase tracking-wider">
                      {{ formatDate(group.item.published_at) }}
                    </span>
                    <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                      {{ group.item.platform }}
                    </span>
                  </div>
                  
                  <h3 class="text-lg font-bold text-slate-800 leading-tight">
                    {{ (group.item.title || '').replace(/^🐙 |^🏛️ |^🐦 |^📄 |^🎥 |^👤 |^🔥 |^💎 /, '') }}
                  </h3>
                  
                  <p class="text-sm text-slate-500 leading-relaxed">
                    {{ group.item.reason || (group.item.content ? group.item.content.slice(0, 500) : '') }}
                  </p>

                  <div v-if="group.item.takeaways && group.item.takeaways.length > 0" class="bg-slate-50/50 rounded-lg p-3 space-y-1 border border-slate-100/50">
                    <div v-for="(point, idx) in group.item.takeaways.slice(0, 5)" :key="idx" class="flex gap-2 text-[12px] text-slate-600">
                      <span class="text-slate-400 font-bold">•</span>
                      <span>{{ point }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- Intelligence Dashboard (New Section) -->
      <div class="p-10 pt-0">
        <div class="grid grid-cols-3 gap-4 border-t border-slate-100 pt-8">
          <div class="bg-slate-50 rounded-xl p-4 border border-slate-100">
            <div class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Intelligence Count</div>
            <div class="text-2xl font-black text-primary">{{ news.length }}+</div>
            <div class="text-[9px] text-slate-400 font-bold">Processed globally</div>
          </div>
          <div class="bg-slate-50 rounded-xl p-4 border border-slate-100">
            <div class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Trending Tech</div>
            <div class="flex flex-wrap gap-1 mt-1">
              <span v-for="kw in (latestInsight?.hot_topics?.slice(0, 3) || ['LLM', 'Agent', 'Multimodal'])" :key="kw" class="text-[9px] font-bold bg-white text-primary/70 px-1.5 py-0.5 rounded border border-primary/10 uppercase">
                {{ kw }}
              </span>
            </div>
          </div>
          <div class="bg-slate-50 rounded-xl p-4 border border-slate-100">
            <div class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Pulse Status</div>
            <div class="flex items-center gap-2 mt-1">
              <div class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
              <span class="text-[10px] font-black text-slate-600 uppercase">System OK</span>
            </div>
            <div class="text-[9px] text-slate-400 font-bold mt-1">AI Node: Active</div>
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

    <!-- Hidden element to signal readiness to Playwright (persistent) -->
    <div id="report-ready" :class="{ 'ready': ready }" class="hidden"></div>
    <div class="hidden">Debug: Loading: {{ loading }}, Ready: {{ ready }}, News Count: {{ news.length }}</div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');

#report-content {
  font-family: 'Inter', sans-serif;
}

.markdown-content :deep(h1), 
.markdown-content :deep(h2), 
.markdown-content :deep(h3) {
  font-weight: 800;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  line-height: 1.2;
}

.markdown-content :deep(p) {
  margin-bottom: 1rem;
  line-height: 1.6;
}

.markdown-content :deep(ul) {
  list-style-type: disc;
  padding-left: 1.25rem;
  margin-bottom: 1rem;
}

.markdown-content :deep(li) {
  margin-bottom: 0.5rem;
}
</style>
