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

const showTakeaways = ref(false);

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
  twitter: 'bg-[#1DA1F2]/10 text-[#1DA1F2]',
  x: 'bg-white/10 text-white',
  youtube: 'bg-[#FF0000]/10 text-[#FF0000]',
  reddit: 'bg-[#FF4500]/10 text-[#FF4500]',
  ph: 'bg-[#DA552F]/10 text-[#DA552F]',
  hn: 'bg-[#FF6600]/10 text-[#FF6600]',
  github: 'bg-[#333]/40 text-[#ffffff]',
  arxiv: 'bg-[#B31B1B]/10 text-[#B31B1B]',
};

// 🛠️ 处理编码过的 URL (如 Reddit 的 &amp;)
const decodeUrl = (url: string) => {
  if (!url) return '';
  const txt = document.createElement('textarea');
  txt.innerHTML = url;
  return txt.value;
};

// 🎥 判断是否为视频
const isVideo = (url: string) => {
  if (!url) return false;
  const decoded = url.toLowerCase();
  const videoExtensions = ['.mp4', '.webm', '.ogg', '.m3u8', 'video', 'ext_tw_video', 'amplify_video'];
  return videoExtensions.some(ext => decoded.includes(ext));
};

// 🖼️ 获取备选封面图
const getPoster = (mediaUrls?: string[]) => {
  if (!mediaUrls || mediaUrls.length < 2) return undefined;
  return isVideo(mediaUrls[0]) ? decodeUrl(mediaUrls[1]) : undefined;
};
</script>

