<script setup lang="ts">
import { Zap, Activity, ArrowRight, Search, Globe, ShieldCheck, Languages } from 'lucide-vue-next';
import { ref, onMounted, computed } from 'vue';

const isScrolled = ref(false);
const lang = ref<'zh' | 'en'>('zh');

const t = computed(() => {
  const content = {
    zh: {
      nav: { intelligence: '情报能力', curation: '自动化', narrative: '叙事风格', enter: '进入指挥部' },
      hero: {
        edition: '刊号：2026年6月13日',
        live: '系统运行中',
        title_top: 'AI 时代，喧嚣遍地。',
        title_bottom: '只看 70 分以上的干货。',
        sub: '全球首个全自动 AI 战略情报系统。我们从海量信号中打捞核心，识别语义共振，通过 Strike 信用分实时清洗信源，确保每一条推送都是决策级的资产。',
        cta: '阅读今日情报'
      },
      resonance: {
        title: '全球话题共振',
        desc: '"通过语义聚类算法，跨源交叉验证 Twitter, GitHub 与 ArXiv，捕捉最真实的行业共鸣。"',
        new_signal: '发现新信源',
        vetted: '已通过 AI 面试'
      },
      synthesis: {
        eyebrow: '01 / 深度合成',
        title: '数据是负担，\n洞察是资产。',
        p1: 'Nexus 2.0 引入了首发溯源 (First Break) 勋章，利用高精度算法识别全球 AI 资讯的最早源头。我们不仅评估内容，更是在寻找“第一现场”。',
        p2: '全新的“战略资产库”实现了技术名词 (Wiki) 的自动沉淀与深度研报 (Whitepapers) 的双周自动产出。低于 71 分的垃圾资讯将被自动拦截，确保你只阅读最有价值的情报资产。',
        f1: '资产库自动沉淀',
        f2: 'Strike 实时清洗',
        f3: '双周战略白皮书',
        f4: '白皮书一键导出',
        f1_sub: 'Wiki 词条自动生成',
        f2_sub: '低质量信源自动熔断',
        f3_sub: '从碎片信号到深度综述',
        f4_sub: '支持 MD/PDF 卷宗下载'
      },
      narrative: {
        eyebrow: '02 / 多维叙事',
        title: '同一信号，\n多重真相。',
        toxic: '毒舌内参版',
        official: '正经战略版',
        toxic_p: '"又是一个拿风投资金堆出来的\'突破\'？不过是给上个月的 API 刷了层新漆。技术债累累，但营销团队已经去巴哈马度假了。等延迟降到 2 秒以下再叫醒我。"',
        official_p: '"当前市场趋势表明中间件服务正在加速整合。战略资源配置显示，行业目前更倾向于短期投资回报（ROI），而非架构的绝对纯净性。"'
      },
      craft: {
        status: '系统初始化中...',
        source: '正在连接全球 X Syndication...',
        success: '成功捕捉 482 个高熵节点。',
        ai_route: '正在将负载路由至 Gemini 3.1...',
        cluster: '正在映射 12 个潜在话题的共振关系...',
        ready: '今日情报已生成。点击查看 ->'
      },
      footer: {
        cta: '掌控叙事，\n部署你的情报中心。',
        cta_btn: '立即进入',
        guide: '战略指南',
        docs: 'API 文档',
        github: 'GitHub 仓库'
      }
    },
    en: {
      nav: { intelligence: 'Intelligence', curation: 'Curation', narrative: 'Narrative', enter: 'Enter Command Center' },
      hero: {
        edition: 'Edition: June 13, 2026',
        live: 'Live Now',
        title_top: 'AI IS NOISY.',
        title_bottom: 'SIGNAL > 70 ONLY.',
        sub: "The world's first autonomous intelligence briefing. We harvest signals, cluster them by resonance, and purge low-value sources via real-time Strike system. Every day.",
        cta: "Read Today's Report"
      },
      resonance: {
        title: 'Global\nResonance.',
        desc: '"Real-time semantic clustering cross-references Twitter, GitHub and ArXiv for the truest industry heartbeat."',
        new_signal: 'New Signal Found',
        vetted: 'Auto-Vetted'
      },
      synthesis: {
        eyebrow: '01 / Synthesis',
        title: 'Data is a liability.\nInsight is an asset.',
        p1: "Nexus 2.0 introduces 'First Break' sourcing badges, identifying the original origin of global AI news. We don't just evaluate—we find the front line.",
        p2: "The new 'Asset Hub' enables autonomous Technical Wiki synthesis and Bi-Weekly Whitepaper generation. Content under 71 points is purged, turning noisy feeds into strategic assets.",
        f1: 'Asset Hub Sync',
        f2: 'Real-time Strike',
        f3: 'Strategic Dossiers',
        f4: 'One-Click Export',
        f1_sub: 'Auto Wiki Generation',
        f2_sub: 'Auto-circuit breaker',
        f3_sub: 'Signals to Synthesis',
        f4_sub: 'MD/PDF Downloads'
      },
      narrative: {
        eyebrow: '02 / Narrative',
        title: 'One Signal.\nMultiple Truths.',
        toxic: 'Toxic Mode',
        official: 'Official Mode',
        toxic_p: '"Another venture-backed \'breakthrough\' that\'s just a wrapper around last month\'s API. The technical debt is screaming, but the marketing team is already in the Bahamas. Wake me up when latency drops below 2s."',
        official_p: '"Current market trends indicate a consolidation of middleware services. Strategic allocation of resources suggests an emphasis on short-term ROI over architectural purity."'
      },
      craft: {
        status: 'initializing intelligence nexus...',
        source: 'connecting to global x syndication...',
        success: 'success: captured 482 high-entropy nodes.',
        ai_route: 'routing payload to gemini-3.1...',
        cluster: 'mapping resonance across 12 topics...',
        ready: 'Daily briefing generated. View ->'
      },
      footer: {
        cta: 'Master the Narrative.\nDeploy Your Intel Center.',
        cta_btn: 'Deploy Now',
        guide: 'Strategy Guide',
        docs: 'API Docs',
        github: 'GitHub'
      }
    }
  };
  return content[lang.value];
});

