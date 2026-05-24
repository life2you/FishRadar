<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { Activity, Clock3, ScrollText, Trash2 } from 'lucide-vue-next'
import { useLogs } from '@/composables/useLogs'
import { useTasks } from '@/composables/useTasks'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Card, CardContent } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { toast } from '@/components/ui/toast'

const { t } = useI18n()
const { tasks } = useTasks()
const { logs, isAutoRefresh, clearLogs, toggleAutoRefresh, fetchLogs, setTaskId, loadLatest, loadPrevious, isFetchingHistory, hasMoreHistory } = useLogs()
const logContainer = ref<HTMLElement | null>(null)
const autoScroll = ref(true)
const isClearDialogOpen = ref(false)
const selectedTaskId = ref('')
const isPrepending = ref(false)
const lastScrollTop = ref(0)
const lastScrollHeight = ref(0)

const selectedTask = computed(() => tasks.value.find((task) => String(task.id) === selectedTaskId.value) ?? null)
const heroCards = computed(() => [
  {
    icon: Activity,
    label: t('logs.hero.cards.task'),
    value: selectedTask.value?.task_name || t('logs.selectTask'),
    detail: selectedTask.value?.is_running ? t('common.running') : t('common.idle'),
  },
  {
    icon: Clock3,
    label: t('logs.hero.cards.refresh'),
    value: isAutoRefresh.value ? t('logs.autoRefresh') : t('logs.hero.manualRefresh'),
    detail: autoScroll.value ? t('logs.autoScroll') : t('logs.hero.manualScroll'),
  },
  {
    icon: Trash2,
    label: t('logs.hero.cards.clear'),
    value: selectedTaskId.value ? t('logs.dialogTitle') : t('common.empty'),
    detail: selectedTaskId.value ? t('logs.dialogDescription') : t('logs.hero.clearHint'),
  },
])

// Auto-scroll logic
watch(logs, async () => {
  if (isPrepending.value) {
    await nextTick()
    if (logContainer.value) {
      const delta = logContainer.value.scrollHeight - lastScrollHeight.value
      logContainer.value.scrollTop = lastScrollTop.value + delta
    }
    isPrepending.value = false
    return
  }
  if (autoScroll.value) {
    await nextTick()
    scrollToBottom()
  }
})

watch(tasks, (list) => {
  if (!list.length) {
    selectedTaskId.value = ''
    setTaskId(null)
    return
  }
  if (selectedTaskId.value && list.some((task) => String(task.id) === selectedTaskId.value)) {
    return
  }
  const running = list.find((task) => task.is_running)
  const fallback = list[0]
  if (!fallback) {
    selectedTaskId.value = ''
    setTaskId(null)
    return
  }
  selectedTaskId.value = String(running ? running.id : fallback.id)
}, { immediate: true })

watch(selectedTaskId, (taskId) => {
  const resolvedTaskId = taskId ? Number(taskId) : null
  setTaskId(resolvedTaskId)
  if (resolvedTaskId) {
    loadLatest(50)
  }
})

function scrollToBottom() {
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
}

async function handleScroll() {
  if (!logContainer.value) return
  if (!hasMoreHistory.value || isFetchingHistory.value) return
  if (logContainer.value.scrollTop > 120) return
  lastScrollTop.value = logContainer.value.scrollTop
  lastScrollHeight.value = logContainer.value.scrollHeight
  isPrepending.value = true
  await loadPrevious(50)
}

function openClearDialog() {
  isClearDialogOpen.value = true
}

async function handleClearLogs() {
  try {
    await clearLogs()
    toast({ title: t('logs.logsCleared') })
  } catch (e) {
    toast({
      title: t('logs.clearFailed'),
      description: (e as Error).message,
      variant: 'destructive',
    })
  } finally {
    isClearDialogOpen.value = false
  }
}
</script>

