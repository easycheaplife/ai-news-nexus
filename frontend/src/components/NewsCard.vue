<script setup lang="ts">
import { formatDistanceToNow } from 'date-fns';
import { ExternalLink, Twitter, Youtube, Hash, Box, Terminal, Star, Image as ImageIcon } from 'lucide-vue-next';

defineProps<{
  item: {
    id: number;
    platform: string;
    title: string;
    content: string;
    url: string;
    published_at: string;
    score?: number;
    reason?: string;
    media_urls?: string[];
    metadata_json?: any;
  }
}>();

const platformIcons: Record<string, any> = {
  twitter: Twitter,
  x: Twitter,
  youtube: Youtube,
  reddit: Hash,
  ph: Box,
  hn: Terminal,
};

const platformColors: Record<string, string> = {
  twitter: 'text-sky-400',
  x: 'text-text-primary',
  youtube: 'text-red-500',
  reddit: 'text-orange-500',
  ph: 'text-orange-600',
  hn: 'text-orange-400',
};
</script>

<template>
  <div class="glass-card rounded-2xl p-4 md:p-6 transition-all duration-300 hover:translate-y-[-4px] hover:border-white/10 group animate-slide-up flex flex-col h-full">
    <div class="flex justify-between items-start mb-3 md:mb-4">
      <div class="flex items-center gap-2">
        <component 
          :is="platformIcons[item.platform.toLowerCase()] || Hash" 
          :class="['w-3.5 h-3.5 md:w-4 md:h-4', platformColors[item.platform.toLowerCase()] || 'text-text-muted']"
        />
        <span class="text-[10px] md:text-xs font-medium uppercase tracking-wider text-text-muted">
          {{ item.platform }}
        </span>
      </div>
      <span class="text-[10px] md:text-xs text-text-muted">
        {{ formatDistanceToNow(new Date(item.published_at)) }} 前
      </span>
    </div>

    <!-- 🖼️ Media Preview -->
    <div v-if="item.media_urls && item.media_urls.length > 0" class="mb-3 md:mb-4 rounded-xl overflow-hidden aspect-video bg-white/5 border border-white/5 relative shrink-0">
      <img 
        :src="item.media_urls[0]" 
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
        alt="Media content"
        loading="lazy"
        @error="(e: any) => e.target.style.display = 'none'"
      />
      <!-- 🤖 AI Score Badge -->
      <div v-if="item.score && item.score > 0" class="absolute top-2 right-2 bg-black/60 backdrop-blur-md px-1.5 md:px-2 py-0.5 md:py-1 rounded-lg border border-white/10 flex items-center gap-1">
        <Star class="w-2.5 h-2.5 md:w-3 md:h-3 text-yellow-400 fill-yellow-400" />
        <span class="text-[9px] md:text-[10px] font-bold text-white">{{ item.score }}</span>
      </div>
    </div>
    
    <h3 class="text-base md:text-lg font-semibold leading-snug mb-2 md:mb-3 group-hover:text-primary transition-colors line-clamp-2">
      {{ item.title }}
    </h3>

    <!-- 🤖 AI 推荐理由 -->
    <div v-if="item.reason && item.reason.length > 5 && !item.reason.includes('Evaluation error')" class="mb-3 md:mb-4 p-2.5 md:p-3 rounded-xl bg-primary/5 border border-primary/10 italic shrink-0">
      <p class="text-[11px] md:text-xs text-primary leading-relaxed">
        <span class="font-bold uppercase tracking-widest text-[9px] md:text-[10px] block mb-0.5 md:mb-1 opacity-80">推荐理由</span>
        "{{ item.reason }}"
      </p>
    </div>
    
    <p class="text-xs md:text-sm text-text-secondary line-clamp-3 mb-4 md:mb-6 leading-relaxed flex-grow">
      {{ item.content || '暂无详细描述。' }}
    </p>
    
    <div class="flex justify-between items-center mt-auto pt-2 border-t border-white/5">
      <div class="flex items-center gap-3">
        <div v-if="item.metadata_json?.score || item.metadata_json?.ups" class="text-[10px] md:text-xs text-text-muted flex items-center gap-1">
          <span class="font-medium text-text-secondary">{{ item.metadata_json?.score || item.metadata_json?.ups }}</span> 互动
        </div>
        <!-- Non-media items still show score here if not on badge -->
        <div v-if="(!item.media_urls || item.media_urls.length === 0) && item.score" class="flex items-center gap-1 bg-yellow-400/10 px-1.5 py-0.5 rounded text-[9px] md:text-[10px] text-yellow-500 font-bold border border-yellow-400/20">
          <Star class="w-2.5 h-2.5 fill-yellow-500" />
          {{ item.score }}
        </div>
      </div>
      
      <a 
        :href="item.url" 
        target="_blank" 
        class="inline-flex items-center gap-1 text-[10px] md:text-xs font-semibold text-primary hover:text-accent transition-colors"
      >
        阅读原文
        <ExternalLink class="w-3 h-3" />
      </a>
    </div>
  </div>
</template>
