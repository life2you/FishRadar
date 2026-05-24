<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuth } from '@/composables/useAuth'
import { useResults } from '@/composables/useResults'
import ResultsFilterBar from '@/components/results/ResultsFilterBar.vue'
import ResultsGrid from '@/components/results/ResultsGrid.vue'
import ResultsInsightsPanel from '@/components/results/ResultsInsightsPanel.vue'
import TenantPortalHero from '@/components/tenant/TenantPortalHero.vue'
import CatchYuResultsToolbar from '@/components/tenant/CatchYuResultsToolbar.vue'
import CatchYuResultsInsightsRail from '@/components/tenant/CatchYuResultsInsightsRail.vue'
import CatchYuResultFeed from '@/components/tenant/CatchYuResultFeed.vue'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

const { t } = useI18n()
const { role, tenantName, username } = useAuth()
const route = useRoute()

const {
  files,
  selectedFile,
  results,
  insights,
  filters,
  isLoading,
  error,
  refreshResults,
  exportSelectedResults,
  deleteSelectedFile,
  toggleItemBlock,
  blacklistKeywords,
  isSavingBlacklist,
  saveBlacklistRules,
  fileOptions,
  isFileOptionsReady,
} = useResults()

const isDeleteDialogOpen = ref(false)
const isBlacklistDialogOpen = ref(false)
const blacklistDraft = ref('')
const isTenantPortal = computed(() => role.value === 'tenant')
const tenantWorkspaceName = computed(() => tenantName.value || username.value || t('common.unnamed'))
const adminTenantScopeLabel = computed(() => {
  if (role.value !== 'admin') return null
  const raw = route.query.tenant_id
  return typeof raw === 'string' ? raw : null
})

const selectedTaskLabel = computed(() => {
  if (!selectedFile.value || fileOptions.value.length === 0) return null
  const match = fileOptions.value.find((option) => option.value === selectedFile.value)
  if (!match) return null
  return match.taskName || null
})
const selectedResultHeadline = computed(() => {
  return selectedTaskLabel.value || (selectedFile.value ? selectedFile.value.replace('_full_data.jsonl', '') : '等待选择结果集')
})

const deleteConfirmText = computed(() => {
  return selectedTaskLabel.value
    ? t('results.filters.deleteDialogWithTask', { task: selectedTaskLabel.value })
    : t('results.filters.deleteDialogFallback')
})
const recommendedCount = computed(() => results.value.filter((item) => item.ai_analysis?.is_recommended).length)
const hiddenCount = computed(() => results.value.filter((item) => item._effective_hidden).length)
const tenantResultStats = computed(() => [
  {
    label: t('tenantPortal.results.stats.files'),
    value: String(files.value.length),
    detail: t('tenantPortal.results.details.files'),
  },
  {
    label: t('tenantPortal.results.stats.items'),
    value: String(results.value.length),
    detail: t('tenantPortal.results.details.items'),
  },
  {
    label: t('tenantPortal.results.stats.recommended'),
    value: String(recommendedCount.value),
    detail: t('tenantPortal.results.details.recommended'),
  },
  {
    label: t('tenantPortal.results.stats.hidden'),
    value: String(hiddenCount.value),
    detail: t('tenantPortal.results.details.hidden'),
  },
])

function openDeleteDialog() {
  if (!selectedFile.value) {
    toast({
      title: t('results.filters.noResultToDelete'),
      variant: 'destructive',
    })
    return
  }
  isDeleteDialogOpen.value = true
}

function openBlacklistDialog() {
  if (!selectedFile.value) {
    toast({
      title: t('results.filters.noResultSelected'),
      variant: 'destructive',
    })
    return
  }
  blacklistDraft.value = blacklistKeywords.value.join('\n')
  isBlacklistDialogOpen.value = true
}

function handleExportResults() {
  if (!selectedFile.value) {
    toast({
      title: t('results.filters.noResultToExport'),
      variant: 'destructive',
    })
    return
  }
  exportSelectedResults()
}

