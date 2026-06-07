<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { Zap, Target, Quote } from 'lucide-vue-next';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

const apiUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

const news = ref<any[]>([]);
const latestInsight = ref<any>(null);
const loading = ref(true);
const ready = ref(false);

const renderMarkdown = (text: string) => {
  if (!text) return '';
  
  // 🩹 鲁棒性增强：移除多余的元数据行（撰写人、日期等），并修复标题格式
  const cleanedText = text
    .replace(/^撰写人：.*$/gm, '')
    .replace(/^日期：.*$/gm, '')
    .replace(/^报告人：.*$/gm, '')
    .replace(/^##\s+##\s+/gm, '## ')
    .replace(/^###\s+###\s+/gm, '### ')
    .replace(/([^ \n])\n(##|###)\s+/g, '$1\n\n$2 ');

  // 🧩 极致解析配置：确保 GFM 开启且处理换行
  const html = marked.parse(cleanedText, { 
    gfm: true, 
    breaks: true 
  });
  return DOMPurify.sanitize(html as string);
};

const fetchReportData = async () => {
  try {
    const base = apiUrl.endsWith('/api') ? apiUrl.slice(0, -4) : apiUrl;
    const today = format(new Date(), 'yyyy-MM-dd');
    const timestamp = Date.now();
    const [newsRes, insightRes] = await Promise.all([
      axios.get(`${base}/api/news/`, { params: { limit: 20, _t: timestamp } }),
      axios.get(`${base}/api/insights/${today}`, { params: { _t: timestamp } }).catch(() => 
        axios.get(`${base}/api/insights/latest`, { params: { _t: timestamp } }).catch(() => ({ data: null }))
      )
    ]);
    
    news.value = newsRes.data.items || [];
    latestInsight.value = insightRes.data;
  } catch (err) {
    console.error('Failed to fetch report data:', err);
  } finally {
    loading.value = false;
    setTimeout(() => {
      ready.value = true;
    }, 1500);
  }
};

onMounted(fetchReportData);
</script>

<template>
  <div :class="{ 'opacity-100': !loading, 'opacity-0': loading }" class="min-h-screen bg-[#f0f2f5] p-10 transition-opacity duration-500">
    <div id="report-content" class="max-w-[800px] mx-auto bg-white rounded-3xl shadow-2xl overflow-hidden border border-slate-200">
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

      <!-- Global Intelligence Synthesis -->
      <div v-if="latestInsight && latestInsight.content" class="p-12 pb-16">
        <div class="bg-white relative">
          <div class="absolute -top-6 right-0 opacity-10">
            <Quote class="w-24 h-24 text-slate-400" />
          </div>
          <div class="flex items-center gap-3 mb-10 border-b-2 border-primary/10 pb-6">
            <Target class="w-7 h-7 text-primary" />
            <h2 class="text-xl font-black uppercase tracking-[0.2em] text-slate-900">深度战略综述 · Strategic Synthesis</h2>
          </div>
          
          <div class="synthesis-content" v-html="renderMarkdown(latestInsight.content)"></div>
        </div>
      </div>

      <!-- Intelligence Dashboard -->
      <div class="p-12 pt-0">
        <div class="grid grid-cols-3 gap-6 border-t border-slate-100 pt-10">
          <div class="bg-slate-50 rounded-2xl p-5 border border-slate-100">
            <div class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Intelligence Count</div>
            <div class="text-3xl font-black text-primary">{{ latestInsight?.stats_json?.Total || news.length }}+</div>
            <div class="text-[11px] text-slate-400 font-bold mt-1">Processed globally</div>
          </div>
          <div class="bg-slate-50 rounded-2xl p-5 border border-slate-100">
            <div class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Trending Tech</div>
            <div class="flex flex-wrap gap-1.5 mt-1">
              <span v-for="kw in (latestInsight?.hot_topics?.slice(0, 3) || ['LLM', 'Agent', 'Multimodal'])" :key="kw" class="text-[10px] font-bold bg-white text-primary px-2 py-0.5 rounded border border-primary/20 uppercase">
                {{ kw }}
              </span>
            </div>
          </div>
          <div class="bg-slate-50 rounded-2xl p-5 border border-slate-100">
            <div class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Pulse Status</div>
            <div class="flex items-center gap-2 mt-1">
              <div class="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse"></div>
              <span class="text-[11px] font-black text-slate-700 uppercase">System OK</span>
            </div>
            <div class="text-[11px] text-slate-400 font-bold mt-1">AI Node: Active</div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="bg-slate-50 p-12 border-t border-slate-100 flex justify-between items-center">
        <div class="flex items-center gap-2">
          <div class="w-2 h-2 rounded-full bg-primary"></div>
          <span class="text-[11px] font-black text-slate-400 uppercase tracking-widest">Synthesized by AI News Nexus</span>
        </div>
        <div class="text-[11px] font-bold text-slate-300 uppercase tracking-widest">Generated at {{ format(new Date(), 'HH:mm') }}</div>
      </div>
    </div>

    <!-- Signal for Playwright -->
    <div id="report-ready" :class="{ 'ready': ready }" class="hidden"></div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');

#report-content {
  font-family: 'Inter', sans-serif;
  background-color: white;
}

.synthesis-content {
  color: #1e293b !important; /* slate-800 */
  line-height: 1.8;
  font-size: 16px;
}

.synthesis-content :deep(h1),
.synthesis-content :deep(h2),
.synthesis-content :deep(h3),
.synthesis-content :deep(h4) {
  color: #0f172a !important; /* Force slate-900 */
  font-weight: 900;
  margin-top: 2rem;
  margin-bottom: 1rem;
  border-left: 5px solid #6366f1;
  padding-left: 1rem;
  line-height: 1.2;
}

.synthesis-content :deep(h2) { font-size: 1.5rem; }
.synthesis-content :deep(h3) { font-size: 1.25rem; }
.synthesis-content :deep(h4) { font-size: 1.05rem; border-left-width: 3px; }

.synthesis-content :deep(p) {
  margin-bottom: 1.5rem;
  text-align: justify;
}

.synthesis-content :deep(strong) {
  color: #0f172a !important;
  font-weight: 800;
  background-color: rgba(254, 240, 138, 0.5);
  padding: 0 4px;
  border-radius: 4px;
}

.synthesis-content :deep(ul) {
  list-style-type: disc;
  padding-left: 1.5rem;
  margin-bottom: 1.5rem;
}

.synthesis-content :deep(li) {
  margin-bottom: 0.75rem;
}
</style>