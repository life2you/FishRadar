<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuth } from '@/composables/useAuth'
import { useTasks } from '@/composables/useTasks'
import type { Task, TaskUpdate } from '@/types/task.d.ts'
import { parseTaskFormDefaults } from '@/lib/taskFormQuery'
import TaskCreateDialog from '@/components/tasks/TaskCreateDialog.vue'
import TasksTable from '@/components/tasks/TasksTable.vue'
import TaskForm from '@/components/tasks/TaskForm.vue'
import TenantPortalHero from '@/components/tenant/TenantPortalHero.vue'
import CatchYuTaskCard from '@/components/tenant/CatchYuTaskCard.vue'
import CatchYuTaskStudioPanel from '@/components/tenant/CatchYuTaskStudioPanel.vue'
import { listAccounts, type AccountItem } from '@/api/accounts'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import { RefreshCw, Sparkles } from 'lucide-vue-next'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
const { t } = useI18n()
const { role, tenantName, username, canUseAi } = useAuth()

const {
  tasks,
  isLoading,
  error,
  fetchTasks,
  removeTask,
  updateTask,
  startTask,
  stopTask,
  stoppingTaskIds,
} = useTasks()
const route = useRoute()

// State for dialogs
const isEditDialogOpen = ref(false)
const isCriteriaDialogOpen = ref(false)
const isEditSubmitting = ref(false)
const selectedTask = ref<Task | null>(null)
const criteriaTask = ref<Task | null>(null)
const criteriaDescription = ref('')
const isCriteriaSubmitting = ref(false)
const isDeleteDialogOpen = ref(false)
const taskToDeleteId = ref<number | null>(null)
const accountOptions = ref<AccountItem[]>([])
const isTenantCreateOpen = ref(false)
const canManageFixedAccounts = computed(() => role.value === 'admin')
const isTenantPortal = computed(() => role.value === 'tenant')
const tenantWorkspaceName = computed(() => tenantName.value || username.value || t('common.unnamed'))
const adminTenantScopeLabel = computed(() => {
  if (role.value !== 'admin') return null
  const raw = route.query.tenant_id
  return typeof raw === 'string' ? raw : null
})
const tenantTaskStats = computed(() => {
  const enabledCount = tasks.value.filter((task) => task.enabled).length
  const runningCount = tasks.value.filter((task) => task.is_running).length
  const keywordCount = tasks.value.filter((task) => task.decision_mode === 'keyword').length
  const scheduledCount = tasks.value.filter((task) => Boolean(task.cron)).length
  return [
    {
      label: t('tenantPortal.tasks.stats.enabled'),
      value: String(enabledCount),
      detail: t('tenantPortal.tasks.details.enabled'),
    },
    {
      label: t('tenantPortal.tasks.stats.running'),
      value: String(runningCount),
      detail: t('tenantPortal.tasks.details.running'),
    },
    {
      label: t('tenantPortal.tasks.stats.keyword'),
      value: String(keywordCount),
      detail: t('tenantPortal.tasks.details.keyword'),
    },
    {
      label: t('tenantPortal.tasks.stats.scheduled'),
      value: String(scheduledCount),
      detail: t('tenantPortal.tasks.details.scheduled'),
    },
  ]
})
const runningTasks = computed(() => tasks.value.filter((task) => task.is_running))
const standbyTasks = computed(() => tasks.value.filter((task) => !task.is_running))

const taskToDelete = computed(() => {
  if (taskToDeleteId.value === null) return null
  return tasks.value.find((task) => task.id === taskToDeleteId.value) || null
})
const editDefaults = computed(() => parseTaskFormDefaults(route.query))

function handleDeleteTask(taskId: number) {
  taskToDeleteId.value = taskId
  isDeleteDialogOpen.value = true
}

async function handleConfirmDeleteTask() {
  if (!taskToDelete.value) {
    toast({ title: t('tasks.toasts.notFound'), variant: 'destructive' })
    isDeleteDialogOpen.value = false
    return
  }
  try {
    await removeTask(taskToDelete.value.id)
    toast({ title: t('tasks.toasts.deleted') })
  } catch (e) {
    toast({
      title: t('tasks.toasts.deleteFailed'),
      description: (e as Error).message,
      variant: 'destructive',
    })
  } finally {
    isDeleteDialogOpen.value = false
    taskToDeleteId.value = null
  }
}