<template>
  <div class="flex h-[calc(100vh-100px)] flex-col gap-4">
    <section class="overflow-hidden rounded-[32px] border border-slate-200/80 bg-[linear-gradient(135deg,#0a1220_0%,#162537_42%,#dbe6f2_220%)] px-6 py-7 text-white shadow-[0_28px_90px_rgba(15,23,42,0.18)] md:px-8">
      <div class="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
        <div class="max-w-3xl">
          <p class="text-xs font-black uppercase tracking-[0.32em] text-slate-300">CatchYu Console</p>
          <h1 class="mt-3 flex items-center gap-3 text-3xl font-black tracking-tight text-white md:text-4xl">
            <ScrollText class="h-8 w-8 text-[#9fd3ff]" />
            {{ t('logs.title') }}
          </h1>
          <p class="mt-3 max-w-2xl text-sm leading-7 text-slate-300 md:text-base">{{ t('logs.description') }}</p>
        </div>
        <div class="rounded-[28px] border border-white/10 bg-white/10 px-5 py-4 backdrop-blur xl:max-w-sm">
          <p class="text-xs font-black uppercase tracking-[0.24em] text-slate-400">{{ t('logs.hero.panelLabel') }}</p>
          <p class="mt-2 text-sm leading-7 text-slate-200">{{ t('logs.hero.panelDescription') }}</p>
        </div>
      </div>

      <div class="mt-6 grid gap-3 lg:grid-cols-[minmax(0,1fr)_auto]">
        <div class="grid gap-3 md:grid-cols-3">
          <article
            v-for="card in heroCards"
            :key="card.label"
            class="rounded-[24px] border border-white/10 bg-white/10 p-4 backdrop-blur"
          >
            <component :is="card.icon" class="h-5 w-5 text-[#a6d0ff]" />
            <p class="mt-4 text-xs font-black uppercase tracking-[0.22em] text-slate-400">{{ card.label }}</p>
            <p class="mt-3 text-lg font-black text-white">{{ card.value }}</p>
            <p class="mt-2 text-sm leading-6 text-slate-300">{{ card.detail }}</p>
          </article>
        </div>
        <div class="rounded-[24px] border border-white/10 bg-white/10 p-4 backdrop-blur">
          <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
              <Label class="text-sm text-slate-300">{{ t('logs.task') }}</Label>
              <Select v-model="selectedTaskId">
                <SelectTrigger class="w-full border-white/10 bg-white/10 text-white sm:w-[260px]">
                  <SelectValue :placeholder="t('logs.selectTask')" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="task in tasks" :key="task.id" :value="String(task.id)">
                    {{ task.task_name }}{{ task.is_running ? t('logs.taskRunningSuffix') : '' }}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button variant="outline" size="sm" class="border-white/15 bg-white/5 text-white hover:bg-white/10" :disabled="!selectedTaskId" @click="fetchLogs">
              {{ t('common.refresh') }}
            </Button>
            <Button variant="destructive" size="sm" :disabled="!selectedTaskId" @click="openClearDialog">
              {{ t('logs.clearLogs') }}
            </Button>
          </div>

          <div class="mt-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
            <div class="flex items-center space-x-2">
              <Switch id="auto-refresh" :model-value="isAutoRefresh" @update:model-value="toggleAutoRefresh" />
              <Label for="auto-refresh" class="text-slate-200">{{ t('logs.autoRefresh') }}</Label>
            </div>

            <div class="flex items-center space-x-2">
              <Switch id="auto-scroll" v-model="autoScroll" />
              <Label for="auto-scroll" class="text-slate-200">{{ t('logs.autoScroll') }}</Label>
            </div>
          </div>
        </div>
      </div>
    </section>

    <Card class="app-surface flex flex-1 flex-col overflow-hidden border-none">
      <CardContent class="flex-1 p-0 relative">
        <pre
          ref="logContainer"
          @scroll="handleScroll"
          class="absolute inset-0 p-4 bg-gray-950 text-gray-100 font-mono text-sm overflow-auto whitespace-pre-wrap break-all"
        >{{ logs }}</pre>
      </CardContent>
    </Card>

    <Dialog v-model:open="isClearDialogOpen">
      <DialogContent class="sm:max-w-[420px]">
        <DialogHeader>
          <DialogTitle>{{ t('logs.dialogTitle') }}</DialogTitle>
          <DialogDescription>
            {{ t('logs.dialogDescription') }}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="isClearDialogOpen = false">{{ t('common.cancel') }}</Button>
          <Button variant="destructive" @click="handleClearLogs">{{ t('logs.confirmClear') }}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
