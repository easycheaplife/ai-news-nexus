<script setup lang="ts">
import { ref } from 'vue';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { ExternalLink, Twitter, Youtube, Hash, Box, Terminal, Star, User, Github, BookOpen, CheckCircle2, ChevronRight, Layers } from 'lucide-vue-next';

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
    takeaways?: string[];
    cluster_id?: string;
    media_urls?: string[];
    metadata_json?: any;
  },
  isFeatured?: boolean
}>();

const emit = defineEmits(['expand-media']);

const showDetails = ref(false);

const platformIcons: Record<string, any> = {
  twitter: Twitter,
  x: Twitter,
  youtube: Youtube,
  reddit: Hash,
  ph: Box,
  hn: Terminal,
  github: Github,
  arxiv: BookOpen,
};

const platformColors: Record<string, string> = {
  twitter: 'bg-[#1DA1F2]/10 text-[#1DA1F2] border-[#1DA1F2]/30',
  x: 'bg-white/10 text-white border-white/20',
  youtube: 'bg-[#FF0000]/10 text-[#FF0000] border-[#FF0000]/30',
  reddit: 'bg-[#FF4500]/10 text-[#FF4500] border-[#FF4500]/30',
  ph: 'bg-[#DA552F]/10 text-[#DA552F] border-[#DA552F]/30',
  hn: 'bg-[#FF6600]/10 text-[#FF6600] border-[#FF6600]/30',
  github: 'bg-[#333]/40 text-[#ffffff] border-white/20',
  arxiv: 'bg-[#B31B1B]/10 text-[#B31B1B] border-[#B31B1B]/30',
};

const decodeUrl = (url: string) => {
  if (!url) return '';
  const txt = document.createElement('textarea');
  txt.innerHTML = url;
  return txt.value;
};

const isVideo = (url: string) => {
  if (!url) return false;
  const decoded = url.toLowerCase();
  const videoExtensions = ['.mp4', '.webm', '.ogg', '.m3u8', 'video', 'ext_tw_video', 'amplify_video'];
  return videoExtensions.some(ext => decoded.includes(ext));
};

const getPoster = (mediaUrls?: string[]) => {
  if (!mediaUrls || mediaUrls.length < 2) return undefined;
  return isVideo(mediaUrls[0]) ? decodeUrl(mediaUrls[1]) : undefined;
};
</script>

