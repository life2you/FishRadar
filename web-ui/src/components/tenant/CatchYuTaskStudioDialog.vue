<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { WandSparkles, Compass, Radar } from 'lucide-vue-next'
import { createTaskWithAI } from '@/api/tasks'
import { useTaskGenerationJob } from '@/composables/useTaskGenerationJob'
import type { TaskGenerateRequest } from '@/types/task.d.ts'
import { parseTaskFormDefaults } from '@/lib/taskFormQuery'
import TaskForm from '@/components/tasks/TaskForm.vue'
import TaskGenerationDialog from '@/components/tasks/TaskGenerationDialog.vue'
import { Button } from '@/components/ui/button'
import { toast } from '@/components/ui/toast'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'

const { t } = useI18n()

const props = defineProps<{
  accountOptions?: { name: string; path: string }[]
  allowFixedAccount?: boolean
}>()

const emit = defineEmits<{
  (event: 'created'): void
}>()

const route = useRoute()
const isFormOpen = ref(false)
const isProgressOpen = ref(false)
const isSubmitting = ref(false)
const defaultAccountPath = ref('')
const defaultValues = ref({})
const {
  activeJob,
  pollingError,
  beginPolling,
  clearJob,
} = useTaskGenerationJob()

function resolveAccountPath(accountName: string) {
  const match = (props.accountOptions || []).find((account) => account.name === accountName)
  return match ? match.path : ''
}

async function handleCreateTask(data: TaskGenerateRequest) {
  isSubmitting.value = true
  clearJob()
  try {
    const result = await createTaskWithAI(data)
    if (result.job) {
      isFormOpen.value = false
      isProgressOpen.value = true
      beginPolling(result.job)
      isSubmitting.value = false
      return
    }
    emit('created')
    toast({ title: t('tasks.toasts.created') })
    isFormOpen.value = false
  } catch (error) {
    toast({
      title: t('tasks.toasts.createFailed'),
      description: (error as Error).message,
      variant: 'destructive',
    })
  } finally {
    if (!isProgressOpen.value) {
      isSubmitting.value = false
    }
  }
}

watch(
  () => [route.query, props.accountOptions],
  () => {
    const accountName = typeof route.query.account === 'string' ? route.query.account : ''
    defaultAccountPath.value = accountName ? resolveAccountPath(accountName) : ''
    defaultValues.value = parseTaskFormDefaults(route.query)
    if (route.query.create === '1') {
      isFormOpen.value = true
    }
  },
  { immediate: true }
)

watch(
  () => activeJob.value?.status,
  (status, previousStatus) => {
    if (!status || status === previousStatus) return
    if (status === 'completed') {
      isSubmitting.value = false
      emit('created')
      toast({ title: t('tasks.toasts.created') })
      isProgressOpen.value = false
      clearJob()
      return
    }
    if (status === 'failed') {
      isSubmitting.value = false
      toast({
        title: t('tasks.toasts.createFailed'),
        description: activeJob.value?.error || activeJob.value?.message,
        variant: 'destructive',
      })
    }
  }
)

watch(pollingError, (value) => {
  if (!value) return
  isSubmitting.value = false
  toast({
    title: t('tasks.toasts.progressFailed'),
    description: value.message,
    variant: 'destructive',
  })
})
</script>

