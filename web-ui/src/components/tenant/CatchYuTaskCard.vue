<script setup lang="ts">
import { computed, toRefs } from 'vue'
import {
  Bot,
  CirclePlay,
  Clock3,
  Eye,
  MapPin,
  PauseCircle,
  Pencil,
  RotateCcw,
  ScanSearch,
  ShieldCheck,
  Trash2,
} from 'lucide-vue-next'
import type { Task } from '@/types/task.d.ts'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'

const props = defineProps<{
  task: Task
  isStopping?: boolean
}>()
const { task, isStopping } = toRefs(props)

const emit = defineEmits<{
  (e: 'run', taskId: number): void
  (e: 'stop', taskId: number): void
  (e: 'edit', task: Task): void
  (e: 'delete', taskId: number): void
  (e: 'refresh-criteria', task: Task): void
  (e: 'toggle-enabled', payload: { task: Task; enabled: boolean }): void
}>()

const decisionModeLabel = computed(() => props.task.decision_mode === 'keyword' ? '关键词模式' : 'AI 模式')
const decisionModeTone = computed(() =>
  props.task.decision_mode === 'keyword'
    ? 'border-[#d7e4d8] bg-[#eef6ef] text-[#355943]'
    : 'border-[#edd9c7] bg-[#fbefe1] text-[#8f4e1f]'
)
const scheduleLabel = computed(() => props.task.cron || '手动触发')
const scheduleTone = computed(() => props.task.cron ? '已设置频率' : '随时启动')
const statusTone = computed(() => {
  if (props.task.is_running) {
    return {
      dot: 'bg-[#3d7d58]',
      label: '扫描进行中',
      shell: 'border-[#dce9df] bg-[#edf6ef] text-[#325341]',
    }
  }
  if (props.task.enabled) {
    return {
      dot: 'bg-[#c27f2b]',
      label: '待命中',
      shell: 'border-[#eadcc7] bg-[#fbf4e8] text-[#7e5d37]',
    }
  }
  return {
    dot: 'bg-[#8a8177]',
    label: '已暂停',
    shell: 'border-[#e6dfd7] bg-[#f7f2ec] text-[#71675d]',
  }
})
const tags = computed(() => {
  const values: string[] = []
  if (props.task.personal_only) values.push('仅个人卖家')
  if (props.task.free_shipping) values.push('包邮优先')
  if (props.task.region) values.push(props.task.region)
  if (props.task.keyword_rules?.length) values.push(`${props.task.keyword_rules.length} 条关键词规则`)
  return values.slice(0, 4)
})
const priceRange = computed(() => {
  const min = props.task.min_price
  const max = props.task.max_price
  if (!min && !max) return '不限价格'
  if (min && max) return `¥${min} - ¥${max}`
  if (min) return `¥${min} 起`
  return `最高 ¥${max}`
})
</script>