function handleEditTask(task: Task) {
  selectedTask.value = task
  isEditDialogOpen.value = true
}

watch(
  () => [route.query.edit, tasks.value],
  () => {
    const editTaskId = typeof route.query.edit === 'string' ? Number(route.query.edit) : NaN
    if (!Number.isFinite(editTaskId)) return
    const match = tasks.value.find((task) => task.id === editTaskId)
    if (!match) return
    selectedTask.value = match
    isEditDialogOpen.value = true
  },
  { immediate: true }
)

watch(
  () => route.query.create,
  (value) => {
    if (value === '1' && isTenantPortal.value) {
      isTenantCreateOpen.value = true
    }
  },
  { immediate: true }
)

async function handleUpdateTask(data: TaskUpdate) {
  if (!selectedTask.value) return
  isEditSubmitting.value = true
  try {
    await updateTask(selectedTask.value.id, data)
    isEditDialogOpen.value = false
  }
  catch (e) {
    toast({
      title: t('tasks.toasts.updateFailed'),
      description: (e as Error).message,
      variant: 'destructive',
    })
  }
  finally {
    isEditSubmitting.value = false
  }
}

function handleOpenCriteriaDialog(task: Task) {
  criteriaTask.value = task
  criteriaDescription.value = task.description || ''
  isCriteriaDialogOpen.value = true
}

async function handleRefreshCriteria() {
  if (!criteriaTask.value) return
  if (!criteriaDescription.value.trim()) {
    toast({
      title: t('tasks.toasts.descriptionRequired'),
      description: t('tasks.criteria.descriptionRequired'),
      variant: 'destructive',
    })
    return
  }

  isCriteriaSubmitting.value = true
  try {
    await updateTask(criteriaTask.value.id, { description: criteriaDescription.value })
    isCriteriaDialogOpen.value = false
  } catch (e) {
    toast({
      title: t('tasks.toasts.regenerateFailed'),
      description: (e as Error).message,
      variant: 'destructive',
    })
  } finally {
    isCriteriaSubmitting.value = false
  }
}

async function handleStartTask(taskId: number) {
  try {
    await startTask(taskId)
  } catch (e) {
    toast({
      title: t('tasks.toasts.startFailed'),
      description: (e as Error).message,
      variant: 'destructive',
    })
  }
}

async function handleStopTask(taskId: number) {
  try {
    await stopTask(taskId)
  } catch (e) {
    toast({
      title: t('tasks.toasts.stopFailed'),
      description: (e as Error).message,
      variant: 'destructive',
    })
  }
}

async function handleToggleEnabled(task: Task, enabled: boolean) {
  const previous = task.enabled
  task.enabled = enabled
  try {
    await updateTask(task.id, { enabled })
  } catch (e) {
    task.enabled = previous
    toast({
      title: t('tasks.toasts.toggleFailed'),
      description: (e as Error).message,
      variant: 'destructive',
    })
  }
}

async function fetchAccountOptions() {
  if (!canManageFixedAccounts.value) {
    accountOptions.value = []
    return
  }
  try {
    accountOptions.value = await listAccounts()
  } catch (e) {
    toast({
      title: t('tasks.toasts.loadAccountsFailed'),
      description: (e as Error).message,
      variant: 'destructive',
    })
  }
}

onMounted(fetchAccountOptions)
</script>

