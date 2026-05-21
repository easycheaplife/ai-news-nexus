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
    <div class="p-4 bg-white dark:bg-gray-800">
      <div class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Perspectives</div>
      <div class="space-y-3">
        <div v-for="item in previewItems" :key="item.id" class="flex gap-3 items-start group cursor-pointer p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
          <div class="mt-1 flex-shrink-0" :class="getPlatformTextColor(item.platform_role)">
            {{ getPlatformIcon(item.platform_role) }}
          </div>
          <div class="flex-1 min-w-0">
            <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate group-hover:text-blue-600 transition-colors">
              {{ item.news?.title || 'Unknown Source' }}
            </h4>
            <p class="text-xs text-gray-500 dark:text-gray-400 line-clamp-1 mt-0.5">
              {{ item.news?.reason || item.news?.content?.substring(0, 80) || 'Click to read more...' }}
            </p>
          </div>
          <div class="flex-shrink-0 text-xs text-gray-400">
             <a :href="item.news?.url" target="_blank" class="hover:text-blue-500" @click.stop>↗</a>
          </div>
        </div>
      </div>
      
      <!-- Expand Button -->
      <button v-if="cluster.news_items.length > 3" 
              class="w-full mt-4 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors">
        View all {{ cluster.news_items.length }} sources
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