async function handleDeleteResults() {
  if (!selectedFile.value) return
  try {
    await deleteSelectedFile(selectedFile.value)
    toast({ title: t('results.filters.resultDeleted') })
  } catch (e) {
    toast({
      title: t('results.filters.deleteFailed'),
      description: (e as Error).message,
      variant: 'destructive',
    })
  } finally {
    isDeleteDialogOpen.value = false
  }
}

function parseBlacklistKeywords(input: string) {
  return input
    .split(/[\n,，]+/)
    .map((item) => item.trim())
    .filter(Boolean)
}

async function handleSaveBlacklistRules() {
  try {
    await saveBlacklistRules(parseBlacklistKeywords(blacklistDraft.value))
    toast({ title: t('results.filters.blacklistSaved') })
    isBlacklistDialogOpen.value = false
  } catch (e) {
    toast({
      title: t('results.filters.blacklistSaveFailed'),
      description: (e as Error).message,
      variant: 'destructive',
    })
  }
}
</script>

<template>
  <div>
    <div v-if="isTenantPortal" class="space-y-6">
      <TenantPortalHero
        :eyebrow="t('tenantPortal.eyebrow')"
        :title="t('tenantPortal.results.title', { tenant: tenantWorkspaceName })"
        :description="t('tenantPortal.results.description')"
        :note="t('tenantPortal.note')"
        :stats="tenantResultStats"
      />

      <section class="space-y-4">
        <div class="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
          <div>
            <p class="text-xs font-black uppercase tracking-[0.26em] text-[#9b8165]">
              {{ t('tenantPortal.eyebrow') }}
            </p>
            <h2 class="mt-2 text-2xl font-black tracking-tight text-[#241a12]">
              {{ t('tenantPortal.results.workspaceTitle') }}
            </h2>
            <p class="mt-2 max-w-3xl text-sm leading-6 text-[#6b5744]">
              {{ t('tenantPortal.results.workspaceDescription') }}
            </p>
          </div>
        </div>

        <div v-if="error" class="app-alert-error mb-4" role="alert">
          <strong class="font-bold">{{ t('common.error') }}</strong>
          <span class="block sm:inline">{{ error.message }}</span>
        </div>

        <CatchYuResultsToolbar
          :files="files"
          :file-options="fileOptions"
          :is-ready="isFileOptionsReady"
          v-model:selectedFile="selectedFile"
          v-model:aiRecommendedOnly="filters.ai_recommended_only"
          v-model:keywordRecommendedOnly="filters.keyword_recommended_only"
          v-model:includeHidden="filters.include_hidden"
          v-model:sortBy="filters.sort_by"
          v-model:sortOrder="filters.sort_order"
          :is-loading="isLoading"
          @refresh="refreshResults"
          @manage-blacklist="openBlacklistDialog"
          @export="handleExportResults"
          @delete="openDeleteDialog"
        />

        <section class="rounded-[30px] border border-[#eadfce] bg-[linear-gradient(135deg,rgba(255,252,246,0.98)_0%,rgba(248,241,230,0.98)_100%)] p-5 shadow-[0_24px_60px_rgba(77,56,35,0.08)]">
          <div class="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
            <div>
              <p class="text-[11px] font-bold uppercase tracking-[0.24em] text-[#9b8165]">当前情报焦点</p>
              <h3 class="mt-3 text-3xl font-black tracking-[-0.04em] text-[#241a12]">{{ selectedResultHeadline }}</h3>
              <p class="mt-3 text-sm leading-7 text-[#6a5744]">
                先从这个结果集里筛掉噪音，再根据推荐状态、黑名单和价格走势判断哪些线索值得继续跟进。
              </p>
            </div>
            <div class="grid gap-3 md:grid-cols-3 lg:grid-cols-1">
              <article class="rounded-[22px] border border-white/85 bg-white/82 p-4 shadow-sm">
                <p class="text-[11px] font-bold uppercase tracking-[0.22em] text-[#9b8165]">结果条目</p>
                <p class="mt-2 text-2xl font-black tracking-[-0.04em] text-[#241a12]">{{ results.length }}</p>
              </article>
              <article class="rounded-[22px] border border-white/85 bg-white/82 p-4 shadow-sm">
                <p class="text-[11px] font-bold uppercase tracking-[0.22em] text-[#9b8165]">推荐占比</p>
                <p class="mt-2 text-2xl font-black tracking-[-0.04em] text-[#241a12]">{{ recommendedCount }}</p>
              </article>
              <article class="rounded-[22px] border border-white/85 bg-white/82 p-4 shadow-sm">
                <p class="text-[11px] font-bold uppercase tracking-[0.22em] text-[#9b8165]">已隐藏</p>
                <p class="mt-2 text-2xl font-black tracking-[-0.04em] text-[#241a12]">{{ hiddenCount }}</p>
              </article>
            </div>
          </div>
        </section>

        <div class="grid gap-4 xl:grid-cols-[minmax(0,1fr)_340px]">
          <CatchYuResultFeed :results="results" :is-loading="isLoading" @toggle-block="toggleItemBlock" />
          <CatchYuResultsInsightsRail
            :insights="insights"
            :selected-task-label="selectedTaskLabel"
            :blacklist-keywords="blacklistKeywords"
            :can-export="Boolean(selectedFile)"
            :can-manage-blacklist="Boolean(selectedFile)"
            @export="handleExportResults"
            @manage-blacklist="openBlacklistDialog"
          />
        </div>
      </section>
    </div>

    <template v-else>
      <h1 class="text-2xl font-bold text-gray-800 mb-6">
        {{ t('results.title') }}
      </h1>
      <div v-if="adminTenantScopeLabel" class="mb-4 rounded-2xl border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-700">
        {{ t('tenantDetail.scopeHint', { id: adminTenantScopeLabel }) }}
      </div>

      <div v-if="error" class="app-alert-error mb-4" role="alert">
        <strong class="font-bold">{{ t('common.error') }}</strong>
        <span class="block sm:inline">{{ error.message }}</span>
      </div>

      <ResultsFilterBar
        :files="files"
        :file-options="fileOptions"
        :is-ready="isFileOptionsReady"
        v-model:selectedFile="selectedFile"
        v-model:aiRecommendedOnly="filters.ai_recommended_only"
        v-model:keywordRecommendedOnly="filters.keyword_recommended_only"
        v-model:includeHidden="filters.include_hidden"
        v-model:sortBy="filters.sort_by"
        v-model:sortOrder="filters.sort_order"
        :is-loading="isLoading"
        @refresh="refreshResults"
        @manage-blacklist="openBlacklistDialog"
        @export="handleExportResults"
        @delete="openDeleteDialog"
      />

      <ResultsInsightsPanel :insights="insights" :selected-task-label="selectedTaskLabel" />

      <ResultsGrid :results="results" :is-loading="isLoading" @toggle-block="toggleItemBlock" />
    </template>

    <Dialog v-model:open="isDeleteDialogOpen">
      <DialogContent class="sm:max-w-[420px]">
        <DialogHeader>
          <DialogTitle>{{ t('results.filters.deleteDialogTitle') }}</DialogTitle>
          <DialogDescription>
            {{ deleteConfirmText }}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="isDeleteDialogOpen = false">{{ t('common.cancel') }}</Button>
          <Button variant="destructive" :disabled="isLoading" @click="handleDeleteResults">
            {{ t('results.filters.confirmDelete') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="isBlacklistDialogOpen">
      <DialogContent class="sm:max-w-[520px]">
        <DialogHeader>
          <DialogTitle>{{ t('results.filters.blacklistDialogTitle') }}</DialogTitle>
          <DialogDescription>
            {{ t('results.filters.blacklistDialogDescription') }}
          </DialogDescription>
        </DialogHeader>
        <div class="space-y-2">
          <label class="text-sm font-medium text-slate-700">
            {{ t('results.filters.blacklistRulesLabel') }}
          </label>
          <Textarea
            v-model="blacklistDraft"
            class="min-h-[180px]"
            :placeholder="t('results.filters.blacklistRulesPlaceholder')"
          />
          <p class="text-xs leading-5 text-slate-500">
            {{ t('results.filters.blacklistRulesHint') }}
          </p>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="isBlacklistDialogOpen = false">{{ t('common.cancel') }}</Button>
          <Button :disabled="isSavingBlacklist" @click="handleSaveBlacklistRules">
            {{ t('results.filters.confirmBlacklistSave') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
