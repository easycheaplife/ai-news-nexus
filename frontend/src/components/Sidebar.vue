<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { 
  Users, 
  Search, 
  Activity, 
  Trash2, 
  TrendingUp, 
  Star,
  ShieldAlert,
  Flame,
  Zap,
  X
} from 'lucide-vue-next';
import axios from 'axios';

const props = defineProps<{
  apiUrl: string;
  isOpen?: boolean;
}>();

const emit = defineEmits(['filter-author', 'filter-keyword', 'close']);

const targets = ref<any[]>([]);
const discoveryItems = ref<any[]>([]);
const loading = ref(true);

const fetchSidebarData = async () => {
  loading.value = true;
  try {
    const [targetsRes, discoveryRes] = await Promise.all([
      axios.get(`${props.apiUrl}/targets/`, { params: { is_active: true } }),
      axios.get(`${props.apiUrl}/discovery/`, { params: { status: 'pending' } })
    ]);
    
    // 按评分排序取 Top 10
    targets.value = targetsRes.data
      .sort((a: any, b: any) => (b.avg_score || 0) - (a.avg_score || 0))
      .slice(0, 15);
      
    discoveryItems.value = discoveryRes.data.slice(0, 10);
  } catch (err) {
    console.error('Failed to fetch sidebar data', err);
  } finally {
    loading.value = false;
  }
};

const blacklistTarget = async (target: any) => {
  const confirmMsg = `确定要屏蔽 @${target.handle} 吗？\n\n屏蔽后：\n1. 立即停止采集该账号\n2. 发现引擎将不再自动收录此人`;
  if (!confirm(confirmMsg)) return;
  
  try {
    await axios.patch(`${props.apiUrl}/targets/${target.id}`, {
      is_active: false,
      status: 'blacklisted',
      description: (target.description || '') + ' [Manual Blacklisted]'
    });
    // 从左侧列表移除
    targets.value = targets.value.filter(t => t.id !== target.id);
  } catch (err) {
    console.error('Failed to blacklist target', err);
    alert('屏蔽失败');
  }
};

onMounted(fetchSidebarData);

const getStatusColor = (status: string) => {
  switch (status) {
    case 'active': return 'bg-blue-500';
    case 'probation': return 'bg-purple-500';
    default: return 'bg-slate-500';
  }
};
</script>

