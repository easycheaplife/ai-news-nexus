<script setup lang="ts">
import { computed } from 'vue';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { Twitter, Youtube, Hash, Box, Terminal, Star, User, Github, BookOpen, CheckCircle2, Layers, MessageSquare, Building2, Play, Cpu, Newspaper, Zap, Landmark, Shield } from 'lucide-vue-next';

const props = defineProps<{
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

// 🛠️ 提取正文和评论
const contentParts = computed(() => {
  const content = props.item.content || '';
  // 识别不同的评论分隔符
  const separators = ['--- Reddit Community Insights ---', '--- HN Top Discussions ---', '--- 热门评论 ---'];
  
  let postBody = content;
  let comments: string[] = [];

  for (const sep of separators) {
    if (content.includes(sep)) {
      const parts = content.split(sep);
      postBody = parts[0].trim();
      // 提取前 2 条评论
      comments = parts[1].trim().split('\n\n').filter(c => c.trim()).slice(0, 2);
      break;
    }
  }

  // 清理包含 HTML 的抓取内容（如 Product Hunt 返回的带标签内容）
  if (/<(p|div|a\s+href|br|strong|b|em|i|span|ul|li)[^>]*>/i.test(postBody)) {
    postBody = postBody
      .replace(/<br\s*\/?>/gi, '\n')
      .replace(/<\/(p|div|h[1-6]|ul|li)>/gi, '\n')
      .replace(/<[^>]+>/g, '') // 移除其余所有标签
      .replace(/&nbsp;/g, ' ')
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/\s*Discussion\s*\|\s*Link\s*/gi, '') // 移除 Product Hunt 的底部固定无用文本
      .replace(/\n\s*\n/g, '\n') // 合并多余空行
      .trim();
  }

  return { postBody, comments };
});

// 🏆 平台显示映射
const platformDisplayName = computed(() => {
  const p = props.item.platform.toLowerCase();
  const domesticPlatforms = ['aihot', 'qbitai', '36kr', 'juejin', 'infoq', 'ithome', 'aiera', 'paperweekly', 'founderpark'];
  if (domesticPlatforms.includes(p)) return '智涌中国';
  return props.item.platform;
});

const platformIcons: Record<string, any> = {
  twitter: Twitter,
  x: Twitter,
  youtube: Youtube,
  reddit: Hash,
  ph: Box,
  hn: Terminal,
  github: Github,
  arxiv: BookOpen,
  labs: Building2,
  huggingface: Cpu,
  aihot: Newspaper,
  qbitai: Zap,
  '36kr': Star,
  juejin: MessageSquare,
  infoq: Layers,
  ithome: Newspaper,
  aiera: Globe,
  paperweekly: BookText,
  founderpark: Building,
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
  labs: 'bg-[#6366f1]/10 text-[#818cf8] border-[#6366f1]/30',
  huggingface: 'bg-[#FFD21E]/10 text-[#eab308] border-[#FFD21E]/30',
  aihot: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30',
  qbitai: 'bg-amber-500/10 text-amber-500 border-amber-500/30',
  '36kr': 'bg-blue-500/10 text-blue-500 border-blue-500/30',
  juejin: 'bg-indigo-500/10 text-indigo-500 border-indigo-500/30',
  infoq: 'bg-red-500/10 text-red-500 border-red-500/30',
  ithome: 'bg-rose-500/10 text-rose-500 border-rose-500/30',
  aiera: 'bg-cyan-500/10 text-cyan-500 border-cyan-500/30',
  paperweekly: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30',
  founderpark: 'bg-orange-500/10 text-orange-500 border-orange-500/30',
};

const decodeUrl = (url: string) => {
  if (!url) return '';
  const txt = document.createElement('textarea');
  txt.innerHTML = url;
  return txt.value;
};

// 🔗 智能路径拼接
const getFullUrl = (url: string) => {
  if (!url) return '';
  const decoded = decodeUrl(url);
  // 如果是相对路径 (/f/ 打头)，自动拼接后端地址
  if (decoded.startsWith('/f/')) {
    const apiUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
    // 如果 apiUrl 是 /api (Netlify 代理模式)，则保持相对路径，让浏览器处理
    if (!apiUrl.startsWith('http')) return decoded;
    return `${apiUrl}${decoded}`;
  }
  return decoded;
};

