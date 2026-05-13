<script setup lang="ts">
import { formatDistanceToNow } from 'date-fns';
import { ExternalLink, Twitter, Youtube, Hash, Box, Terminal } from 'lucide-vue-next';

defineProps<{
  item: {
    id: number;
    platform: string;
    title: string;
    content: string;
    url: string;
    published_at: string;
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
  <div class="glass-card rounded-2xl p-6 transition-all duration-300 hover:translate-y-[-4px] hover:border-white/10 group animate-slide-up">
    <div class="flex justify-between items-start mb-4">
      <div class="flex items-center gap-2">
        <component 
          :is="platformIcons[item.platform.toLowerCase()] || Hash" 
          :class="['w-4 h-4', platformColors[item.platform.toLowerCase()] || 'text-text-muted']"
        />
        <span class="text-xs font-medium uppercase tracking-wider text-text-muted">
          {{ item.platform }}
        </span>
      </div>
      <span class="text-xs text-text-muted">
        {{ formatDistanceToNow(new Date(item.published_at)) }} ago
      </span>
    </div>
    
    <h3 class="text-lg font-semibold leading-snug mb-3 group-hover:text-primary transition-colors line-clamp-2">
      {{ item.title }}
    </h3>
    
    <p class="text-sm text-text-secondary line-clamp-3 mb-6 leading-relaxed">
      {{ item.content || 'No description available.' }}
    </p>
    
    <div class="flex justify-between items-center mt-auto">
      <div v-if="item.metadata_json?.score || item.metadata_json?.ups" class="text-xs text-text-muted flex items-center gap-1">
        <span class="font-medium text-text-secondary">{{ item.metadata_json?.score || item.metadata_json?.ups }}</span> points
      </div>
      <div v-else></div>
      
      <a 
        :href="item.url" 
        target="_blank" 
        class="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:text-accent transition-colors"
      >
        READ MORE
        <ExternalLink class="w-3 h-3" />
      </a>
    </div>
  </div>
</template>
