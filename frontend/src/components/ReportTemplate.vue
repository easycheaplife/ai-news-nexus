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
const totalCount = ref(0);
const latestInsight = ref<any>(null);
const loading = ref(true);
const ready = ref(false);
const styleVariant = ref(1); // 1: Classic Dark, 2: Modern Gradient

const renderMarkdown = (text: string) => {
  if (!text) return '';
  
  // 🩹 鲁棒性增强：仅移除多余的元数据行（撰写人、日期等）
  // 移除了破坏 Markdown 标题语法的正则，让 marked 正常工作
  const cleanedText = text
    .replace(/^.*撰写人[:：].*$/gm, '')
    .replace(/^.*日期[:：].*$/gm, '')
    .replace(/^.*报告人[:：].*$/gm, '')
    .replace(/^.*撰写日期[:：].*$/gm, '');

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
    
    // 随机选择风格
    styleVariant.value = Math.random() > 0.5 ? 1 : 2;

    const [newsRes, insightRes] = await Promise.all([
      axios.get(`${base}/api/news/`, { 
        params: { 
          limit: 20, 
          min_score: 71, 
          include_pending: false,
          _t: timestamp 
        } 
      }),
      axios.get(`${base}/api/insights/${today}`, { params: { _t: timestamp } }).catch(() => 
        axios.get(`${base}/api/insights/latest`, { params: { _t: timestamp } }).catch(() => ({ data: null }))
      )
    ]);
    
    // 适配新的 API 结构 { items: [], total: 123 }
    if (newsRes.data && typeof newsRes.data === 'object' && 'items' in newsRes.data) {
      news.value = newsRes.data.items || [];
      totalCount.value = newsRes.data.total || 0;
    } else {
      news.value = newsRes.data || [];
      totalCount.value = news.value.length;
    }
    
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
  <div :class="{ 'opacity-100': !loading, 'opacity-0': loading }" class="min-h-screen bg-[#f0f2f5] md:p-10 p-4 transition-opacity duration-500">
    <div id="report-content" class="max-w-[800px] mx-auto bg-white md:rounded-3xl rounded-xl shadow-2xl overflow-hidden border border-slate-200">
      <!-- Header -->
      <div :class="[
        'md:p-10 p-6 text-white relative overflow-hidden transition-all duration-700',
        styleVariant === 1 ? 'bg-gradient-to-br from-[#1a1a20] to-[#0a0a0c]' : 'bg-gradient-to-br from-indigo-600 via-primary to-blue-700'
      ]">
        <div class="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-[100px] -mr-32 -mt-32"></div>
        <div class="relative z-10">
          <div class="flex items-center gap-4 mb-6">
            <div :class="[
              'p-3 rounded-2xl shadow-lg transition-all',
              styleVariant === 1 ? 'bg-primary shadow-primary/30' : 'bg-white shadow-white/20'
            ]">
              <Zap :class="['md:w-8 md:h-8 w-6 h-6', styleVariant === 1 ? 'text-white' : 'text-primary']" />
            </div>
            <div>
              <h1 class="md:text-3xl text-2xl font-black tracking-tighter uppercase leading-tight">AI NEWS <span :class="styleVariant === 1 ? 'text-primary' : 'text-white/80'">DAILY</span></h1>
              <p :class="['text-[10px] font-bold tracking-[0.3em] uppercase', styleVariant === 1 ? 'text-slate-400' : 'text-white/60']">Global Intelligence Report</p>
            </div>
          </div>
          <div class="flex justify-between items-end border-t border-white/10 pt-6">
            <div class="md:text-2xl text-xl font-bold">{{ format(new Date(), 'yyyy年MM月dd日', { locale: zhCN }) }}</div>
            <div :class="['font-bold uppercase tracking-widest text-xs', styleVariant === 1 ? 'text-slate-400' : 'text-white/70']">{{ format(new Date(), 'EEEE', { locale: zhCN }) }}</div>
          </div>
        </div>
      </div>

      <!-- Global Intelligence Synthesis -->
      <div v-if="latestInsight && latestInsight.content" class="md:p-12 p-6 md:pb-16 pb-10">
        <div class="bg-white relative">
          <div class="absolute -top-6 right-0 opacity-10 hidden md:block">
            <Quote class="w-24 h-24 text-slate-400" />
          </div>
          <div :class="[
            'flex items-center gap-3 mb-10 border-b-2 pb-6',
            styleVariant === 1 ? 'border-primary/10' : 'border-indigo-100'
          ]">
            <Target :class="['w-7 h-7 shrink-0', styleVariant === 1 ? 'text-primary' : 'text-indigo-600']" />
            <h2 class="md:text-xl text-lg font-black uppercase tracking-[0.2em] text-slate-900 leading-tight">深度战略综述 · Strategic Synthesis</h2>
          </div>
          
          <div class="synthesis-content" v-html="renderMarkdown(latestInsight.content)"></div>
        </div>
      </div>

      <!-- Intelligence Dashboard -->
      <div class="md:p-12 p-6 pt-0">
        <div class="grid md:grid-cols-3 grid-cols-1 gap-6 border-t border-slate-100 pt-10">
          <div :class="['rounded-2xl p-5 border transition-all', styleVariant === 1 ? 'bg-slate-50 border-slate-100' : 'bg-indigo-50/30 border-indigo-100']">
            <div class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Intelligence Count</div>
            <div :class="['text-3xl font-black', styleVariant === 1 ? 'text-primary' : 'text-indigo-600']">{{ totalCount || latestInsight?.stats_json?.Total || news.length }}+</div>
            <div class="text-[11px] text-slate-400 font-bold mt-1">Processed globally</div>
          </div>
          <div :class="['rounded-2xl p-5 border transition-all', styleVariant === 1 ? 'bg-slate-50 border-slate-100' : 'bg-indigo-50/30 border-indigo-100']">
            <div class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Trending Tech</div>
            <div class="flex flex-wrap gap-1.5 mt-1">
              <span v-for="kw in (latestInsight?.hot_topics?.slice(0, 3) || ['LLM', 'Agent', 'Multimodal'])" :key="kw" 
                    :class="['text-[10px] font-bold px-2 py-0.5 rounded border uppercase', 
                             styleVariant === 1 ? 'bg-white text-primary border-primary/20' : 'bg-white text-indigo-600 border-indigo-200 shadow-sm']">
                {{ kw }}
              </span>
            </div>
          </div>
          <div :class="['rounded-2xl p-5 border transition-all', styleVariant === 1 ? 'bg-slate-50 border-slate-100' : 'bg-indigo-50/30 border-indigo-100']">
            <div class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Pulse Status</div>
            <div class="flex items-center gap-2 mt-1">
              <div :class="['w-2.5 h-2.5 rounded-full animate-pulse', styleVariant === 1 ? 'bg-green-500' : 'bg-indigo-500']"></div>
              <span class="text-[11px] font-black text-slate-700 uppercase">System OK</span>
            </div>
            <div class="text-[11px] text-slate-400 font-bold mt-1">AI Node: Active</div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="bg-slate-50 md:p-12 p-8 border-t border-slate-100 flex md:flex-row flex-col gap-10 justify-between items-center text-center md:text-left">
        <div class="flex flex-col gap-3">
          <div class="flex items-center gap-2 justify-center md:justify-start">
            <div class="w-2.5 h-2.5 rounded-full bg-primary"></div>
            <span class="text-[12px] font-black text-slate-500 uppercase tracking-widest">AI News Nexus Synthesis</span>
          </div>
          <div class="text-[11px] font-bold text-slate-300 uppercase tracking-[0.2em]">Generated at {{ format(new Date(), 'HH:mm') }}</div>
        </div>
        
        <div class="flex items-center gap-6 md:border-l border-slate-200 md:pl-10">
          <div class="flex flex-col md:items-end items-center">
            <div class="text-[12px] font-black text-slate-900 uppercase tracking-wider mb-1">Explore Full Intelligence</div>
            <div class="text-[10px] font-bold text-primary tracking-tight px-2 py-0.5 bg-primary/5 rounded">ai-news-nexus.netlify.app</div>
          </div>
          <div class="bg-white p-2.5 rounded-2xl shadow-md border border-slate-100 shrink-0">
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=80x80&data=https://ai-news-nexus.netlify.app/&bgcolor=ffffff&color=000000&margin=0" 
                 alt="QR Code" 
                 class="w-14 h-14" />
          </div>
        </div>
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