<template>
  <div>
    <div v-if="isTenantPortal" class="space-y-6">
      <TenantPortalHero
        :eyebrow="t('tenantPortal.eyebrow')"
        :title="t('tenantPortal.tasks.title', { tenant: tenantWorkspaceName })"
        :description="t('tenantPortal.tasks.description')"
        :note="t('tenantPortal.note')"
        :stats="tenantTaskStats"
      >
        <template #actions>
          <Button class="h-12 rounded-full bg-[#21160f] px-6 text-sm font-bold text-white shadow-[0_16px_36px_rgba(33,22,15,0.24)] hover:bg-[#2f2016]" @click="isTenantCreateOpen = true">
            创建监控任务
          </Button>
          <Button
            variant="outline"
            class="h-12 rounded-full border-[#dfd2c1] bg-white/80 px-5 text-[#473122] hover:bg-white"
            :disabled="isLoading"
            @click="fetchTasks"
          >
            <RefreshCw class="mr-2 h-4 w-4" />
            刷新任务
          </Button>
        </template>
      </TenantPortalHero>

      <CatchYuTaskStudioPanel
        v-if="isTenantCreateOpen"
        :account-options="accountOptions"
        :allow-fixed-account="canManageFixedAccounts"
        @created="() => { isTenantCreateOpen = false; fetchTasks() }"
        @cancel="isTenantCreateOpen = false"
      />

      <section class="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div class="space-y-4">
          <div class="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
            <div>
              <p class="text-xs font-black uppercase tracking-[0.26em] text-[#9b8165]">
                {{ t('tenantPortal.eyebrow') }}
              </p>
              <h2 class="mt-2 text-2xl font-black tracking-tight text-[#241a12]">
                {{ t('tenantPortal.tasks.queueTitle') }}
              </h2>
              <p class="mt-2 max-w-3xl text-sm leading-6 text-[#6b5744]">
                {{ t('tenantPortal.tasks.queueDescription') }}
              </p>
            </div>
          </div>

          <div v-if="error" class="app-alert-error mb-4" role="alert">
            <strong class="font-bold">{{ t('common.error') }}</strong>
            <span class="block sm:inline">{{ error.message }}</span>
          </div>

          <div v-if="tasks.length === 0" class="rounded-[32px] border border-dashed border-[#dccfbf] bg-[#fffaf2] px-6 py-14 text-center">
            <p class="text-lg font-bold text-[#4a3627]">还没有 CatchYu 任务</p>
            <p class="mt-2 text-sm text-[#7b6956]">从“创建监控任务”开始，先配置目标商品和抓取策略。</p>
          </div>

          <div v-else class="space-y-4">
            <CatchYuTaskCard
              v-for="task in tasks"
              :key="task.id"
              :task="task"
              :is-stopping="stoppingTaskIds.has(task.id)"
              @delete="handleDeleteTask"
              @edit="handleEditTask"
              @run="handleStartTask"
              @stop="handleStopTask"
              @refresh-criteria="handleOpenCriteriaDialog"
              @toggle-enabled="({ task, enabled }) => handleToggleEnabled(task, enabled)"
            />
          </div>
        </div>

        <aside class="space-y-4">
          <section class="rounded-[30px] border border-[#eadfce] bg-[linear-gradient(180deg,rgba(255,252,246,0.98)_0%,rgba(252,247,239,0.98)_100%)] p-5 shadow-[0_24px_60px_rgba(77,56,35,0.08)]">
            <div class="flex items-center gap-2 text-[#9b8165]">
              <Sparkles class="h-4 w-4" />
              <p class="text-[11px] font-bold uppercase tracking-[0.24em]">运行概况</p>
            </div>
            <div class="mt-4 grid gap-3">
              <article class="rounded-[24px] border border-white/80 bg-white/85 p-4 shadow-sm">
                <p class="text-sm font-bold text-[#2b1d13]">进行中的任务</p>
                <p class="mt-2 text-3xl font-black tracking-[-0.04em] text-[#241a12]">{{ runningTasks.length }}</p>
                <p class="mt-2 text-xs leading-5 text-[#6a5744]">正在抓取或等待完成停止动作的任务会优先显示在这里。</p>
              </article>
              <article class="rounded-[24px] border border-white/80 bg-white/85 p-4 shadow-sm">
                <p class="text-sm font-bold text-[#2b1d13]">待命任务</p>
                <p class="mt-2 text-3xl font-black tracking-[-0.04em] text-[#241a12]">{{ standbyTasks.length }}</p>
                <p class="mt-2 text-xs leading-5 text-[#6a5744]">包括待手动启动和已配置调度规则的监控任务。</p>
              </article>
            </div>
          </section>

          <section class="rounded-[30px] border border-[#eadfce] bg-white/88 p-5 shadow-[0_24px_60px_rgba(77,56,35,0.08)]">
            <p class="text-[11px] font-bold uppercase tracking-[0.24em] text-[#9b8165]">创建提示</p>
            <ul class="mt-4 space-y-3 text-sm leading-6 text-[#5f4d3d]">
              <li>AI 模式会异步生成分析标准，并在创建流程中实时显示进度。</li>
              <li>关键词模式会直接保存并立即可启动，适合明确规则场景。</li>
              <li>任务创建后都可以继续编辑、停用、删除或重新启动。</li>
            </ul>
          </section>
        </aside>
      </section>
    </div>

    <template v-else>
      <div class="mb-6 flex justify-between items-center">
        <div>
          <h1 class="text-2xl font-bold text-gray-800">
            {{ t('tasks.title') }}
          </h1>
          <p v-if="adminTenantScopeLabel" class="mt-1 text-sm text-sky-700">
            {{ t('tenantDetail.scopeHint', { id: adminTenantScopeLabel }) }}
          </p>
        </div>
        <TaskCreateDialog
          :account-options="accountOptions"
          :allow-fixed-account="canManageFixedAccounts"
          @created="fetchTasks"
        />
      </div>

      <div v-if="error" class="app-alert-error mb-4" role="alert">
        <strong class="font-bold">{{ t('common.error') }}</strong>
        <span class="block sm:inline">{{ error.message }}</span>
      </div>

      <TasksTable
        :tasks="tasks"
        :is-loading="isLoading"
        :stopping-ids="stoppingTaskIds"
        @delete-task="handleDeleteTask"
        @edit-task="handleEditTask"
        @run-task="handleStartTask"
        @stop-task="handleStopTask"
        @refresh-criteria="handleOpenCriteriaDialog"
        @toggle-enabled="handleToggleEnabled"
      />
    </template>

    <!-- Edit Task Dialog -->
    <Dialog v-model:open="isEditDialogOpen">
      <DialogContent :class="isTenantPortal ? 'border-[#e7daca] bg-[#fffaf1] shadow-[0_36px_100px_rgba(58,39,20,0.24)] sm:max-w-[820px]' : 'sm:max-w-[640px]'" class="max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{{ t('tasks.editDialog.title', { task: selectedTask?.task_name || "" }) }}</DialogTitle>
        </DialogHeader>
        <TaskForm
          v-if="selectedTask"
          mode="edit"
          :variant="isTenantPortal ? 'tenant' : 'default'"
          :allow-ai-mode="!isTenantPortal || canUseAi"
          :initial-data="selectedTask"
          :account-options="accountOptions"
          :allow-fixed-account="canManageFixedAccounts"
          :default-values="editDefaults"
          @submit="(data) => handleUpdateTask(data as TaskUpdate)"
        />
        <DialogFooter>
          <Button type="submit" form="task-form" :disabled="isEditSubmitting">
            {{ isEditSubmitting ? t('common.saving') : t('tasks.editDialog.save') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Refresh Criteria Dialog -->
    <Dialog v-model:open="isCriteriaDialogOpen">
      <DialogContent class="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>{{ t('tasks.criteria.title') }}</DialogTitle>
          <DialogDescription>
            {{ t('tasks.criteria.description') }}
          </DialogDescription>
        </DialogHeader>
        <div class="grid gap-3">
          <label class="text-sm font-medium text-gray-700">{{ t('tasks.form.description') }}</label>
          <Textarea
            v-model="criteriaDescription"
            class="min-h-[140px]"
            :placeholder="t('tasks.form.descriptionPlaceholder')"
          />
        </div>
        <DialogFooter>
          <Button variant="outline" @click="isCriteriaDialogOpen = false">
            {{ t('common.cancel') }}
          </Button>
          <Button :disabled="isCriteriaSubmitting" @click="handleRefreshCriteria">
            {{ isCriteriaSubmitting ? t('tasks.criteria.generating') : t('tasks.criteria.action') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="isDeleteDialogOpen">
      <DialogContent class="sm:max-w-[420px]">
        <DialogHeader>
          <DialogTitle>{{ t('tasks.deleteDialog.title') }}</DialogTitle>
          <DialogDescription>
            {{ taskToDelete ? t('tasks.deleteDialog.descriptionWithTask', { task: taskToDelete.task_name }) : t('tasks.deleteDialog.descriptionFallback') }}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="isDeleteDialogOpen = false">{{ t('common.cancel') }}</Button>
          <Button variant="destructive" @click="handleConfirmDeleteTask">{{ t('tasks.deleteDialog.confirm') }}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