<template>
  <aside 
    class="flex flex-col overflow-y-auto no-scrollbar gap-6 fixed top-0 left-0 h-[100dvh] w-72 bg-[#1a1a20] z-[60] p-6 shadow-2xl border-r border-white/10 transition-transform duration-300 ease-in-out lg:relative lg:h-[calc(100vh-88px)] lg:sticky lg:top-[88px] lg:bg-[#0a0a0c]/50 lg:backdrop-blur-xl lg:p-4 lg:pt-6 lg:border-white/5 lg:shadow-none lg:z-auto"
    :class="isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'"
  >
    <!-- Mobile Header & Close Button -->
    <div class="flex items-center justify-between lg:hidden mb-2">
      <div class="flex items-center gap-2">
        <Zap class="w-4 h-4 text-primary" />
        <span class="text-sm font-black text-white uppercase tracking-widest">情报雷达</span>
      </div>
      <button @click="emit('close')" class="p-2 text-text-muted hover:text-white bg-white/5 rounded-lg active:scale-95 transition-all">
        <X class="w-4 h-4" />
      </button>
    </div>
    
    <!-- 1. System Pulse (Simplified for now) -->
    <section>
      <div class="flex items-center gap-2 mb-4 px-2">
        <Activity class="w-4 h-4 text-primary" />
        <h3 class="text-[10px] font-black uppercase tracking-widest text-white/50">系统脉冲 · System Pulse</h3>
      </div>
      <div class="grid grid-cols-2 gap-2">
        <div class="bg-white/5 rounded-xl p-2 flex items-center gap-2 border border-white/5">
          <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
          <span class="text-[10px] font-bold">Scraper OK</span>
        </div>
        <div class="bg-white/5 rounded-xl p-2 flex items-center gap-2 border border-white/5">
          <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
          <span class="text-[10px] font-bold">AI Node OK</span>
        </div>
      </div>
    </section>

    <!-- 2. Inner Circle (KOLs) -->
    <section>
      <div class="flex items-center justify-between mb-4 px-2">
        <div class="flex items-center gap-2">
          <Users class="w-4 h-4 text-blue-400" />
          <h3 class="text-[10px] font-black uppercase tracking-widest text-white/50">核心圈 · Inner Circle</h3>
        </div>
        <span class="text-[9px] bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded font-bold">{{ targets.length }}</span>
      </div>
      
      <div class="space-y-1">
        <div 
          v-for="target in targets" 
          :key="target.id"
          class="group flex items-center justify-between p-2 rounded-xl hover:bg-white/5 transition-all cursor-pointer border border-transparent hover:border-white/5"
          @click="emit('filter-author', target.handle)"
        >
          <div class="flex items-center gap-3 overflow-hidden">
            <div class="relative flex-shrink-0">
              <div class="w-8 h-8 rounded-full bg-gradient-to-br from-slate-800 to-slate-900 flex items-center justify-center border border-white/10">
                <span class="text-[10px] font-bold text-white/50 uppercase">{{ target.handle[0] }}</span>
              </div>
              <div 
                class="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-[#0a0a0c]"
                :class="getStatusColor(target.status)"
              ></div>
            </div>
            <div class="flex flex-col overflow-hidden">
              <span class="text-xs font-bold text-slate-300 truncate">@{{ target.handle }}</span>
              <div class="flex items-center gap-2">
                <div class="h-1 w-12 bg-white/5 rounded-full overflow-hidden">
                  <div class="h-full bg-primary" :style="{ width: `${target.avg_score}%` }"></div>
                </div>
                <span class="text-[9px] font-black text-primary">{{ target.avg_score }}</span>
              </div>
            </div>
          </div>
          
          <div class="flex items-center gap-1">
            <Flame v-if="target.avg_score >= 90" class="w-3 h-3 text-orange-500" />
            <button 
              @click.stop="blacklistTarget(target)"
              class="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-500/20 hover:text-red-500 rounded-lg transition-all"
              title="拉黑此账号"
            >
              <Trash2 class="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- 3. Discovery Radar -->
    <section>
      <div class="flex items-center gap-2 mb-4 px-2">
        <Search class="w-4 h-4 text-purple-400" />
        <h3 class="text-[10px] font-black uppercase tracking-widest text-white/50">发现雷达 · Discovery</h3>
      </div>
      
      <div class="space-y-3">
        <div v-if="discoveryItems.length === 0" class="px-2 py-4 border border-dashed border-white/10 rounded-xl text-center">
          <span class="text-[10px] text-white/20 font-bold uppercase">正在扫描新信号...</span>
        </div>
        
        <div 
          v-for="item in discoveryItems" 
          :key="item.id"
          class="bg-white/5 border border-white/5 rounded-xl p-3 hover:border-purple-500/30 transition-all cursor-pointer group"
          @click="item.type === 'keyword' ? emit('filter-keyword', item.value) : null"
        >
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <Star v-if="item.type === 'user'" class="w-3 h-3 text-yellow-500" />
              <TrendingUp v-else class="w-3 h-3 text-purple-400" />
              <span class="text-[10px] font-black uppercase text-white/40">{{ item.type }}</span>
            </div>
            <span class="text-[9px] text-white/20">{{ new Date(item.created_at).toLocaleDateString() }}</span>
          </div>
          <p class="text-xs font-bold text-slate-200">
            {{ item.type === 'user' ? '@' : '#' }}{{ item.value }}
          </p>
          <p class="text-[10px] text-white/40 mt-1 line-clamp-1 group-hover:line-clamp-none transition-all">
            {{ item.discovery_reason }}
          </p>
        </div>
      </div>
    </section>

    <!-- 4. Footer Stats -->
    <section class="mt-auto pt-6 border-t border-white/5">
      <div class="flex items-center gap-4 text-center">
        <div class="flex-1">
          <p class="text-[9px] font-black text-white/30 uppercase">Active</p>
          <p class="text-sm font-black text-white">{{ targets.length }}</p>
        </div>
        <div class="w-[1px] h-8 bg-white/5"></div>
        <div class="flex-1">
          <p class="text-[9px] font-black text-white/30 uppercase">Vetting</p>
          <p class="text-sm font-black text-white">{{ discoveryItems.length }}</p>
        </div>
      </div>
    </section>

  </aside>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
