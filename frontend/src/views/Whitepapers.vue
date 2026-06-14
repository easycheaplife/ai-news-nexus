<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { Scroll, ChevronLeft, X, Calendar, BarChart3, ArrowRight } from 'lucide-vue-next';
import { useRouter } from 'vue-router';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

const apiUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
const router = useRouter();

const reports = ref<any[]>([]);
const loading = ref(true);
const selectedReport = ref<any>(null);
const isModalOpen = ref(false);

const fetchReports = async () => {
  loading.value = true;
  try {
    const response = await axios.get(`${apiUrl}/api/assets/reports`, {
      params: { limit: 20 }
    });
    reports.value = response.data;
  } catch (err) {
    console.error('Failed to fetch periodic reports', err);
  } finally {
    loading.value = false;
  }
};

const renderMarkdown = (text: string) => {
  if (!text) return '';
  const html = marked.parse(text, { gfm: true, breaks: true });
  return DOMPurify.sanitize(html as string);
};

const openReport = (report: any) => {
  selectedReport.value = report;
  isModalOpen.value = true;
  document.body.style.overflow = 'hidden';
};

const closeReport = () => {
  isModalOpen.value = false;
  document.body.style.overflow = 'auto';
};

onMounted(fetchReports);
</script>

<template>
  <div class="min-h-screen bg-[#050505] text-slate-200 p-6 md:p-10">
    <!-- Header -->
    <header class="max-w-5xl mx-auto mb-16 flex items-center gap-6">
      <button 
        @click="router.push('/app')"
        class="p-3 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all text-text-muted hover:text-white"
      >
        <ChevronLeft class="w-6 h-6" />
      </button>
      <div>
        <div class="flex items-center gap-3 mb-1">
          <Scroll class="w-6 h-6 text-amber-400" />
          <h1 class="text-3xl font-black text-white tracking-tight">深度战略白皮书 <span class="text-amber-400">Whitepapers</span></h1>
        </div>
        <p class="text-xs text-text-muted font-bold uppercase tracking-widest opacity-50">Bi-Weekly Intelligence & Trend Analysis</p>
      </div>
    </header>

    <main class="max-w-5xl mx-auto">
      <div v-if="loading" class="flex flex-col items-center justify-center py-40 gap-4 opacity-50">
        <Scroll class="w-10 h-10 animate-bounce text-amber-400" />
        <span class="text-sm font-black uppercase tracking-[0.3em] text-amber-400">Synthesizing Reports...</span>
      </div>

      <div v-else-if="reports.length === 0" class="text-center py-40 border-2 border-dashed border-white/5 rounded-[3rem]">
        <Calendar class="w-12 h-12 text-white/10 mx-auto mb-4" />
        <p class="text-text-muted font-bold">暂无已生成的白皮书，请等待系统自动产出</p>
      </div>

      <div v-else class="grid grid-cols-1 gap-8">
        <div 
          v-for="report in reports" 
          :key="report.id"
          @click="openReport(report)"
          class="group relative bg-[#0d0d0f] border border-white/5 rounded-[2.5rem] p-10 cursor-pointer hover:border-amber-500/30 transition-all duration-500 overflow-hidden"
        >
          <!-- Accent Decoration -->
          <div class="absolute top-0 left-0 w-2 h-full bg-amber-500/20 group-hover:bg-amber-500 transition-colors"></div>
          <div class="absolute top-0 right-0 w-64 h-64 bg-amber-500/5 rounded-full blur-[80px] -mr-32 -mt-32"></div>

          <div class="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-10">
            <div class="flex-1">
              <div class="flex items-center gap-4 mb-6">
                <div class="px-3 py-1 rounded-lg bg-amber-500/10 border border-amber-500/20 text-[10px] font-black text-amber-400 uppercase tracking-widest">
                  Strategic Edition
                </div>
                <span class="text-xs font-mono text-white/20">{{ report.start_date }} — {{ report.end_date }}</span>
              </div>
              
              <h2 class="text-2xl md:text-3xl font-black text-white group-hover:text-amber-400 transition-colors leading-tight mb-4">
                {{ report.title }}
              </h2>
              
              <p class="text-slate-400 text-sm line-clamp-2 leading-relaxed opacity-60">
                {{ report.content.substring(0, 300).replace(/[#*]/g, '') }}...
              </p>
            </div>

            <div class="shrink-0 flex flex-col items-center gap-4">
               <div class="w-20 h-20 rounded-3xl bg-white/5 border border-white/5 flex flex-col items-center justify-center gap-1">
                  <BarChart3 class="w-5 h-5 text-amber-400/50" />
                  <span class="text-xs font-black text-white">{{ report.stats_json?.term_count || 0 }}</span>
                  <span class="text-[8px] font-bold text-white/20 uppercase">Assets</span>
               </div>
               <div class="flex items-center gap-2 text-amber-400 text-xs font-black uppercase tracking-widest group-hover:gap-4 transition-all">
                 阅读全文 <ArrowRight class="w-4 h-4" />
               </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Modal for Reading Report -->
    <transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div v-if="isModalOpen" class="fixed inset-0 z-[200] bg-black/95 backdrop-blur-2xl flex items-center justify-center p-4 md:p-10" @click="closeReport">
        <button class="absolute top-8 right-8 text-white/40 hover:text-white transition-all hover:rotate-90 p-2">
          <X class="w-10 h-10" />
        </button>

        <div class="max-w-4xl w-full h-full bg-white rounded-[3rem] overflow-hidden flex flex-col shadow-[0_0_100px_rgba(251,191,36,0.2)]" @click.stop>
          <!-- Modal Header -->
          <div class="p-8 md:p-12 border-b border-slate-100 flex justify-between items-end">
            <div>
              <span class="text-[10px] font-black text-amber-600 uppercase tracking-widest block mb-2">Internal Strategic Document</span>
              <h3 class="text-2xl md:text-3xl font-black text-slate-900 leading-tight">{{ selectedReport.title }}</h3>
            </div>
            <div class="text-right hidden sm:block">
              <span class="text-xs font-bold text-slate-400">{{ selectedReport.date }}</span>
            </div>
          </div>

          <!-- Modal Content (Scrollable) -->
          <div class="flex-1 overflow-y-auto p-8 md:p-16 prose prose-slate max-w-none report-reader">
            <div v-html="renderMarkdown(selectedReport.content)"></div>
          </div>

          <!-- Modal Footer -->
          <div class="p-8 border-t border-slate-100 flex justify-center bg-slate-50/50">
            <p class="text-[10px] font-bold text-slate-400 uppercase tracking-[0.3em]">AI Intelligence Nexus • Confidential Intelligence</p>
          </div>
        </div>
      </div>
    </transition>

    <!-- Background Decoration -->
    <div class="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      <div class="absolute top-0 right-0 w-[800px] h-[800px] bg-amber-500/5 rounded-full blur-[150px] opacity-30"></div>
    </div>
  </div>
</template>

<style scoped>
.report-reader :deep(h1) { font-weight: 900; font-size: 2.25rem; margin-bottom: 2rem; border-bottom: 4px solid #f59e0b; padding-bottom: 1rem; color: #0f172a; }
.report-reader :deep(h2) { font-weight: 800; font-size: 1.5rem; margin-top: 3rem; margin-bottom: 1.5rem; color: #1e293b; background: #fef3c7; padding: 0.5rem 1rem; border-radius: 0.5rem; }
.report-reader :deep(h3) { font-weight: 700; margin-top: 2rem; color: #334155; }
.report-reader :deep(p) { line-height: 1.8; margin-bottom: 1.5rem; color: #475569; }
.report-reader :deep(strong) { color: #f59e0b; }
.report-reader :deep(ul) { list-style-type: disc; padding-left: 2rem; margin-bottom: 1.5rem; }
.report-reader :deep(li) { margin-bottom: 0.75rem; }
</style>