<template>
  <div :class="[
    'group relative border transition-all duration-500 overflow-hidden flex flex-col w-full animate-slide-up',
    isFeatured 
      ? 'bg-gradient-to-r from-[#1a1a24] to-[#0a0a0c] border-primary/40 shadow-[0_0_40px_rgba(37,99,235,0.1)] rounded-[1.5rem]' 
      : 'bg-[#131316] hover:bg-[#18181c] border-white/5 rounded-xl hover:border-white/10'
  ]">
    <!-- ⚡️ Featured Accent -->
    <div v-if="isFeatured" class="absolute top-0 left-0 w-1.5 h-full bg-primary shadow-[0_0_15px_rgba(37,99,235,0.5)]"></div>

    <div class="flex flex-col md:flex-row items-stretch gap-0 md:gap-6 p-3 md:p-4">
      <!-- 1. Media Preview (Compact) -->
      <div 
        v-if="item.media_urls && item.media_urls.length > 0" 
        class="w-full md:w-[220px] lg:w-[320px] shrink-0 cursor-zoom-in group/media"
        @click="emit('expand-media', item)"
      >
        <div class="relative aspect-video rounded-lg overflow-hidden bg-black/20 border border-white/5 h-full">
          <video 
            v-if="isVideo(item.media_urls[0])"
            :src="decodeUrl(item.media_urls[0])" 
            :poster="getPoster(item.media_urls)"
            class="w-full h-full object-cover"
            autoplay muted loop playsinline preload="auto"
            referrerpolicy="no-referrer"
          ></video>
          <img 
            v-else
            :src="decodeUrl(item.media_urls[0])" 
            class="w-full h-full object-cover transition-transform duration-700 group-hover/media:scale-110"
            alt="Thumbnail"
            loading="lazy"
            referrerpolicy="no-referrer"
          />
          
          <!-- 🔍 Expand Indicator -->
          <div class="absolute inset-0 bg-primary/20 opacity-0 group-hover/media:opacity-100 transition-opacity flex items-center justify-center">
            <div class="bg-white/10 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/20 text-[10px] font-black uppercase tracking-widest text-white shadow-2xl">
              Expand Content
            </div>
          </div>
          
          <!-- Multi-media badge -->
          <div v-if="item.media_urls.length > 1" class="absolute bottom-2 right-2 bg-black/60 backdrop-blur-md px-1.5 py-0.5 rounded text-[8px] font-bold text-white border border-white/10">
            +{{ item.media_urls.length - 1 }} More
          </div>
        </div>
      </div>

      <!-- 2. Core Content -->
      <div class="flex-1 flex flex-col justify-center min-w-0 py-4 md:py-1 pr-2 md:pr-4">
        <!-- Platform & Time Header -->
        <div class="flex items-center gap-3 mb-2">
          <div :class="['px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-wider flex items-center gap-1.5 border', platformColors[item.platform.toLowerCase()] || 'bg-white/5 text-text-muted border-white/10']">
            <component :is="platformIcons[item.platform.toLowerCase()] || Hash" class="w-2.5 h-2.5" />
            {{ item.platform }}
          </div>
          <span class="text-[10px] font-bold text-text-muted uppercase">
            {{ formatDistanceToNow(new Date(item.published_at), { locale: zhCN, addSuffix: true }) }}
          </span>
          <div v-if="item.cluster_id" class="flex items-center gap-1 text-[10px] font-bold text-primary/60 truncate max-w-[150px]">
            <Layers class="w-2.5 h-2.5" />
            {{ item.cluster_id }}
          </div>
        </div>

        <!-- Title & Link -->
        <a :href="item.url" target="_blank" class="block mb-2 group/title">
          <h3 :class="[
            'font-bold text-white transition-colors line-clamp-1 group-hover/title:text-primary',
            isFeatured ? 'text-lg md:text-xl' : 'text-base md:text-lg'
          ]">
            {{ item.title }}
          </h3>
        </a>

        <!-- AI Reason (Inline focus) -->
        <div v-if="item.reason" class="flex items-start gap-2 mb-3">
          <span class="mt-1 w-1.5 h-1.5 rounded-full bg-primary shrink-0"></span>
          <p class="text-xs text-slate-400 italic line-clamp-1">
            "{{ item.reason }}"
          </p>
        </div>

        <!-- Takeaways & Meta Footer -->
        <div class="flex items-center justify-between mt-auto pt-2 border-t border-white/5">
          <div class="flex items-center gap-4">
            <button 
              v-if="item.takeaways && item.takeaways.length > 0"
              @click="showDetails = !showDetails"
              class="text-[10px] font-black uppercase tracking-widest text-primary/80 hover:text-primary transition-colors flex items-center gap-1"
            >
              要点 <ChevronRight :class="['w-3 h-3 transition-transform', showDetails ? 'rotate-90' : '']" />
            </button>
            <div v-if="item.metadata_json?.author || item.metadata_json?.by" class="flex items-center gap-1 text-[10px] font-bold text-text-muted">
              <User class="w-2.5 h-2.5 opacity-50" />
              <span class="truncate max-w-[100px]">{{ item.metadata_json?.author || item.metadata_json?.by }}</span>
            </div>
          </div>
          
          <div class="flex items-center gap-4">
             <div v-if="item.metadata_json?.ups || item.metadata_json?.hn_score" class="text-[10px] font-bold text-text-muted flex items-center gap-1">
              <span class="text-text-secondary">{{ item.metadata_json?.ups || item.metadata_json?.hn_score }}</span> 互动
            </div>
            <a :href="item.url" target="_blank" class="text-[10px] font-black text-primary hover:text-white transition-colors uppercase tracking-widest">
              Detail
            </a>
          </div>
        </div>

        <!-- Expandable Takeaways -->
        <transition enter-active-class="transition-all duration-300 ease-out" enter-from-class="max-h-0 opacity-0" enter-to-class="max-h-40 opacity-100">
          <ul v-if="showDetails" class="mt-4 space-y-2 border-t border-white/5 pt-4">
            <li v-for="p in item.takeaways" :key="p" class="flex items-center gap-2 text-[11px] text-slate-300">
              <CheckCircle2 class="w-3 h-3 text-primary/60" /> {{ p }}
            </li>
          </ul>
        </transition>
      </div>

      <!-- 3. Score (Prominent Right Side) -->
      <div class="hidden md:flex flex-col items-center justify-center w-20 border-l border-white/5 px-4 bg-white/[0.02]">
        <Star class="w-4 h-4 text-yellow-500 fill-yellow-500 mb-1" />
        <span class="text-xl font-black text-white leading-none">{{ item.score || 0 }}</span>
        <span class="text-[8px] text-text-muted font-bold uppercase mt-1 tracking-tighter">Score</span>
      </div>
    </div>
  </div>
</template>
