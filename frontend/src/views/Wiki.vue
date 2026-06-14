<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { Book, Search, ChevronLeft, TrendingUp, Hash, Layers, Zap } from 'lucide-vue-next';
import { useRouter } from 'vue-router';

const apiUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
const router = useRouter();

const terms = ref<any[]>([]);
const loading = ref(true);
const searchQuery = ref('');
const selectedCategory = ref('');

const categories = ['模型', '算力', '框架', '应用', '趋势', 'general'];

const fetchTerms = async () => {
  loading.value = true;
  try {
    const response = await axios.get(`${apiUrl}/api/assets/terms`, {
      params: { limit: 200 }
    });
    terms.value = response.data;
  } catch (err) {
    console.error('Failed to fetch wiki terms', err);
  } finally {
    loading.value = false;
  }
};

const filteredTerms = computed(() => {
  return terms.value.filter(t => {
    const matchesSearch = t.keyword.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                         t.description.toLowerCase().includes(searchQuery.value.toLowerCase());
    const matchesCategory = !selectedCategory.value || t.category === selectedCategory.value;
    return matchesSearch && matchesCategory;
  });
});

onMounted(fetchTerms);

import { computed } from 'vue';
</script>

<template>
  <div class="min-h-screen bg-[#050505] text-slate-200 p-6 md:p-10">
    <!-- Header -->
    <header class="max-w-6xl mx-auto mb-12 flex flex-col md:flex-row md:items-center justify-between gap-8">
      <div class="flex items-center gap-5">
        <button 
          @click="router.push('/app')"
          class="p-3 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all text-text-muted hover:text-white"
        >
          <ChevronLeft class="w-6 h-6" />
        </button>
        <div>
          <div class="flex items-center gap-3 mb-1">
            <Book class="w-5 h-5 text-emerald-400" />
            <h1 class="text-3xl font-black text-white tracking-tight">技术百科 <span class="text-emerald-400">AI Wiki</span></h1>
          </div>
          <p class="text-xs text-text-muted font-bold uppercase tracking-widest opacity-50">Autonomous Technical Glossary & Trends</p>
        </div>
      </div>

      <div class="flex flex-1 max-w-xl gap-4">
        <div class="relative flex-1 group">
          <Search class="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted group-focus-within:text-emerald-400 transition-colors" />
          <input 
            v-model="searchQuery"
            type="text" 
            placeholder="搜索技术名词或定义..." 
            class="w-full bg-white/5 border border-white/10 rounded-2xl py-3 pl-12 pr-6 text-sm focus:outline-none focus:border-emerald-500/50 transition-all"
          >
        </div>
        <select 
          v-model="selectedCategory"
          class="bg-white/5 border border-white/10 rounded-2xl px-4 text-xs font-bold text-text-muted focus:outline-none focus:border-emerald-500/50"
        >
          <option value="">全部类别</option>
          <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
        </select>
      </div>
    </header>

    <main class="max-w-6xl mx-auto">
      <div v-if="loading" class="flex flex-col items-center justify-center py-40 gap-4 opacity-50">
        <Zap class="w-10 h-10 animate-pulse text-emerald-400" />
        <span class="text-sm font-black uppercase tracking-[0.3em] text-emerald-400">Scanning Knowledge Base...</span>
      </div>

      <div v-else-if="filteredTerms.length === 0" class="text-center py-40 border-2 border-dashed border-white/5 rounded-[3rem]">
        <Layers class="w-12 h-12 text-white/10 mx-auto mb-4" />
        <p class="text-text-muted font-bold">未找到相关词条</p>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div 
          v-for="term in filteredTerms" 
          :key="term.id"
          class="group bg-[#131316] border border-white/5 rounded-[2rem] p-8 hover:border-emerald-500/30 transition-all duration-500 relative overflow-hidden"
        >
          <!-- Background Glow -->
          <div class="absolute -top-24 -right-24 w-48 h-48 bg-emerald-500/5 blur-[60px] group-hover:bg-emerald-500/10 transition-all"></div>
          
          <div class="relative z-10">
            <div class="flex justify-between items-start mb-6">
              <div class="px-3 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                <span class="text-[10px] font-black text-emerald-400 uppercase tracking-widest">{{ term.category }}</span>
              </div>
              <div class="flex items-center gap-1.5 text-emerald-400/40 group-hover:text-emerald-400 transition-colors">
                <TrendingUp class="w-3.5 h-3.5" />
                <span class="text-xs font-black">{{ term.heat_score }}</span>
              </div>
            </div>

            <h3 class="text-xl font-black text-white mb-4 group-hover:text-emerald-400 transition-colors tracking-tight">
              {{ term.keyword }}
            </h3>
            
            <p class="text-sm text-slate-400 leading-relaxed mb-8 line-clamp-4 group-hover:line-clamp-none transition-all">
              {{ term.description }}
            </p>

            <div class="pt-6 border-t border-white/5 flex items-center justify-between">
              <span class="text-[9px] font-bold text-white/20 uppercase tracking-widest">
                Last updated: {{ new Date(term.updated_at).toLocaleDateString() }}
              </span>
              <Hash class="w-3 h-3 text-white/10" />
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Background Decoration -->
    <div class="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      <div class="absolute top-0 right-0 w-[800px] h-[800px] bg-emerald-500/5 rounded-full blur-[150px] opacity-30"></div>
      <div class="absolute bottom-0 left-0 w-[600px] h-[600px] bg-emerald-600/5 rounded-full blur-[130px] opacity-20"></div>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-4 {
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;  
  overflow: hidden;
}
</style>
