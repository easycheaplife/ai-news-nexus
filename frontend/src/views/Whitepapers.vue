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
  <div class="min-h-screen bg-[#050505] text-slate-200 p-6 md:p-10 font-sans">
    <!-- Header -->
    <header class="max-w-5xl mx-auto mb-20 border-b border-white/5 pb-12 flex justify-between items-end">
      <div class="flex items-center gap-6">
        <button 
          @click="router.push('/app')"
          class="p-4 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all text-slate-500 hover:text-white group"
        >
          <ChevronLeft class="w-6 h-6 group-hover:-translate-x-1 transition-transform" />
        </button>
        <div>
          <h1 class="text-3xl md:text-4xl font-black text-white tracking-tighter italic uppercase">STRATEGIC <span class="text-indigo-500">DOSSIERS</span></h1>
          <p class="text-[10px] font-mono font-bold text-white/20 uppercase tracking-[0.4em] mt-2">Bi-Weekly Intelligence & Trend Synthesis</p>
        </div>
      </div>
      <div class="hidden md:block text-right">
        <p class="mono text-[9px] text-indigo-500/40 font-black tracking-widest leading-relaxed">
          SECURE_ACCESS // LEVEL_04<br>
          AUTH: AI_NEXUS_SYSTEM
        </p>
      </div>
    </header>

    <main class="max-w-5xl mx-auto">
      <div v-if="loading" class="flex flex-col items-center justify-center py-40 gap-6 opacity-30">
        <Scroll class="w-12 h-12 animate-bounce text-indigo-500" />
        <span class="text-[10px] font-mono font-black uppercase tracking-[0.5em] text-indigo-500">Synthesizing Strategic Documents...</span>
      </div>

      <div v-else-if="reports.length === 0" class="text-center py-40 border border-dashed border-white/5 rounded-[3.5rem]">
        <Calendar class="w-12 h-12 text-white/10 mx-auto mb-6" />
        <p class="text-white/20 font-mono text-xs uppercase tracking-widest">No dossiers found in archive</p>
      </div>

      <div v-else class="space-y-8">
        <div 
          v-for="report in reports" 
          :key="report.id"
          @click="openReport(report)"
          class="dossier-card group p-10 rounded-r-[2.5rem] cursor-pointer relative overflow-hidden"
        >
          <!-- Corner Fold Decoration -->
          <div class="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-indigo-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
          
          <div class="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-12">
            <div class="flex-1">
              <div class="flex items-center gap-4 mb-8">
                <span class="mono text-[10px] text-indigo-500 font-black tracking-widest uppercase">#INTEL-{{ report.id }}-ALPHA</span>
                <div class="w-12 h-[1px] bg-white/5"></div>
                <span class="mono text-[10px] text-white/20 font-bold uppercase tracking-widest">{{ report.start_date }} — {{ report.end_date }}</span>
              </div>
              
              <h2 class="text-2xl md:text-3xl font-black text-white group-hover:text-indigo-400 transition-colors leading-tight mb-6 tracking-tight">
                {{ report.title }}
              </h2>
              
              <p class="text-slate-500 text-sm line-clamp-2 leading-relaxed opacity-80 font-medium">
                {{ report.content.substring(0, 300).replace(/[#*]/g, '') }}...
              </p>
            </div>

            <div class="shrink-0 flex flex-col items-center gap-6">
               <div class="w-24 h-24 rounded-[2rem] bg-indigo-500/5 border border-indigo-500/10 flex flex-col items-center justify-center gap-1 group-hover:border-indigo-500/30 transition-all">
                  <BarChart3 class="w-6 h-6 text-indigo-500/40" />
                  <span class="text-lg font-black text-white leading-none">{{ report.stats_json?.term_count || 0 }}</span>
                  <span class="text-[8px] font-bold text-white/20 uppercase tracking-widest">Assets</span>
               </div>
               <div class="flex items-center gap-2 text-indigo-500 text-[10px] font-black uppercase tracking-widest group-hover:gap-5 transition-all">
                 Read Full Dossier <ArrowRight class="w-4 h-4" />
               </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Modal for Reading Report -->
    <transition
      enter-active-class="transition duration-500 cubic-bezier(0.16, 1, 0.3, 1)"
      enter-from-class="opacity-0 translate-y-10 scale-95"
      enter-to-class="opacity-100 translate-y-0 scale-100"
      leave-active-class="transition duration-300 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div v-if="isModalOpen" class="fixed inset-0 z-[200] bg-black/95 backdrop-blur-3xl flex items-center justify-center p-4 md:p-12" @click="closeReport">
        <div class="max-w-5xl w-full h-full bg-[#fafafa] rounded-[3.5rem] overflow-hidden flex flex-col shadow-[0_0_120px_rgba(99,102,241,0.2)]" @click.stop>
          <!-- Modal Header -->
          <div class="p-10 md:p-16 border-b border-slate-200 flex justify-between items-end bg-white">
            <div>
              <div class="flex items-center gap-3 mb-4">
                <div class="w-8 h-1 bg-indigo-600"></div>
                <span class="text-[10px] font-black text-indigo-600 uppercase tracking-[0.3em]">INTERNAL STRATEGIC DOCUMENT</span>
              </div>
              <h3 class="text-3xl md:text-4xl font-black text-slate-900 leading-tight tracking-tight">{{ selectedReport.title }}</h3>
            </div>
            <div class="text-right hidden sm:block">
               <button @click="closeReport" class="p-3 rounded-full hover:bg-slate-100 transition-colors mb-6">
                 <X class="w-8 h-8 text-slate-400" />
               </button>
               <div class="mono text-[10px] font-bold text-slate-400 tracking-widest uppercase">Issued: {{ selectedReport.date }}</div>
            </div>
          </div>

          <!-- Modal Content -->
          <div class="flex-1 overflow-y-auto p-10 md:p-20 prose prose-slate max-w-none report-reader">
            <div v-html="renderMarkdown(selectedReport.content)"></div>
          </div>

          <!-- Modal Footer -->
          <div class="p-10 border-t border-slate-100 flex justify-center bg-slate-50/80">
            <p class="text-[9px] font-bold text-slate-400 uppercase tracking-[0.5em]">AI Intelligence Nexus • Restricted Intelligence Feed • © 2026</p>
          </div>
        </div>
      </div>
    </transition>

    <!-- Background Decoration -->
    <div class="fixed inset-0 -z-10 overflow-hidden pointer-events-none opacity-20">
      <div class="absolute top-0 right-0 w-[1000px] h-[1000px] bg-indigo-500/5 rounded-full blur-[180px]"></div>
    </div>
  </div>
</template>

<style scoped>
.dossier-card {
  background: #0d0d10;
  border-left: 4px solid #6366f1;
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

.dossier-card:hover {
  background: #111116;
  border-left-width: 10px;
  transform: translateX(8px);
  box-shadow: 0 40px 80px -20px rgba(0, 0, 0, 0.9);
}

.report-reader :deep(h1) { font-weight: 900; font-size: 2.75rem; margin-bottom: 2.5rem; color: #0f172a; letter-spacing: -0.05em; border-bottom: 8px solid #6366f1; padding-bottom: 1.5rem; display: inline-block; }
.report-reader :deep(h2) { font-weight: 800; font-size: 1.75rem; margin-top: 4rem; margin-bottom: 1.5rem; color: #1e293b; position: relative; padding-left: 1.5rem; }
.report-reader :deep(h2)::before { content: ''; position: absolute; left: 0; top: 0.25rem; bottom: 0.25rem; width: 6px; background: #6366f1; border-radius: 2px; }
.report-reader :deep(h3) { font-weight: 800; margin-top: 2.5rem; color: #334155; text-transform: uppercase; letter-spacing: 0.05em; font-size: 1.1rem; }
.report-reader :deep(p) { line-height: 1.9; margin-bottom: 1.75rem; color: #475569; font-size: 1.05rem; }
.report-reader :deep(strong) { color: #4f46e5; font-weight: 800; }
.report-reader :deep(ul) { list-style-type: none; padding-left: 0; margin-bottom: 2rem; }
.report-reader :deep(li) { margin-bottom: 1rem; position: relative; padding-left: 1.5rem; color: #475569; }
.report-reader :deep(li)::before { content: '→'; position: absolute; left: 0; color: #6366f1; font-weight: 900; }
</style>