<template>
  <article class="group rounded-[30px] border border-[#eadfce] bg-[linear-gradient(180deg,rgba(255,251,244,0.96)_0%,rgba(252,248,241,0.98)_100%)] p-5 shadow-[0_24px_60px_rgba(77,56,35,0.08)] transition-transform duration-300 hover:-translate-y-1">
    <div class="flex flex-col gap-5">
      <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div class="min-w-0 space-y-3">
          <div class="flex flex-wrap items-center gap-2">
            <span class="inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-bold" :class="statusTone.shell">
              <span class="h-2.5 w-2.5 rounded-full" :class="statusTone.dot"></span>
              {{ statusTone.label }}
            </span>
            <span class="inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-bold" :class="decisionModeTone">
              <Bot v-if="task.decision_mode === 'ai'" class="h-3.5 w-3.5" />
              <ScanSearch v-else class="h-3.5 w-3.5" />
              {{ decisionModeLabel }}
            </span>
          </div>

          <div>
            <h3 class="line-clamp-2 text-[1.45rem] font-black tracking-[-0.04em] text-[#241a12]">
              {{ task.task_name }}
            </h3>
            <p class="mt-2 text-sm font-semibold text-[#7a6046]">
              关键词：{{ task.keyword }}
            </p>
            <p v-if="task.description" class="mt-3 line-clamp-3 text-sm leading-7 text-[#5f4d3d]">
              {{ task.description }}
            </p>
          </div>
        </div>

        <div class="flex items-center gap-3 self-start rounded-full border border-[#e4d8c7] bg-white/80 px-4 py-2 shadow-sm">
          <div class="text-right">
            <p class="text-[11px] font-bold uppercase tracking-[0.22em] text-[#a0886f]">启用状态</p>
            <p class="mt-1 text-sm font-semibold text-[#332419]">{{ task.enabled ? '参与调度' : '暂停调度' }}</p>
          </div>
          <Switch :model-value="task.enabled" @update:model-value="(value) => emit('toggle-enabled', { task, enabled: value === true })" />
        </div>
      </div>

      <div class="grid gap-3 md:grid-cols-3">
        <div class="rounded-[24px] border border-white/90 bg-white/84 p-4 shadow-sm">
          <p class="text-[11px] font-bold uppercase tracking-[0.22em] text-[#9b8165]">执行频率</p>
          <p class="mt-3 flex items-center gap-2 text-sm font-semibold text-[#2e2117]">
            <Clock3 class="h-4 w-4 text-[#c6582e]" />
            {{ scheduleTone }}
          </p>
          <p class="mt-2 text-sm leading-6 text-[#6a5744]">{{ scheduleLabel }}</p>
        </div>

        <div class="rounded-[24px] border border-white/90 bg-white/84 p-4 shadow-sm">
          <p class="text-[11px] font-bold uppercase tracking-[0.22em] text-[#9b8165]">价格范围</p>
          <p class="mt-3 text-lg font-black tracking-[-0.03em] text-[#2b1d13]">
            {{ priceRange }}
          </p>
          <p class="mt-2 text-sm leading-6 text-[#6a5744]">搜索页数 {{ task.max_pages || 0 }} 页</p>
        </div>

        <div class="rounded-[24px] border border-white/90 bg-white/84 p-4 shadow-sm">
          <p class="text-[11px] font-bold uppercase tracking-[0.22em] text-[#9b8165]">筛选偏好</p>
          <div class="mt-3 flex flex-wrap gap-2">
            <span
              v-for="tag in tags"
              :key="tag"
              class="inline-flex items-center gap-1 rounded-full border border-[#e7ddce] bg-[#faf4eb] px-3 py-1 text-xs font-semibold text-[#694f39]"
            >
              <MapPin v-if="tag === task.region" class="h-3 w-3" />
              <ShieldCheck v-else-if="tag === '仅个人卖家'" class="h-3 w-3" />
              <Eye v-else class="h-3 w-3" />
              {{ tag }}
            </span>
            <span v-if="tags.length === 0" class="text-sm text-[#7d6b57]">当前没有附加筛选项</span>
          </div>
        </div>
      </div>

      <div class="flex flex-wrap gap-3 border-t border-[#eee5d8] pt-4">
        <Button
          v-if="!task.is_running"
          class="rounded-full bg-[#21160f] px-5 text-white hover:bg-[#332117]"
          @click="emit('run', task.id)"
        >
          <CirclePlay class="mr-2 h-4 w-4" />
          立即启动
        </Button>
        <Button
          v-else
          variant="outline"
          class="rounded-full border-[#c6582e]/30 bg-[#fff5ef] px-5 text-[#a24b26] hover:bg-[#fff1e6]"
          :disabled="isStopping"
          @click="emit('stop', task.id)"
        >
          <PauseCircle class="mr-2 h-4 w-4" />
          {{ isStopping ? '停止中...' : '停止任务' }}
        </Button>
        <Button variant="outline" class="rounded-full border-[#ddcfbc] bg-white/80 px-5 text-[#473122] hover:bg-white" @click="emit('edit', task)">
          <Pencil class="mr-2 h-4 w-4" />
          编辑
        </Button>
        <Button
          v-if="task.decision_mode === 'ai'"
          variant="outline"
          class="rounded-full border-[#d6e1d8] bg-[#edf6ef] px-5 text-[#355943] hover:bg-[#e4f1e7]"
          @click="emit('refresh-criteria', task)"
        >
          <RotateCcw class="mr-2 h-4 w-4" />
          重刷 AI 标准
        </Button>
        <Button
          variant="outline"
          class="rounded-full border-[#f1d7d0] bg-[#fff2ef] px-5 text-[#a24b26] hover:bg-[#ffeae5]"
          @click="emit('delete', task.id)"
        >
          <Trash2 class="mr-2 h-4 w-4" />
          删除
        </Button>
      </div>
    </div>
  </article>
</template>
