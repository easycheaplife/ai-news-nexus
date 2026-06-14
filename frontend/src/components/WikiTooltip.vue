<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { TrendingUp, BookOpen, Layers } from 'lucide-vue-next';

const props = defineProps<{
  term: {
    keyword: string;
    category: string;
    description: string;
    heat_score: number;
  }
}>();

const isVisible = ref(false);
const tooltipRef = ref<HTMLElement | null>(null);
const triggerRef = ref<HTMLElement | null>(null);
const position = ref({ top: 0, left: 0 });

const updatePosition = () => {
  if (!triggerRef.value) return;
  const rect = triggerRef.value.getBoundingClientRect();
  
  // 智能定位：优先显示在上方，如果空间不足显示在下方
  const spaceAbove = rect.top;
  const tooltipHeight = 200; // 预估高度
  
  if (spaceAbove > tooltipHeight) {
    position.value = {
      top: rect.top - 10,
      left: rect.left + rect.width / 2
    };
  } else {
    position.value = {
      top: rect.bottom + 10,
      left: rect.left + rect.width / 2
    };
  }
};

const show = () => {
  updatePosition();
  isVisible.value = true;
};

const hide = () => {
  isVisible.value = false;
};

// 监听滚动，防止位置偏移
onMounted(() => {
  window.addEventListener('scroll', updatePosition);
});
onUnmounted(() => {
  window.removeEventListener('scroll', updatePosition);
});
</script>

<template>
  <span class="relative inline-block">
    <span 
      ref="triggerRef"
      @mouseenter="show" 
      @mouseleave="hide"
      class="cursor-help border-b border-dashed border-primary/60 text-primary font-bold hover:text-white hover:bg-primary/20 transition-all px-0.5 rounded-sm"
    >
      <slot></slot>
    </span>

    <!-- Portal-like fixed tooltip -->
    <Teleport to="body">
      <Transition 
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0 translate-y-2 scale-95"
        enter-to-class="opacity-100 translate-y-0 scale-100"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="opacity-100 translate-y-0 scale-100"
        leave-to-class="opacity-0 translate-y-2 scale-95"
      >
        <div 
          v-if="isVisible"
          ref="tooltipRef"
          class="fixed z-[9999] w-72 p-5 bg-[#1a1a20]/95 backdrop-blur-xl border border-white/10 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.5),0_0_20px_rgba(99,102,241,0.2)] -translate-x-1/2"
          :style="{ top: `${position.top}px`, left: `${position.left}px`, transform: `translateX(-50%) ${position.top < 300 ? '' : 'translateY(-100%)'}` }"
        >
          <!-- Header -->
          <div class="flex items-start justify-between mb-3">
            <div class="flex flex-col">
              <div class="flex items-center gap-2 mb-1">
                <BookOpen class="w-3 h-3 text-primary" />
                <span class="text-[9px] font-black text-white/40 uppercase tracking-widest">AI Wiki Term</span>
              </div>
              <h4 class="text-lg font-black text-white leading-none tracking-tight">{{ term.keyword }}</h4>
            </div>
            <div class="bg-primary/10 border border-primary/20 px-2 py-0.5 rounded-md">
               <span class="text-[9px] font-bold text-primary uppercase">{{ term.category }}</span>
            </div>
          </div>

          <!-- Description -->
          <p class="text-xs text-slate-300 leading-relaxed mb-4 italic">
            {{ term.description }}
          </p>

          <!-- Stats Footer -->
          <div class="flex items-center justify-between pt-3 border-t border-white/5">
            <div class="flex items-center gap-2 text-emerald-400">
              <TrendingUp class="w-3 h-3" />
              <span class="text-[10px] font-black uppercase">Resonance Pulse</span>
            </div>
            <div class="text-[11px] font-black text-white">
              {{ term.heat_score }} <span class="text-white/20">pts</span>
            </div>
          </div>

          <!-- Arrow -->
          <div 
            class="absolute left-1/2 -translate-x-1/2 w-3 h-3 bg-[#1a1a20] border-r border-b border-white/10 rotate-45"
            :class="position.top < 300 ? '-top-1.5 rotate-[225deg]' : '-bottom-1.5'"
          ></div>
        </div>
      </Transition>
    </Teleport>
  </span>
</template>

<style scoped>
/* 确保 Tooltip 不会被截断 */
</style>
