<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import axios from 'axios';
import { Search, RefreshCw, Zap } from 'lucide-vue-next';
import NewsCard from './components/NewsCard.vue';

const news = ref<any[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

const filters = ref({
  platform: '',
  query: '',
  limit: 50
});

const platforms = [
  { label: 'All Platforms', value: '' },
  { label: 'Twitter (X)', value: 'twitter' },
  { label: 'YouTube', value: 'youtube' },
  { label: 'Reddit', value: 'reddit' },
  { label: 'Product Hunt', value: 'ph' },
  { label: 'Hacker News', value: 'hn' },
];

const fetchNews = async () => {
  loading.value = true;
  try {
    const params = {
      platform: filters.value.platform || undefined,
      query: filters.value.query || undefined,
      limit: filters.value.limit
    };
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const response = await axios.get(`${apiUrl}/news/`, { params });
    news.value = response.data;
    error.value = null;
  } catch (err: any) {
    error.value = 'Failed to connect to the news engine.';
    console.error(err);
  } finally {
    loading.value = false;
  }
};

onMounted(fetchNews);

watch(() => filters.value.platform, fetchNews);

let searchTimeout: any;
const handleSearch = () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(fetchNews, 500);
};
</script>

<template>
  <div class="min-h-screen">
    <!-- Header -->
    <header class="sticky top-0 z-50 glass-card border-x-0 border-t-0 py-4 px-6 mb-8">
      <div class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
        <div class="flex items-center gap-3">
          <div class="bg-primary p-2 rounded-xl shadow-lg shadow-primary/20">
            <Zap class="w-6 h-6 text-white" />
          </div>
          <h1 class="text-2xl font-bold tracking-tight">
            AI NEWS <span class="text-gradient">NEXUS</span>
          </h1>
        </div>

        <div class="flex flex-1 max-w-2xl w-full items-center gap-4">
          <div class="relative flex-1">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
            <input 
              v-model="filters.query"
              @input="handleSearch"
              type="text" 
              placeholder="Search AI trends, models, research..." 
              class="w-full bg-white/5 border border-white/10 rounded-full py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
            >
          </div>
          
          <select 
            v-model="filters.platform"
            class="bg-white/5 border border-white/10 rounded-full py-2.5 px-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all appearance-none cursor-pointer"
          >
            <option v-for="p in platforms" :key="p.value" :value="p.value" class="bg-surface">
              {{ p.label }}
            </option>
          </select>

          <button 
            @click="fetchNews"
            class="p-2.5 rounded-full hover:bg-white/5 transition-colors border border-white/10"
            title="Refresh"
          >
            <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loading }" />
          </button>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-6 pb-20">
      <!-- Welcome Message -->
      <div v-if="!news.length && !loading" class="text-center py-20 animate-fade-in">
        <h2 class="text-xl text-text-secondary mb-4">No transmissions found.</h2>
        <p class="text-text-muted">Adjust your filters or check back later for the latest AI intel.</p>
      </div>

      <!-- Loading State -->
      <div v-if="loading && !news.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
        <div v-for="i in 6" :key="i" class="h-64 bg-white/5 rounded-2xl border border-white/10"></div>
      </div>

      <!-- News Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <NewsCard 
          v-for="item in news" 
          :key="item.id" 
          :item="item" 
        />
      </div>
    </main>

    <!-- Background Decoration -->
    <div class="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      <div class="absolute top-[20%] -left-20 w-[500px] h-[500px] bg-primary/10 rounded-full blur-[120px]"></div>
      <div class="absolute bottom-[10%] -right-20 w-[400px] h-[400px] bg-secondary/10 rounded-full blur-[100px]"></div>
    </div>
  </div>
</template>
