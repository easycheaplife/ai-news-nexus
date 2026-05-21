<template>
  <div class="resonance-card bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-100 dark:border-gray-700 overflow-hidden hover:shadow-xl transition-all duration-300">
    <!-- Header with Source Badges -->
    <div class="p-4 border-b border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50">
      <div class="flex items-center justify-between mb-2">
        <div class="flex -space-x-2">
          <!-- Render icons based on platforms involved in this cluster -->
          <div v-for="platform in uniquePlatforms" :key="platform" 
               class="w-8 h-8 rounded-full flex items-center justify-center border-2 border-white dark:border-gray-800 shadow-sm z-10"
               :class="getPlatformColor(platform)">
            <span class="text-xs font-bold text-white">{{ getPlatformIcon(platform) }}</span>
          </div>
          <div v-if="cluster.news_items.length > uniquePlatforms.length" 
               class="w-8 h-8 rounded-full flex items-center justify-center border-2 border-white dark:border-gray-800 bg-gray-200 dark:bg-gray-600 text-xs font-bold text-gray-600 dark:text-gray-300 shadow-sm z-10">
            +{{ cluster.news_items.length - uniquePlatforms.length }}
          </div>
        </div>
        <div class="text-sm font-semibold text-orange-500 bg-orange-50 dark:bg-orange-900/30 px-3 py-1 rounded-full flex items-center gap-1">
          <span>🔥</span> Resonance {{ cluster.resonance_score }}
        </div>
      </div>
      <h3 class="text-xl font-bold text-gray-900 dark:text-white leading-tight mt-3">
        {{ cluster.title }}
      </h3>
      <p class="text-gray-600 dark:text-gray-300 text-sm mt-2 line-clamp-2">
        {{ cluster.summary }}
      </p>
    </div>

    <!-- Perspective View -->
    <div class="p-4 bg-[#1a1a20]/30">
      <div class="text-[10px] font-black text-text-muted uppercase tracking-widest mb-4 flex items-center gap-2">
        <div class="w-1 h-1 bg-orange-500 rounded-full"></div>
        互证视角 Perspectives
      </div>
      <div class="space-y-2">
        <div 
          v-for="item in previewItems" 
          :key="item.id" 
          @click="item.news?.url && window.open(item.news.url, '_blank')"
          class="flex gap-4 items-start group cursor-pointer p-3 rounded-xl hover:bg-white/5 border border-transparent hover:border-white/5 transition-all"
        >
          <div class="mt-1 flex-shrink-0" :class="getPlatformTextColor(item.platform_role)">
            <span class="text-sm">{{ getPlatformIcon(item.platform_role) }}</span>
          </div>
          <div class="flex-1 min-w-0">
            <h4 class="text-xs font-bold text-slate-200 truncate group-hover:text-primary transition-colors">
              {{ item.news?.title || 'Unknown Source' }}
            </h4>
            <p class="text-[10px] text-text-muted line-clamp-1 mt-1 opacity-60">
              {{ item.news?.reason || (item.news?.content ? item.news.content.substring(0, 80) : 'Click to read more...') }}
            </p>
          </div>
          <div class="flex-shrink-0">
             <div class="w-6 h-6 rounded-lg bg-white/5 flex items-center justify-center group-hover:bg-primary/20 group-hover:text-primary transition-all">
               <span class="text-[10px]">↗</span>
             </div>
          </div>
        </div>
      </div>
      
      <!-- Expand Button -->
      <button v-if="cluster.news_items.length > 3" 
              @click="emit('filter-cluster', cluster.id)"
              class="w-full mt-4 py-3 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 hover:text-white bg-white/5 hover:bg-primary/20 border border-white/5 hover:border-primary/30 rounded-xl transition-all active:scale-95">
        查看全部 {{ cluster.news_items.length }} 个来源
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface NewsItem {
  id: number;
  title: string;
  url: string;
  reason?: string;
  content?: string;
}

interface ClusterNewsMapping {
  id: number;
  news_id: number;
  platform_role: string;
  news?: NewsItem;
}

interface TopicCluster {
  id: string;
  title: string;
  summary: string;
  resonance_score: number;
  news_items: ClusterNewsMapping[];
}

const props = defineProps<{
  cluster: TopicCluster
}>();

const emit = defineEmits(['filter-cluster']);

const window = (globalThis as any).window;

// Extract unique platforms for badges
const uniquePlatforms = computed<string[]>(() => {
  if (!props.cluster.news_items) return [];
  const platforms = props.cluster.news_items.map(item => item.platform_role).filter(Boolean);
  return [...new Set(platforms)].slice(0, 3); // Max 3 unique icons
});

// Get top 3 items for preview
const previewItems = computed(() => {
  if (!props.cluster.news_items) return [];
  return props.cluster.news_items.slice(0, 3);
});

// UI Helpers
const getPlatformColor = (platform: string) => {
  const p = platform.toLowerCase();
  if (p.includes('github')) return 'bg-gray-800';
  if (p.includes('twitter')) return 'bg-blue-400';
  if (p.includes('reddit')) return 'bg-orange-500';
  if (p.includes('arxiv')) return 'bg-red-700';
  if (p.includes('hn')) return 'bg-orange-400';
  return 'bg-indigo-500';
};

const getPlatformTextColor = (platform: string) => {
  const p = platform?.toLowerCase() || '';
  if (p.includes('github')) return 'text-gray-800 dark:text-gray-300';
  if (p.includes('twitter')) return 'text-blue-400';
  if (p.includes('reddit')) return 'text-orange-500';
  if (p.includes('arxiv')) return 'text-red-700';
  if (p.includes('hn')) return 'text-orange-400';
  return 'text-indigo-500';
};

const getPlatformIcon = (platform: string) => {
  const p = platform?.toLowerCase() || '';
  if (p.includes('github')) return '🐙';
  if (p.includes('twitter')) return '🐦';
  if (p.includes('reddit')) return '👽';
  if (p.includes('arxiv')) return '📄';
  if (p.includes('hn')) return 'Y';
  return '🌐';
};
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;  
  overflow: hidden;
}
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;  
  overflow: hidden;
}
</style>