<template>
  <div :class="[
    'group relative border rounded-[2rem] transition-all duration-700 overflow-hidden flex flex-col h-full',
    isFeatured 
      ? 'bg-gradient-to-br from-[#1a1a24] via-[#131316] to-[#0a0a0c] border-primary/30 shadow-[0_0_50px_rgba(37,99,235,0.15)] p-6 md:p-10' 
      : 'bg-[#131316] hover:bg-[#1a1a1e] border-white/5 p-5 md:p-8 hover:shadow-[0_20px_50px_rgba(0,0,0,0.5)] hover:-translate-y-1'
  ]">
    <!-- 🌠 Premium Glow Effect for Featured -->
    <div v-if="isFeatured" class="absolute -top-24 -right-24 w-64 h-64 bg-primary/10 rounded-full blur-[100px] pointer-events-none"></div>
    
    <!-- Header: Platform, Time, Score -->
    <div class="flex flex-wrap items-center justify-between gap-3 mb-6 relative z-10">
      <div class="flex items-center gap-2">
        <div :class="['px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-[0.1em] flex items-center gap-1.5', platformColors[item.platform.toLowerCase()] || 'bg-white/5 text-text-muted']">
          <component :is="platformIcons[item.platform.toLowerCase()] || Hash" class="w-3 h-3" />
          {{ item.platform }}
        </div>
        <span class="text-[10px] font-bold text-text-muted uppercase tracking-widest bg-white/5 px-3 py-1 rounded-full">
          {{ formatDistanceToNow(new Date(item.published_at), { locale: zhCN, addSuffix: true }) }}
        </span>
        <div v-if="isFeatured" class="px-3 py-1 rounded-full bg-primary text-white text-[10px] font-black uppercase tracking-widest shadow-lg shadow-primary/20 animate-pulse">
          Featured
        </div>
      </div>
      
      <!-- Quality Score -->
      <div v-if="item.score && item.score > 0" class="flex items-center gap-1.5 bg-yellow-400/10 px-3 py-1 rounded-full border border-yellow-400/20">
        <Star class="w-3.5 h-3.5 text-yellow-500 fill-yellow-500" />
        <span class="text-xs font-bold text-yellow-500">{{ item.score }}</span>
      </div>
    </div>

    <div class="flex flex-col lg:flex-row gap-6 md:gap-8 items-start relative z-10">
      <!-- Media Side -->
      <div v-if="item.media_urls && item.media_urls.length > 0" :class="['w-full lg:w-[320px] shrink-0', isFeatured ? 'lg:w-[400px]' : '']">
        <div class="relative aspect-video rounded-2xl overflow-hidden border border-white/5 bg-white/5 shadow-2xl">
          <video 
            v-if="isVideo(item.media_urls[0])"
            :src="decodeUrl(item.media_urls[0])" 
            :poster="getPoster(item.media_urls)"
            class="w-full h-full object-cover"
            autoplay muted loop playsinline controls preload="auto"
            referrerpolicy="no-referrer"
          ></video>
          <img 
            v-else
            :src="decodeUrl(item.media_urls[0])" 
            class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
            alt="Content preview"
            loading="lazy"
            referrerpolicy="no-referrer"
            @error="(e: any) => e.target.style.display = 'none'"
          />
          <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
        </div>
      </div>

      <!-- Content Side -->
      <div class="flex-1 min-w-0">
        <a :href="item.url" target="_blank" class="block group/title">
          <h3 :class="[
            'font-bold text-white leading-tight mb-4 group-hover/title:text-primary transition-colors line-clamp-2',
            isFeatured ? 'text-2xl md:text-3xl' : 'text-lg md:text-xl'
          ]">
            {{ item.title }}
          </h3>
        </a>

        <div v-if="item.reason && item.reason.length > 5 && !item.reason.includes('Evaluation error')" class="relative mb-4 p-4 rounded-xl bg-primary/5 border border-primary/10 overflow-hidden group/reason">
          <div class="absolute top-0 left-0 w-1 h-full bg-primary opacity-30 group-hover/reason:opacity-100 transition-opacity"></div>
          <p class="text-sm text-slate-300 leading-relaxed italic relative">
            <span class="not-italic font-bold text-[10px] uppercase tracking-widest text-primary block mb-2 opacity-60">AI 推荐理由</span>
            "{{ item.reason }}"
          </p>
        </div>

        <div v-if="item.takeaways && item.takeaways.length > 0" class="mb-6">
          <button @click="showTakeaways = !showTakeaways" class="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-primary/80 hover:text-primary transition-colors">
            <ChevronRight :class="['w-3.5 h-3.5 transition-transform duration-300', (showTakeaways || isFeatured) ? 'rotate-90' : '']" />
            核心要点 · Key Takeaways
          </button>
          <transition enter-active-class="transition-all duration-300 ease-out" enter-from-class="max-h-0 opacity-0" enter-to-class="max-h-60 opacity-100">
            <ul v-if="showTakeaways || isFeatured" class="mt-4 space-y-3 pl-2 border-l border-white/5 ml-1.5">
              <li v-for="point in item.takeaways" :key="point" class="flex items-start gap-3 group/point">
                <CheckCircle2 class="w-3.5 h-3.5 text-primary/60 group-hover/point:text-primary transition-colors mt-0.5" />
                <span :class="['text-slate-400 group-hover/point:text-slate-200 transition-colors', isFeatured ? 'text-sm' : 'text-xs']">{{ point }}</span>
              </li>
            </ul>
          </transition>
        </div>

        <p :class="['text-text-muted leading-relaxed line-clamp-3 mb-6 font-medium', isFeatured ? 'text-base' : 'text-sm']">
          {{ item.content || '暂无详细描述。' }}
        </p>

        <div class="flex items-center justify-between pt-6 border-t border-white/5 mt-auto">
          <div class="flex items-center gap-4">
            <div v-if="item.metadata_json?.author || item.metadata_json?.by" class="flex items-center gap-1.5 text-[11px] font-bold text-text-muted">
              <User class="w-3 h-3 opacity-50" />
              <span class="truncate max-w-[150px]">{{ item.metadata_json?.author || item.metadata_json?.by }}</span>
            </div>
            <div v-if="item.metadata_json?.hn_score || item.metadata_json?.ups" class="text-[11px] font-bold text-text-muted flex items-center gap-1.5">
              <span class="bg-white/5 px-2 py-0.5 rounded-md text-text-secondary">{{ item.metadata_json?.hn_score || item.metadata_json?.ups }}</span>
              <span>互动</span>
            </div>
            <div v-if="item.cluster_id" class="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-500 text-[10px] font-black uppercase tracking-wider border border-blue-500/20">
              <Layers class="w-3 h-3" />
              {{ item.cluster_id }}
            </div>
          </div>
          <a :href="item.url" target="_blank" class="flex items-center gap-2 text-xs font-black text-primary hover:text-white transition-all group/link">
            详情 <ExternalLink class="w-3 h-3 group-hover/link:translate-x-0.5 group-hover/link:-translate-y-0.5 transition-transform" />
          </a>
        </div>
      </div>
    </div>
  </div>
</template>
