<template>
  <div class="resonance-card group relative bg-[#131316] hover:bg-[#18181c] rounded-[2rem] border border-white/5 hover:border-primary/30 transition-all duration-500 overflow-hidden shadow-2xl shadow-primary/5">
    <!-- Top Progress Bar Decoration -->
    <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-orange-500/50 to-primary/50 opacity-30 group-hover:opacity-100 transition-opacity"></div>
    
    <!-- 🏅 First Mover Badge -->
    <div v-if="cluster.first_mover_news" 
         class="absolute top-4 right-4 z-20"
         :title="`首发情报源: @${cluster.first_mover_news.metadata_json?.author || 'Unknown'}`">
      <div :class="[
        'flex items-center gap-1.5 px-3 py-1 rounded-lg border text-[9px] font-black uppercase tracking-tighter shadow-lg backdrop-blur-md',
        cluster.first_mover_tier === 'S' ? 'bg-amber-500/10 border-amber-500/30 text-amber-500 shadow-amber-500/10' :
        cluster.first_mover_tier === 'A' ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-500 shadow-indigo-500/10' :
        'bg-slate-500/10 border-slate-500/30 text-slate-400 shadow-slate-500/10'
      ]">
        <span class="text-xs">{{ cluster.first_mover_tier === 'S' ? '🏆' : cluster.first_mover_tier === 'A' ? '💎' : '⏱️' }}</span>
        <span>{{ getTierLabel(cluster.first_mover_tier) }}</span>
      </div>
    </div>

    <!-- Header with Source Badges -->
    <div class="p-6 pb-4">
      <div class="flex items-center justify-between mb-4">
        <div class="flex -space-x-3">
          <!-- Render icons based on platforms involved in this cluster -->
          <div v-for="platform in uniquePlatforms" :key="platform" 
               class="w-9 h-9 rounded-full flex items-center justify-center border-2 border-[#131316] shadow-2xl z-10 transition-transform group-hover:translate-x-1"
               :class="getPlatformColor(platform)">
            <span class="text-sm font-bold text-white">{{ getPlatformIcon(platform) }}</span>
          </div>
          <div v-if="cluster.news_items.length > uniquePlatforms.length" 
               class="w-9 h-9 rounded-full flex items-center justify-center border-2 border-[#131316] bg-slate-800 text-[10px] font-black text-slate-400 shadow-2xl z-10">
            +{{ cluster.news_items.length - uniquePlatforms.length }}
          </div>
        </div>
        
        <!-- Only show Resonance score if no First Mover (or smaller if both) -->
        <div v-if="!cluster.first_mover_news" class="flex items-center gap-2 px-3 py-1.5 rounded-full bg-orange-500/10 border border-orange-500/20">
          <span class="text-orange-500">🔥</span>
          <span class="text-[10px] font-black uppercase tracking-widest text-orange-500">Resonance {{ cluster.resonance_score }}</span>
        </div>
      </div>

      <h3 class="text-xl font-bold text-white leading-tight tracking-tight group-hover:text-primary transition-colors pr-20">
        {{ cluster.title }}
      </h3>
      <p class="text-slate-400 text-sm mt-3 line-clamp-2 leading-relaxed opacity-80">
        {{ cluster.summary }}
      </p>
    </div>

    <!-- Perspective View (Darker Inset) -->
    <div class="p-5 bg-black/20 mt-2">
      <div class="text-[9px] font-black text-text-muted uppercase tracking-[0.2em] mb-4 flex items-center gap-2 opacity-50">
        <div class="w-1.5 h-1.5 bg-orange-500 rounded-full shadow-[0_0_8px_rgba(249,115,22,0.5)]"></div>
        跨源视角 Perspectives
      </div>
      
      <div class="space-y-2">
        <div 
          v-for="item in previewItems" 
          :key="item.id" 
          @click="item.news?.url && window.open(item.news.url, '_blank')"
          class="flex gap-4 items-start group/item cursor-pointer p-3 rounded-2xl hover:bg-white/5 border border-transparent hover:border-white/5 transition-all"
        >
          <div class="mt-1 flex-shrink-0 w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center border border-white/5 group-hover/item:border-primary/30 transition-all">
            <span class="text-sm">{{ getPlatformIcon(item.platform_role) }}</span>
          </div>
          <div class="flex-1 min-w-0">
            <h4 class="text-xs font-bold text-slate-200 truncate group-hover/item:text-primary transition-colors">
              <span v-if="item.news_id === cluster.first_mover_news_id" class="text-primary mr-1">★</span>
              {{ item.news?.title || 'Unknown Source' }}
            </h4>
            <p class="text-[10px] text-text-muted line-clamp-1 mt-1 opacity-60 italic">
              {{ item.news?.reason || (item.news?.content ? item.news.content.substring(0, 80) : '点击阅读详情...') }}
            </p>
          </div>
          <div class="flex-shrink-0 opacity-0 group-hover/item:opacity-100 transition-all translate-x-2 group-hover/item:translate-x-0">
             <div class="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center text-primary">
               <span class="text-xs">↗</span>
             </div>
          </div>
        </div>
      </div>
      
      <!-- Expand Button -->
      <button v-if="cluster.news_items.length > 3" 
              @click="emit('filter-cluster', cluster.id)"
              class="w-full mt-5 py-3 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 hover:text-white bg-white/5 hover:bg-primary/20 border border-white/5 hover:border-primary/30 rounded-2xl transition-all active:scale-95 flex items-center justify-center gap-2 group/btn">
        查看全部 {{ cluster.news_items.length }} 个共振来源
        <span class="group-hover/btn:translate-x-1 transition-transform">→</span>
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
  metadata_json?: any;
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
  first_mover_news_id?: number;
  first_mover_tier?: string;
  first_mover_news?: NewsItem;
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

const getPlatformIcon = (platform: string) => {
  const p = platform?.toLowerCase() || '';
  if (p.includes('github')) return '🐙';
  if (p.includes('twitter')) return '🐦';
  if (p.includes('reddit')) return '👽';
  if (p.includes('arxiv')) return '📄';
  if (p.includes('hn')) return 'Y';
  return '🌐';
};

const getTierLabel = (tier: string | undefined) => {
  if (tier === 'S') return 'Elite Mover';
  if (tier === 'A') return 'Core Insight';
  return 'First Break';
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