const toggleLang = () => {
  lang.value = lang.value === 'zh' ? 'en' : 'zh';
};

const liveSignals = [
  "🥇 First Break: @karpathy identified as original source",
  "📘 Wiki: New term 'MoE' synthesized and cross-referenced",
  "📜 Whitepaper: '2026 Q2 Trend Report' generated & signed",
  "🛡️ Strike: @low_quality_bot deactivated (Failure Count: 15/15)",
  "🥇 First Break: @bindureddy credited for 'Claude 5.5' leak",
  "📥 Export: Strategic Dossier downloaded in PDF format"
];

onMounted(() => {
  window.addEventListener('scroll', () => {
    isScrolled.value = window.scrollY > 50;
  });
});
</script>

<template>
  <div class="magazine-landing min-h-screen">
    <!-- Header -->
    <header :class="{ 'scrolled': isScrolled }" class="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 md:px-12 h-20 transition-all duration-500 border-b border-white/5">
      <router-link to="/" class="flex items-center gap-2 hover:opacity-80 transition-opacity">
        <div class="bg-primary p-1.5 rounded">
          <Zap class="w-5 h-5 text-white" />
        </div>
        <span class="logo-text text-xl font-black uppercase tracking-tighter text-ink">Nexus.</span>
      </router-link>
      
      <div class="flex items-center gap-6">
        <nav class="hidden lg:flex items-center gap-10 mr-10">
          <a href="#resonance" class="nav-link">{{ t.nav.intelligence }}</a>
          <a href="#curation" class="nav-link">{{ t.nav.curation }}</a>
          <a href="#narrative" class="nav-link">{{ t.nav.narrative }}</a>
        </nav>
        
        <button @click="toggleLang" class="nav-link flex items-center gap-1 hover:text-primary transition-colors">
          <Languages class="w-3 h-3" />
          {{ lang === 'zh' ? 'EN' : '中' }}
        </button>

        <router-link to="/app" class="button-cta group">
          <span>{{ t.nav.enter }}</span>
          <ArrowRight class="w-4 h-4 group-hover:translate-x-1 transition-transform" />
        </router-link>
      </div>
    </header>

    <main class="pt-24 pb-20">
      <!-- Hero Magazine Grid -->
      <section id="hero" class="max-w-[1400px] mx-auto px-6 md:px-12 grid grid-cols-1 lg:grid-cols-12 gap-6 mb-20">
        <!-- A: The Lead Story -->
        <div @click="$router.push('/app')" class="lg:col-span-8 bg-surface-1 border border-hairline rounded-3xl p-10 md:p-16 relative overflow-hidden flex flex-col justify-end min-h-[500px] group cursor-pointer hover:border-primary/30 transition-all duration-500">
          <div class="absolute inset-0 bg-[url('/src/assets/hero.png')] bg-cover bg-center opacity-20 grayscale group-hover:scale-105 group-hover:grayscale-0 transition-all duration-[2s]"></div>
          <div class="absolute inset-0 bg-gradient-to-t from-midnight via-midnight/60 to-transparent"></div>
          
          <div class="relative z-10 animate-slide-up">
            <div class="flex items-center gap-3 mb-6">
              <span class="eyebrow">{{ t.hero.edition }}</span>
              <div class="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></div>
              <span class="eyebrow text-primary">{{ t.hero.live }}</span>
            </div>
            <h1 class="display-xl text-ink leading-[1.1] mb-8 whitespace-pre-line">
              {{ t.hero.title_top }}<br/>
              <span class="text-primary italic">NEXUS</span> {{ t.hero.title_bottom }}
            </h1>
            <p class="body-lg text-ink-muted max-w-xl mb-10">
              {{ t.hero.sub }}
            </p>
            <div class="inline-flex items-center gap-4 text-ink font-bold group-hover:text-primary transition-colors">
              {{ t.hero.cta }} <ArrowRight class="w-5 h-5 group-hover:translate-x-2 transition-transform" />
            </div>
          </div>
        </div>

        <!-- B: The Pulse / Resonance -->
        <div class="lg:col-span-4 flex flex-col gap-6">
          <div @click="$router.push('/app')" class="flex-1 bg-surface-1 border border-hairline rounded-3xl p-8 relative overflow-hidden cursor-pointer hover:border-primary/30 hover:bg-surface-2 transition-all group/resonance">
            <div class="flex justify-between items-start mb-12">
              <h3 class="card-title leading-tight whitespace-pre-line">{{ t.resonance.title }}</h3>
              <Activity class="w-6 h-6 text-primary group-hover/resonance:scale-110 transition-transform" />
            </div>
            <div class="space-y-6">
              <div v-for="(topic, idx) in ['AGI Evolution', 'Edge Reasoning', 'Token Economics']" :key="idx" class="relative">
                <div class="flex justify-between text-[10px] font-bold uppercase tracking-widest text-ink-muted mb-2">
                  <span>{{ topic }}</span>
                  <span>{{ 95 - (idx * 12) }}%</span>
                </div>
                <div class="h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <div class="h-full bg-primary" :style="{ width: `${95 - (idx * 12)}%` }"></div>
                </div>
              </div>
            </div>
            <p class="mt-8 text-[11px] text-ink-subtle leading-relaxed italic">
              {{ t.resonance.desc }}
            </p>
          </div>

          <div @click="$router.push('/app')" class="bg-primary/10 border border-primary/20 rounded-3xl p-8 group hover:bg-primary/20 transition-all cursor-pointer">
            <h4 class="text-xs font-black uppercase tracking-widest text-primary mb-4">{{ t.resonance.new_signal }}</h4>
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">B</div>
              <div>
                <p class="text-sm font-bold text-ink">@baoyu_share</p>
                <p class="text-[10px] text-primary/60 font-bold uppercase">{{ t.resonance.vetted }}: 94/100</p>
              </div>
            </div>
          </div>
        </div>

        <!-- C: The Ticker -->
        <div class="lg:col-span-12 h-16 bg-midnight border-y border-hairline relative overflow-hidden flex items-center">
          <div class="ticker-content flex items-center gap-12 px-6 whitespace-nowrap">
            <div v-for="(signal, i) in [...liveSignals, ...liveSignals]" :key="i" class="flex items-center gap-3">
              <span class="text-[10px] font-mono text-ink-muted">{{ signal }}</span>
              <span class="text-primary/30 text-xs">•</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Section: The Art of Synthesis -->
      <section id="resonance" class="max-w-[1200px] mx-auto px-6 md:px-12 mb-32 grid grid-cols-1 md:grid-cols-2 gap-20 items-center">
        <div>
          <span class="eyebrow text-primary mb-4 block">{{ t.synthesis.eyebrow }}</span>
          <h2 class="display-lg mb-8 whitespace-pre-line">{{ t.synthesis.title }}</h2>
          <div class="prose text-ink-muted body-lg">
            <p class="mb-6">{{ t.synthesis.p1 }}</p>
            <p>{{ t.synthesis.p2 }}</p>
          </div>
        </div>
        
        <div class="grid grid-cols-2 gap-4">
          <div @click="$router.push('/app')" class="bg-surface-1 border border-hairline p-6 rounded-2xl h-40 flex flex-col justify-between cursor-pointer hover:border-primary/40 hover:bg-surface-2 transition-all group/card">
            <div class="flex justify-between items-start">
              <Globe class="w-6 h-6 text-primary/40 group-hover/card:text-primary transition-colors" />
              <div class="text-[8px] font-bold px-2 py-0.5 rounded bg-primary/10 text-primary border border-primary/20">LIVE</div>
            </div>
            <div>
              <p class="text-[10px] font-black uppercase text-ink-muted mb-1">{{ t.synthesis.f1 }}</p>
              <p class="text-[9px] text-ink-subtle leading-tight">{{ t.synthesis.f1_sub }}</p>
            </div>
          </div>
          
          <div @click="$router.push('/app')" class="bg-surface-2 border border-hairline p-6 rounded-2xl h-40 flex flex-col justify-between translate-y-8 cursor-pointer hover:border-primary/40 hover:bg-surface-1 transition-all group/card">
            <div class="flex justify-between items-start">
              <Search class="w-6 h-6 text-primary/40 group-hover/card:text-primary transition-colors" />
              <div class="text-[8px] font-bold px-2 py-0.5 rounded bg-white/5 text-ink-subtle">99.9%</div>
            </div>
            <div>
              <p class="text-[10px] font-black uppercase text-ink-muted mb-1">{{ t.synthesis.f2 }}</p>
              <p class="text-[9px] text-ink-subtle leading-tight">{{ t.synthesis.f2_sub }}</p>
            </div>
          </div>

          <div @click="$router.push('/app')" class="bg-surface-1 border border-hairline p-6 rounded-2xl h-40 flex flex-col justify-between cursor-pointer hover:border-primary/40 hover:bg-surface-2 transition-all group/card">
            <div class="flex justify-between items-start">
              <Zap class="w-6 h-6 text-primary group-hover/card:scale-110 transition-transform" />
              <div class="text-[8px] font-bold px-2 py-0.5 rounded bg-primary/20 text-white">AI</div>
            </div>
            <div>
              <p class="text-[10px] font-black uppercase text-ink-muted mb-1">{{ t.synthesis.f3 }}</p>
              <p class="text-[9px] text-ink-subtle leading-tight">{{ t.synthesis.f3_sub }}</p>
            </div>
          </div>

          <div @click="$router.push('/app')" class="bg-surface-2 border border-hairline p-6 rounded-2xl h-40 flex flex-col justify-between translate-y-8 cursor-pointer hover:border-primary/40 hover:bg-surface-1 transition-all group/card">
            <div class="flex justify-between items-start">
              <ShieldCheck class="w-6 h-6 text-primary/40 group-hover/card:text-primary transition-colors" />
              <div class="text-[8px] font-bold px-2 py-0.5 rounded bg-white/5 text-ink-subtle">AUTO</div>
            </div>
            <div>
              <p class="text-[10px] font-black uppercase text-ink-muted mb-1">{{ t.synthesis.f4 }}</p>
              <p class="text-[9px] text-ink-subtle leading-tight">{{ t.synthesis.f4_sub }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Section: Craft & Terminal -->
      <section id="curation" class="max-w-[1000px] mx-auto px-6 md:px-12 mb-32">
        <div class="bg-surface-1 border border-hairline rounded-3xl overflow-hidden shadow-2xl">
          <div class="h-12 bg-midnight/80 border-b border-hairline flex items-center px-6 gap-2">
            <div class="w-2.5 h-2.5 rounded-full bg-red-500/20 border border-red-500/30"></div>
            <div class="w-2.5 h-2.5 rounded-full bg-yellow-500/20 border border-yellow-500/30"></div>
            <div class="w-2.5 h-2.5 rounded-full bg-green-500/20 border border-green-500/30"></div>
            <span class="ml-4 text-[9px] font-mono text-ink-subtle uppercase tracking-widest">nexus_engine --verbose</span>
          </div>
          <div class="p-8 font-mono text-xs leading-relaxed">
            <p class="text-ink-muted mb-2"><span class="text-primary">system:</span> {{ t.craft.status }}</p>
            <p class="text-ink-muted mb-2"><span class="text-primary">source:</span> {{ t.craft.source }}</p>
            <p class="text-emerald-500 mb-2">success: {{ t.craft.success }}</p>
            <p class="text-ink-muted mb-2"><span class="text-primary">ai:</span> {{ t.craft.ai_route }}</p>
            <p class="text-ink-muted mb-2"><span class="text-primary">cluster:</span> {{ t.craft.cluster }}</p>
            <p class="text-ink animate-pulse underline mt-4 cursor-pointer" @click="$router.push('/reports-list')">{{ t.craft.ready }}</p>
          </div>
        </div>
      </section>

      <!-- Section: Narrative Style -->
      <section id="narrative" class="max-w-[1200px] mx-auto px-6 md:px-12 mb-32 text-center">
        <span class="eyebrow text-primary mb-4 block">{{ t.narrative.eyebrow }}</span>
        <h2 class="display-lg mb-12 whitespace-pre-line">{{ t.narrative.title }}</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div class="bg-surface-1 border border-hairline p-8 rounded-3xl text-left">
            <h4 class="text-xs font-black uppercase text-orange-500 mb-4 tracking-widest">{{ t.narrative.toxic }}</h4>
            <p class="text-sm font-serif italic text-ink leading-relaxed">
              {{ t.narrative.toxic_p }}
            </p>
          </div>
          <div class="bg-surface-1 border border-hairline p-8 rounded-3xl text-left">
            <h4 class="text-xs font-black uppercase text-blue-400 mb-4 tracking-widest">{{ t.narrative.official }}</h4>
            <p class="text-sm text-ink-muted leading-relaxed">
              {{ t.narrative.official_p }}
            </p>
          </div>
        </div>
      </section>

      <!-- Final CTA -->
      <section class="text-center py-32 border-t border-hairline relative overflow-hidden">
        <div class="absolute inset-0 bg-primary/5 blur-[120px] rounded-full translate-y-32"></div>
        <h2 class="display-lg text-ink mb-12 relative z-10 whitespace-pre-line">{{ t.footer.cta }}</h2>
        <router-link to="/app" class="button-cta-large relative z-10">
          {{ t.footer.cta_btn }} <ArrowRight class="w-6 h-6" />
        </router-link>
      </section>
    </main>

    <!-- Footer -->
    <footer class="bg-midnight border-t border-hairline py-16 px-6 md:px-12 flex flex-col md:flex-row justify-between items-center gap-10">
      <router-link to="/" class="flex items-center gap-3 hover:opacity-80 transition-opacity">
        <Zap class="w-6 h-6 text-primary" />
        <span class="logo-text text-xl font-black uppercase text-ink">Nexus AI</span>
      </router-link>
      <div class="flex items-center gap-10 text-[10px] font-black uppercase tracking-[0.2em] text-ink-subtle">
        <a href="https://github.com/easycheaplife/ai-news-nexus" target="_blank" class="hover:text-primary transition-colors">{{ t.footer.github }}</a>
        <a href="https://github.com/easycheaplife/ai-news-nexus/blob/main/docs/api.md" target="_blank" class="hover:text-primary transition-colors">{{ t.footer.docs }}</a>
        <a href="https://github.com/easycheaplife/ai-news-nexus/tree/main/docs/specs" target="_blank" class="hover:text-primary transition-colors">{{ t.footer.guide }}</a>
        <span class="opacity-30">© 2026</span>
      </div>
    </footer>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&family=Inter:wght@400;700;900&display=swap');

.magazine-landing {
  background-color: #050505; /* Midnight */
  color: #F5F5F5; /* Ink */
  font-family: 'Inter', sans-serif;
  overflow-x: hidden;
}

/* Typography Scale */
.display-xl {
  font-family: 'Playfair Display', serif;
  font-size: clamp(40px, 6vw, 72px);
  font-weight: 900;
  letter-spacing: -0.04em;
}

.display-lg {
  font-family: 'Playfair Display', serif;
  font-size: clamp(28px, 4vw, 48px);
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.1;
}

.display-md {
  font-family: 'Playfair Display', serif;
  font-size: clamp(24px, 3vw, 36px);
  font-weight: 700;
}

.card-title {
  font-family: 'Playfair Display', serif;
  font-size: 22px;
  font-weight: 700;
  color: #F5F5F5;
}

.eyebrow {
  font-size: 10px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.25em;
  color: #94a3b8;
}

.body-lg {
  font-size: 18px;
  line-height: 1.6;
  color: #94a3b8;
}

/* Colors & Surfaces */
.bg-midnight { background-color: #050505; }
.bg-surface-1 { background-color: #0d0d0d; }
.bg-surface-2 { background-color: #141414; }
.border-hairline { border-color: rgba(255, 255, 255, 0.08); }
.text-ink { color: #F5F5F5; }
.text-ink-muted { color: #94a3b8; }
.text-ink-subtle { color: #64748b; }
.text-primary { color: #6366f1; }

/* Header & Links */
header.scrolled {
  background-color: rgba(5, 5, 5, 0.8);
  backdrop-filter: blur(20px);
  height: 70px;
}

.nav-link {
  font-size: 10px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: #94a3b8;
  transition: color 0.3s;
}
.nav-link:hover { color: #F5F5F5; }

/* Buttons */
.button-cta {
  background-color: #F5F5F5;
  color: #050505;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s;
}
.button-cta:hover {
  background-color: #6366f1;
  color: #ffffff;
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(99, 102, 241, 0.3);
}

.button-cta-large {
  background-color: #F5F5F5;
  color: #050505;
  padding: 20px 48px;
  border-radius: 12px;
  font-size: 18px;
  font-weight: 900;
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 0 auto;
  width: fit-content;
  transition: all 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
}
.button-cta-large:hover {
  transform: scale(1.05);
  background-color: #6366f1;
  color: #ffffff;
  box-shadow: 0 0 80px rgba(99, 102, 241, 0.4);
}

/* Animations */
@keyframes ticker {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

.ticker-content {
  animation: ticker 60s linear infinite;
}

@keyframes slide-up {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-slide-up { animation: slide-up 1s cubic-bezier(0.2, 0.8, 0.2, 1) forwards; }

/* Responsive Grid Adjustments */
@media (max-width: 1024px) {
  .ticker-content { animation-duration: 30s; }
}
</style>