const isVideo = (url: string) => {
  if (!url) return false;
  const decoded = url.toLowerCase();
  const videoExtensions = ['.mp4', '.webm', '.ogg', '.m3u8', 'video', 'ext_tw_video', 'amplify_video'];
  return videoExtensions.some(ext => decoded.includes(ext));
};

const contentLines = parseInt(import.meta.env.VITE_CONTENT_LINES || '5');
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

    <div class="flex flex-col md:flex-row items-center gap-0 md:gap-8 p-3 md:p-5">
      <!-- 1. Media Preview (Compact & Fixed) -->
      <div 
        v-if="item.media_urls && item.media_urls.length > 0" 
        class="w-full md:w-[280px] lg:w-[380px] shrink-0 cursor-zoom-in group/media"
        @click="emit('expand-media', item)"
      >
        <div class="relative aspect-video rounded-xl overflow-hidden bg-black/40 border border-white/5 shadow-xl">
          <video 
            v-if="isVideo(item.media_urls[0])"
            :src="getFullUrl(item.media_urls[0])" 
            :poster="getFullUrl(item.media_urls[1])"
            class="w-full h-full object-cover rendering-sharp"
            autoplay muted loop playsinline preload="auto"
            referrerpolicy="no-referrer"
          ></video>
          <img 
            v-else
            :src="getFullUrl(item.media_urls[0])" 
            class="w-full h-full object-cover transition-transform duration-700 group-hover/media:scale-110 rendering-sharp"
            alt="Thumbnail"
            loading="lazy"
            referrerpolicy="no-referrer"
          />
          
          <div class="absolute inset-0 bg-primary/20 opacity-0 group-hover/media:opacity-100 transition-opacity flex items-center justify-center">
            <div v-if="item.platform.toLowerCase() === 'youtube'" class="bg-primary/90 p-4 rounded-full shadow-2xl scale-75 group-hover/media:scale-100 transition-transform duration-500">
              <Play class="w-8 h-8 text-white fill-white" />
            </div>
            <div v-else class="bg-white/10 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/20 text-[10px] font-black uppercase tracking-widest text-white shadow-2xl">
              Expand Content
            </div>
          </div>
          
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
            {{ platformDisplayName }}
            <span v-if="['aihot', 'qbitai', '36kr', 'juejin', 'infoq', 'ithome', 'aiera', 'paperweekly', 'founderpark', 'synced', 'zhihu_ai', 'guizang'].includes(item.platform.toLowerCase())" class="ml-1 opacity-60 normal-case font-bold">
              · {{ 
                item.platform === 'qbitai' ? '量子位' : 
                item.platform === '36kr' ? '36氪' : 
                item.platform === 'juejin' ? '掘金' : 
                item.platform === 'infoq' ? 'InfoQ' : 
                item.platform === 'ithome' ? 'IT之家' : 
                item.platform === 'aiera' ? '新智元' : 
                item.platform === 'paperweekly' ? 'PaperWeekly' : 
                item.platform === 'founderpark' ? 'Founder Park' : 
                item.platform === 'synced' ? '机器之心' : 
                item.platform === 'zhihu_ai' ? '知乎' : 
                item.platform === 'guizang' ? '归藏' : 'AI HOT' 
              }}
            </span>
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
        <a :href="item.url" target="_blank" class="block mb-3 group/title">
          <h3 :class="[
            'font-bold text-white transition-colors line-clamp-2 group-hover/title:text-primary',
            isFeatured ? 'text-lg md:text-xl' : 'text-base md:text-lg'
          ]">
            {{ item.title }}
          </h3>
        </a>

        <!-- 📄 原始正文 (Scraped Body Content) -->
        <div 
          v-if="contentParts.postBody" 
          class="mb-4 text-sm text-slate-300 leading-relaxed opacity-90 break-all whitespace-pre-wrap"
          :style="{ display: '-webkit-box', WebkitLineClamp: contentLines, WebkitBoxOrient: 'vertical', overflow: 'hidden' }"
        >
          {{ contentParts.postBody }}
        </div>

        <!-- 🧩 核心观点 (Takeaways) - 直接显示 (仅当有 AI 数据时) -->
        <div v-if="item.takeaways && item.takeaways.length > 0" class="mb-4 space-y-1.5">
          <div v-for="point in item.takeaways" :key="point" class="flex items-start gap-2">
            <CheckCircle2 class="w-3 h-3 text-primary mt-1 shrink-0" />
            <span class="text-[12px] font-bold text-slate-200 leading-snug">{{ point }}</span>
          </div>
        </div>

        <!-- 💬 精彩回帖 (Top Comments) -->
        <div v-if="contentParts.comments.length > 0" class="mb-4 space-y-2 bg-white/[0.03] p-2.5 rounded-lg border border-white/5">
          <div class="flex items-center gap-2 mb-1 opacity-50">
            <MessageSquare class="w-2.5 h-2.5" />
            <span class="text-[9px] font-black uppercase tracking-widest">社区精华讨论</span>
          </div>
          <div v-for="(comment, idx) in contentParts.comments" :key="idx" class="text-[11px] text-slate-400 italic leading-relaxed border-l border-white/10 pl-3 py-0.5 line-clamp-2 break-all">
            {{ comment }}
          </div>
        </div>

        <!-- AI Reason (Inline focus) -->
        <div v-if="item.reason" class="flex items-start gap-2 mb-4">
          <span class="mt-1.5 w-1 h-1 rounded-full bg-primary shrink-0"></span>
          <p class="text-[11px] text-text-muted italic opacity-80">
            AI 分析: "{{ item.reason }}"
          </p>
        </div>

        <!-- Takeaways & Meta Footer -->
        <div class="flex items-center justify-between mt-auto pt-2 border-t border-white/5">
          <div class="flex items-center gap-4">
            <div v-if="item.metadata_json?.author || item.metadata_json?.by" class="flex items-center gap-1 text-[10px] font-bold text-text-muted">
              <User class="w-2.5 h-2.5 opacity-50" />
              <span class="truncate max-w-[100px]">{{ item.metadata_json?.author || item.metadata_json?.by }}</span>
            </div>
            <div v-if="item.metadata_json?.ups || item.metadata_json?.hn_score" class="text-[10px] font-bold text-text-muted flex items-center gap-1">
              <span class="text-text-secondary">{{ item.metadata_json?.ups || item.metadata_json?.hn_score }}</span> 互动
            </div>
          </div>
          
          <div class="flex items-center gap-4">
            <a :href="item.url" target="_blank" class="text-[10px] font-black text-primary hover:text-white transition-colors uppercase tracking-widest">
              Read Original
            </a>
          </div>
        </div>
      </div>

      <!-- 3. Score (Prominent Right Side) -->
      <div v-if="item.score && item.score > 0" class="hidden md:flex flex-col items-center justify-center w-20 border-l border-white/5 px-4 bg-white/[0.02]">
        <Star class="w-4 h-4 text-yellow-500 fill-yellow-500 mb-1" />
        <span class="text-xl font-black text-white leading-none">{{ item.score }}</span>
        <span class="text-[8px] text-text-muted font-bold uppercase mt-1 tracking-tighter">Score</span>
      </div>
      <div v-else class="hidden md:flex flex-col items-center justify-center w-20 border-l border-white/5 px-4 bg-white/[0.02] opacity-50">
        <div class="w-4 h-4 rounded-full border-2 border-slate-500 border-t-transparent animate-spin mb-1"></div>
        <span class="text-[10px] font-black text-slate-400 leading-none mt-2">RAW</span>
        <span class="text-[7px] text-slate-500 font-bold uppercase mt-1 tracking-tighter">Pending</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.rendering-sharp {
  image-rendering: -webkit-optimize-contrast;
  image-rendering: crisp-edges;
}
</style>
