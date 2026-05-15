<script setup lang="ts">
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { ExternalLink, Twitter, Youtube, Hash, Box, Terminal, Star, User } from 'lucide-vue-next';

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
  twitter: 'bg-[#1DA1F2]/10 text-[#1DA1F2]',
  x: 'bg-white/10 text-white',
  youtube: 'bg-[#FF0000]/10 text-[#FF0000]',
  reddit: 'bg-[#FF4500]/10 text-[#FF4500]',
  ph: 'bg-[#DA552F]/10 text-[#DA552F]',
  hn: 'bg-[#FF6600]/10 text-[#FF6600]',
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
  const videoExtensions = ['.mp4', '.webm', '.ogg', '.m3u8'];
  return videoExtensions.some(ext => url.toLowerCase().includes(ext));
};
</script>

<template>
  <div class="group relative bg-[#131316] hover:bg-[#1a1a1e] border border-white/5 rounded-[2rem] p-5 md:p-8 transition-all duration-500 hover:shadow-[0_20px_50px_rgba(0,0,0,0.5)] hover:-translate-y-1 overflow-hidden">
    <!-- Header: Platform, Time, Score -->
    <div class="flex flex-wrap items-center justify-between gap-3 mb-6">
      <div class="flex items-center gap-2">
        <div :class="['px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-[0.1em] flex items-center gap-1.5', platformColors[item.platform.toLowerCase()] || 'bg-white/5 text-text-muted']">
          <component :is="platformIcons[item.platform.toLowerCase()] || Hash" class="w-3 h-3" />
          {{ item.platform }}
        </div>
        <span class="text-[10px] font-bold text-text-muted uppercase tracking-widest bg-white/5 px-3 py-1 rounded-full">
          {{ formatDistanceToNow(new Date(item.published_at), { locale: zhCN, addSuffix: true }) }}
        </span>
      </div>
      
      <!-- Quality Score -->
      <div v-if="item.score && item.score > 0" class="flex items-center gap-1.5 bg-yellow-400/10 px-3 py-1 rounded-full border border-yellow-400/20">
        <Star class="w-3.5 h-3.5 text-yellow-500 fill-yellow-500" />
        <span class="text-xs font-bold text-yellow-500">{{ item.score }}</span>
      </div>
    </div>

    <div class="flex flex-col md:flex-row gap-6 md:gap-8 items-start">
      <!-- Content Side -->
      <div class="flex-1 min-w-0">
        <!-- Title -->
        <a :href="item.url" target="_blank" class="block group/title">
          <h3 class="text-lg md:text-xl font-bold text-white leading-snug mb-4 group-hover/title:text-primary transition-colors line-clamp-2">
            {{ item.title }}
          </h3>
        </a>

        <!-- 🤖 AI 推荐理由 (高亮核心展示) -->
        <div v-if="item.reason && item.reason.length > 5 && !item.reason.includes('Evaluation error')" class="relative mb-6 p-4 rounded-xl bg-primary/5 border border-primary/10 overflow-hidden group/reason">
          <div class="absolute top-0 left-0 w-1 h-full bg-primary opacity-30 group-hover/reason:opacity-100 transition-opacity"></div>
          <p class="text-sm text-slate-300 leading-relaxed italic relative">
            <span class="not-italic font-bold text-[10px] uppercase tracking-widest text-primary block mb-2 opacity-60">AI 推荐理由</span>
            "{{ item.reason }}"
          </p>
        </div>

        <!-- Content Snippet -->
        <p class="text-sm text-text-muted leading-relaxed line-clamp-3 mb-6 font-medium">
          {{ item.content || '暂无详细描述。' }}
        </p>

        <!-- Footer Info -->
        <div class="flex items-center justify-between pt-6 border-t border-white/5 mt-auto">
          <div class="flex items-center gap-4">
            <!-- Author -->
            <div v-if="item.metadata_json?.author || item.metadata_json?.by" class="flex items-center gap-1.5 text-[11px] font-bold text-text-muted">
              <User class="w-3 h-3 opacity-50" />
              <span class="truncate max-w-[100px]">{{ item.metadata_json?.author || item.metadata_json?.by }}</span>
            </div>
            <!-- Interactions -->
            <div v-if="item.metadata_json?.hn_score || item.metadata_json?.ups" class="text-[11px] font-bold text-text-muted flex items-center gap-1.5">
              <span class="bg-white/5 px-2 py-0.5 rounded-md text-text-secondary">{{ item.metadata_json?.hn_score || item.metadata_json?.ups }}</span>
              <span>互动</span>
            </div>
          </div>

          <a 
            :href="item.url" 
            target="_blank" 
            class="flex items-center gap-2 text-xs font-black text-primary hover:text-white transition-all group/link"
          >
            详情
            <ExternalLink class="w-3 h-3 group-hover/link:translate-x-0.5 group-hover/link:-translate-y-0.5 transition-transform" />
          </a>
        </div>
      </div>

      <!-- Media Side (PC side, Mobile below) -->
      <div v-if="item.media_urls && item.media_urls.length > 0" class="w-full md:w-[380px] shrink-0">
        <div class="relative aspect-video rounded-2xl overflow-hidden border border-white/5 bg-white/5">
          <!-- Video Player -->
          <video 
            v-if="isVideo(item.media_urls[0])"
            :src="decodeUrl(item.media_urls[0])" 
            class="w-full h-full object-cover"
            autoplay
            muted
            loop
            playsinline
            controls
            preload="metadata"
            referrerpolicy="no-referrer"
          ></video>
          <!-- Image Player -->
          <img 
            v-else
            :src="decodeUrl(item.media_urls[0])" 
            class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
            alt="Content preview"
            loading="lazy"
            referrerpolicy="no-referrer"
            @error="(e: any) => e.target.style.display = 'none'"
          />
          <div class="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
        </div>
      </div>
    </div>
  </div>
</template>
