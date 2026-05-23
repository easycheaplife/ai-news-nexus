<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { Calendar, Download, Eye, ChevronLeft, RefreshCw, X, FileImage } from 'lucide-vue-next';
import { useRouter } from 'vue-router';

const apiUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
const router = useRouter();

const reports = ref<any[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

const fetchReports = async () => {
  loading.value = true;
  try {
    const response = await axios.get(`${apiUrl}/api/insights/`);
    // 仅显示有报表链接的记录
    reports.value = response.data.filter((i: any) => i.report_url);
    error.value = null;
  } catch (err) {
    console.error('Failed to fetch reports list', err);
    error.value = '无法从云端加载日报列表。';
  } finally {
    loading.value = false;
  }
};

const getReportUrl = (url: string) => {
  if (url.startsWith('http')) return url;
  return `${apiUrl}${url}`;
};

const downloadReport = (report: any) => {
  const url = getReportUrl(report.report_url);
  const filename = `AI-Daily-${report.date}.png`;
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// 预览状态
const preview = ref<{ isOpen: boolean; url: string; title: string }>({
  isOpen: false,
  url: '',
  title: ''
});

const openPreview = (report: any) => {
  preview.value = {
    isOpen: true,
    url: getReportUrl(report.report_url),
    title: report.date
  };
  document.body.style.overflow = 'hidden';
};

const closePreview = () => {
  preview.value.isOpen = false;
  document.body.style.overflow = 'auto';
};

onMounted(fetchReports);
</script>

<template>
  <div class="min-h-screen bg-[#0a0a0c] text-slate-200 p-6 md:p-10">
    <!-- Header -->
    <header class="max-w-6xl mx-auto mb-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
      <div class="flex items-center gap-4">
        <button 
          @click="router.push('/')"
          class="p-2.5 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all text-text-muted hover:text-white"
        >
          <ChevronLeft class="w-6 h-6" />
        </button>
        <div>
          <h1 class="text-3xl font-black text-white tracking-tight flex items-center gap-3">
            历史日报 <span class="text-primary">Reports</span>
          </h1>
          <p class="text-xs text-text-muted font-bold uppercase tracking-widest mt-1 opacity-50">Archived Intelligence Digests</p>
        </div>
      </div>

      <button 
        @click="fetchReports"
        class="flex items-center gap-2 px-6 py-3 bg-primary/10 hover:bg-primary/20 border border-primary/20 rounded-2xl text-sm font-bold text-primary transition-all active:scale-95"
      >
        <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loading }" />
        刷新列表
      </button>
    </header>

    <!-- Content -->
    <main class="max-w-6xl mx-auto">
      <!-- Loading -->
      <div v-if="loading && !reports.length" class="flex flex-col items-center justify-center py-40 gap-4 opacity-50">
        <RefreshCw class="w-10 h-10 animate-spin text-primary" />
        <span class="text-sm font-bold uppercase tracking-widest">正在检索归档...</span>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="bg-red-500/10 border border-red-500/20 p-8 rounded-3xl text-center">
        <p class="text-red-400 font-bold mb-4">{{ error }}</p>
        <button @click="fetchReports" class="text-xs font-black uppercase tracking-widest underline decoration-2 underline-offset-4">重试一次</button>
      </div>

      <!-- Empty -->
      <div v-else-if="!reports.length" class="flex flex-col items-center justify-center py-40 gap-6 border-2 border-dashed border-white/5 rounded-[3rem]">
        <div class="p-6 rounded-full bg-white/5">
          <Calendar class="w-12 h-12 text-white/20" />
        </div>
        <div class="text-center">
          <h3 class="text-xl font-bold text-white mb-2">暂无生成记录</h3>
          <p class="text-text-muted text-sm max-w-xs mx-auto">系统每天早晨会自动生成当天的日报。如果还没有看到，请稍后再试或检查采集器状态。</p>
        </div>
      </div>

      <!-- Grid -->
      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div 
          v-for="report in reports" 
          :key="report.id"
          class="group bg-[#131316] border border-white/5 rounded-3xl p-6 hover:border-primary/50 transition-all hover:shadow-2xl hover:shadow-primary/10 relative overflow-hidden"
        >
          <div class="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
            <FileImage class="w-20 h-20" />
          </div>
          
          <div class="relative z-10">
            <div class="flex items-center gap-3 mb-6">
              <div class="p-3 rounded-2xl bg-white/5 text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                <Calendar class="w-6 h-6" />
              </div>
              <div>
                <span class="text-[10px] font-black text-text-muted uppercase tracking-[0.2em] block">Daily Report</span>
                <span class="text-xl font-bold text-white tracking-tight">{{ report.date }}</span>
              </div>
            </div>

            <div class="flex gap-2">
              <button 
                @click="openPreview(report)"
                class="flex-1 flex items-center justify-center gap-2 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-xs font-bold transition-all"
              >
                <Eye class="w-4 h-4" />
                预览图片
              </button>
              <button 
                @click="downloadReport(report)"
                class="w-12 flex items-center justify-center bg-primary/10 hover:bg-primary text-primary hover:text-white rounded-xl transition-all active:scale-90"
                title="直接下载"
              >
                <Download class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Preview Modal (Lightbox) -->
    <transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div v-if="preview.isOpen" class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/95 backdrop-blur-xl" @click="closePreview">
        <button 
          class="absolute top-6 right-8 text-white/50 hover:text-white transition-all p-2 z-[110] hover:rotate-90"
        >
          <X class="w-10 h-10" /> 
        </button>
        
        <div class="relative max-w-4xl w-full max-h-[90vh] flex flex-col items-center gap-6" @click.stop>
          <div class="w-full h-full rounded-3xl overflow-y-auto no-scrollbar shadow-2xl border border-white/10 bg-white">
            <img 
              :src="preview.url" 
              class="w-full h-auto block" 
              :alt="preview.title"
            />
          </div>
          <div class="flex items-center gap-4 w-full">
            <h2 class="text-xl font-bold text-white flex-1">{{ preview.title }} · Daily Intelligence</h2>
            <button 
              @click="downloadReport(preview.title + '.png')"
              class="flex items-center gap-2 px-6 py-3 bg-primary rounded-2xl text-sm font-bold text-white shadow-xl shadow-primary/30 active:scale-95 transition-all"
            >
              <Download class="w-4 h-4" />
              下载此日报
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Background Decoration -->
    <div class="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      <div class="absolute top-0 right-0 w-[800px] h-[800px] bg-primary/5 rounded-full blur-[150px] opacity-30"></div>
      <div class="absolute bottom-0 left-0 w-[600px] h-[600px] bg-indigo-600/5 rounded-full blur-[130px] opacity-20"></div>
    </div>
  </div>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
