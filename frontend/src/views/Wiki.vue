<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';
import { Search, ChevronLeft, TrendingUp, Layers, Zap } from 'lucide-vue-next';
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
</script>

<template>
  <div class="min-h-screen bg-[#050505] text-slate-200 p-6 md:p-10 font-sans">
    <!-- Header -->
    <header class="max-w-7xl mx-auto mb-16 flex flex-col md:flex-row md:items-end justify-between gap-8 border-b border-white/5 pb-10">
      <div class="flex items-center gap-6">
        <button 
          @click="router.push('/app')"
          class="p-4 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all text-slate-500 hover:text-white group"
        >
          <ChevronLeft class="w-6 h-6 group-hover:-translate-x-1 transition-transform" />
        </button>
        <div>
          <div class="flex items-center gap-4 mb-2">
            <div class="w-1.5 h-8 bg-indigo-500 rounded-full"></div>
            <h1 class="text-3xl md:text-4xl font-black text-white tracking-tighter italic">技术百科 <span class="text-indigo-500/80">AI WIKI</span></h1>
          </div>
          <p class="text-[10px] font-mono font-bold text-white/20 uppercase tracking-[0.4em]">Strategic Technical Asset Indexing // V2.0</p>
        </div>
      </div>

      <div class="flex flex-1 max-w-2xl gap-4">
        <div class="relative flex-1 group">
          <Search class="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20 group-focus-within:text-indigo-400 transition-colors" />
          <input 
            v-model="searchQuery"
            type="text" 
            placeholder="搜索技术名词、架构或定义..." 
            class="w-full bg-white/[0.03] border border-white/10 rounded-2xl py-4 pl-12 pr-6 text-sm focus:outline-none focus:border-indigo-500/50 transition-all placeholder:text-white/10"
          >
        </div>
        <select 
          v-model="selectedCategory"
          class="bg-white/[0.03] border border-white/10 rounded-2xl px-6 text-xs font-black text-white/40 uppercase tracking-widest focus:outline-none focus:border-indigo-500/50 cursor-pointer"
        >
          <option value="">全部类别</option>
          <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
        </select>
      </div>
    </header>

    <main class="max-w-7xl mx-auto">
      <div v-if="loading" class="flex flex-col items-center justify-center py-40 gap-6 opacity-30">
        <Zap class="w-12 h-12 animate-pulse text-indigo-500" />
        <span class="text-[10px] font-mono font-black uppercase tracking-[0.5em] text-indigo-500">Initializing Knowledge Grid...</span>
      </div>

      <div v-else-if="filteredTerms.length === 0" class="text-center py-40 border border-dashed border-white/5 rounded-[3rem]">
        <Layers class="w-12 h-12 text-white/10 mx-auto mb-6" />
        <p class="text-white/20 font-mono text-xs uppercase tracking-widest">No matching assets found in database</p>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        <div 
          v-for="term in filteredTerms" 
          :key="term.id"
          class="term-card group p-10 rounded-[2.5rem] relative overflow-hidden flex flex-col"
        >
          <!-- Background Decoration -->
          <div class="absolute -top-16 -right-16 w-32 h-32 bg-indigo-500/5 rounded-full blur-3xl group-hover:bg-indigo-500/10 transition-all"></div>
          
          <div class="relative z-10 flex-1">
            <div class="flex justify-between items-center mb-10">
              <div class="px-3 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/20">
                <span class="text-[10px] font-black text-indigo-400 uppercase tracking-widest">{{ term.category }}</span>
              </div>
              <div class="glow-dot" :class="term.heat_score > 90 ? 'active' : 'idle'"></div>
            </div>

            <h3 class="text-2xl font-black text-white mb-6 group-hover:text-indigo-400 transition-colors tracking-tight leading-tight">
              {{ term.keyword }}
            </h3>
            
            <p class="text-sm text-slate-400 leading-relaxed mb-10 opacity-70 line-clamp-4 group-hover:line-clamp-none transition-all duration-500">
              {{ term.description }}
            </p>
          </div>

          <!-- Card Footer -->
          <div class="relative z-10 pt-8 border-t border-white/5 flex items-center justify-between">
            <div class="flex flex-col">
              <span class="text-[8px] font-mono font-black text-white/20 uppercase tracking-widest mb-1">Resonance Score</span>
              <div class="flex items-center gap-2">
                <TrendingUp class="w-3 h-3 text-indigo-500/50" />
                <span class="text-sm font-black text-indigo-400 font-mono">{{ term.heat_score }}%</span>
              </div>
            </div>
            <div class="flex gap-1">
              <div class="w-1 h-4 bg-indigo-500" :style="{ opacity: term.heat_score / 100 }"></div>
              <div class="w-1 h-4 bg-indigo-500" :style="{ opacity: (term.heat_score - 20) / 100 }"></div>
              <div class="w-1 h-4 bg-indigo-500" :style="{ opacity: (term.heat_score - 40) / 100 }"></div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Background Decoration -->
    <div class="fixed inset-0 -z-10 overflow-hidden pointer-events-none opacity-20">
      <div class="absolute top-0 right-0 w-[1000px] h-[1000px] bg-indigo-600/5 rounded-full blur-[150px]"></div>
      <div class="absolute bottom-0 left-0 w-[800px] h-[800px] bg-indigo-900/5 rounded-full blur-[130px]"></div>
    </div>
  </div>
</template>

<style scoped>
.term-card {
  background: #0d0d10;
  border: 1px solid rgba(255, 255, 255, 0.03);
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

.term-card:hover {
  background: #121218;
  border-color: rgba(99, 102, 241, 0.4);
  transform: translateY(-8px);
  box-shadow: 0 30px 60px -20px rgba(0, 0, 0, 0.8), 0 0 20px rgba(99, 102, 241, 0.05);
}

.glow-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  position: relative;
}

.glow-dot.active {
  background: #6366f1;
  box-shadow: 0 0 15px #6366f1;
}

.glow-dot.active::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 1px solid #6366f1;
  animation: pulse 2s cubic-bezier(0, 0, 0.2, 1) infinite;
}

.glow-dot.idle {
  background: rgba(255, 255, 255, 0.1);
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  100% { transform: scale(3); opacity: 0; }
}

.line-clamp-4 {
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;  
  overflow: hidden;
}
</style>