<template>
  <Dialog v-model:open="isFormOpen">
    <DialogTrigger as-child>
      <Button class="h-12 rounded-full bg-[#21160f] px-6 text-sm font-bold text-white shadow-[0_16px_36px_rgba(33,22,15,0.24)] hover:bg-[#2f2016]">
        <WandSparkles class="mr-2 h-4 w-4" />
        创建监控任务
      </Button>
    </DialogTrigger>
    <DialogContent class="max-h-[88vh] overflow-y-auto border-[#e7daca] bg-[#fffaf1] p-0 shadow-[0_36px_100px_rgba(58,39,20,0.24)] sm:max-w-[1100px]">
      <div class="grid gap-0 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div class="border-b border-[#eadbc8] px-6 py-6 lg:border-b-0 lg:border-r lg:px-8 lg:py-8">
          <DialogHeader class="space-y-4 text-left">
            <div class="inline-flex w-fit rounded-full border border-[#ddc9ae] bg-white/80 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.28em] text-[#8a6d4e]">
              CatchYu Task Studio
            </div>
            <DialogTitle class="text-3xl font-black tracking-[-0.04em] text-[#23170f]">
              创建新的抓鱼任务
            </DialogTitle>
            <p class="max-w-2xl text-sm leading-7 text-[#685542]">
              用 AI 模式生成分析标准，或直接用关键词模式快速上线。所有配置都会映射到当前租户可用的真实任务接口。
            </p>
          </DialogHeader>

          <div class="mt-6">
            <TaskForm
              mode="create"
              variant="tenant"
              :account-options="accountOptions"
              :allow-fixed-account="allowFixedAccount"
              :default-account="defaultAccountPath"
              :default-values="defaultValues"
              @submit="(data) => handleCreateTask(data as TaskGenerateRequest)"
            />
          </div>
        </div>

        <aside class="bg-[linear-gradient(180deg,#f6eee1_0%,#efe5d7_100%)] px-6 py-6 lg:px-7 lg:py-8">
          <div class="space-y-6">
            <div>
              <p class="text-[11px] font-bold uppercase tracking-[0.24em] text-[#8a6d4e]">创建提示</p>
              <h3 class="mt-3 text-2xl font-black tracking-[-0.03em] text-[#23170f]">
                让任务更快命中真正值得看的商品
              </h3>
            </div>

            <div class="space-y-4">
              <article class="rounded-[26px] border border-white/80 bg-white/78 p-4 shadow-sm">
                <div class="flex items-center gap-3">
                  <div class="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#f1dfc2] text-[#9b5e25]">
                    <Radar class="h-5 w-5" />
                  </div>
                  <div>
                    <p class="text-sm font-bold text-[#2b1d13]">AI 模式</p>
                    <p class="mt-1 text-xs leading-5 text-[#6f5b47]">适合复杂需求，会异步生成分析标准并自动建任务。</p>
                  </div>
                </div>
              </article>

              <article class="rounded-[26px] border border-white/80 bg-white/78 p-4 shadow-sm">
                <div class="flex items-center gap-3">
                  <div class="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#d9e7dc] text-[#35624b]">
                    <Compass class="h-5 w-5" />
                  </div>
                  <div>
                    <p class="text-sm font-bold text-[#2b1d13]">关键词模式</p>
                    <p class="mt-1 text-xs leading-5 text-[#6f5b47]">适合规则清晰的场景，命中任一关键词即可推荐。</p>
                  </div>
                </div>
              </article>
            </div>

            <div class="rounded-[28px] border border-[#dfceb8] bg-[#fffaf2] p-5">
              <p class="text-[11px] font-bold uppercase tracking-[0.24em] text-[#8a6d4e]">执行方式</p>
              <ul class="mt-3 space-y-3 text-sm leading-6 text-[#5d4c3b]">
                <li>支持手动运行，也支持 cron 定时规则。</li>
                <li>支持价格区间、卖家类型、包邮、新发布和区域筛选。</li>
                <li>创建完成后可立即启动、停止、编辑或删除任务。</li>
              </ul>
            </div>
          </div>

          <DialogFooter class="mt-8 block">
            <Button
              type="submit"
              form="task-form"
              class="h-12 w-full rounded-full bg-[#c6582e] text-sm font-bold text-white shadow-[0_18px_40px_rgba(198,88,46,0.28)] hover:bg-[#b34d27]"
              :disabled="isSubmitting"
            >
              {{ isSubmitting ? t('tasks.createDialog.submitting') : '发布 CatchYu 任务' }}
            </Button>
          </DialogFooter>
        </aside>
      </div>
    </DialogContent>
  </Dialog>

  <TaskGenerationDialog
    v-model:open="isProgressOpen"
    :job="activeJob"
  />
</template>
