<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useDashboard } from '@/composables/useDashboard'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import Badge from '@/components/ui/badge/Badge.vue'
import PriceTrendChart from '@/components/results/PriceTrendChart.vue'
import { formatNumber, formatRelativeTimeFromNow } from '@/i18n'
import {
  Activity,
  ArrowRight,
  Building2,
  Compass,
  LayoutDashboard,
  Search,
  Settings2,
  Sparkles,
  Target,
  Users,
} from 'lucide-vue-next'

const router = useRouter()
const { t } = useI18n()
const {
  focusInsights,
  focusTask,
  suggestion,
  stats,
  activities,
  isLoading,
  error,
} = useDashboard()

const statCards = computed(() => [
  {
    label: t('dashboard.stats.activeTasks'),
    value: String(stats.value.enabledTasks),
    detail: t('dashboard.stats.runningCount', { count: stats.value.runningTasks }),
    icon: Activity,
    color: 'text-blue-500',
    bg: 'bg-blue-500/10',
  },
  {
    label: t('dashboard.stats.scannedItems'),
    value: formatNumber(stats.value.scannedItems),
    detail: t('dashboard.stats.resultFiles', { count: stats.value.resultFiles }),
    icon: Search,
    color: 'text-emerald-500',
    bg: 'bg-emerald-500/10',
  },
  {
    label: t('dashboard.stats.recommendedItems'),
    value: String(stats.value.recommendedItems),
    detail: t('dashboard.stats.recommendedBreakdown', {
      ai: stats.value.aiRecommendedItems,
      keyword: stats.value.keywordRecommendedItems,
    }),
    icon: Target,
    color: 'text-amber-500',
    bg: 'bg-amber-500/10',
  },
  {
    label: t('dashboard.stats.monitoredTasks'),
    value: String(stats.value.totalTasks),
    detail: t('dashboard.stats.showAllTasks'),
    icon: Compass,
    color: 'text-purple-500',
    bg: 'bg-purple-500/10',
  },
])

const focusTitle = computed(() => focusTask.value?.task_name || t('dashboard.focus.defaultTitle'))
const focusMeta = computed(() => {
  if (!focusTask.value) return t('dashboard.focus.empty')
  const keyword = focusTask.value.keyword || t('dashboard.focus.missingKeyword')
  const count = focusTask.value.total_items
  return t('dashboard.focus.meta', { keyword, count })
})

const insightCards = computed(() => {
  const market = focusInsights.value?.market_summary
  const history = focusInsights.value?.history_summary
  return [
    {
      label: t('results.insights.currentAvg'),
      value: market?.avg_price ? `¥${market.avg_price}` : '—',
      hint: market
        ? t('results.insights.sampleCount', { count: market.sample_count })
        : t('results.grid.empty'),
    },
    {
      label: t('results.insights.historyAvg'),
      value: history?.avg_price ? `¥${history.avg_price}` : '—',
      hint: history
        ? t('results.insights.uniqueItems', { count: history.unique_items })
        : t('results.insights.noSnapshot'),
    },
    {
      label: t('results.card.marketAvg'),
      value: market?.min_price ? `¥${market.min_price}` : '—',
      hint: market?.max_price
        ? t('results.insights.highestPrice', { price: market.max_price })
        : t('results.insights.noRange'),
    },
  ]
})

const quickActions = computed(() => [
  {
    title: t('dashboard.actions.tenantsTitle'),
    description: t('dashboard.actions.tenantsDescription'),
    icon: Building2,
    routeName: 'Tenants',
  },
  {
    title: t('dashboard.actions.accountsTitle'),
    description: t('dashboard.actions.accountsDescription'),
    icon: Users,
    routeName: 'Accounts',
  },
  {
    title: t('dashboard.actions.settingsTitle'),
    description: t('dashboard.actions.settingsDescription'),
    icon: Settings2,
    routeName: 'Settings',
  },
])

function openRoute(routeName: string) {
  router.push({ name: routeName })
}

function openSuggestion() {
  router.push({
    name: suggestion.value.routeName,
    query: suggestion.value.query,
  })
}

function openActivity(activity: { filename: string | null; type: string }) {
  if (activity.filename) {
    router.push({ name: 'Results', query: { file: activity.filename } })
    return
  }
  if (activity.type === 'task') {
    router.push({ name: 'Logs' })
    return
  }
  router.push({ name: 'Dashboard' })
}
</script>

<template>
  <div class="space-y-8 animate-fade-in">
    <section class="overflow-hidden rounded-[32px] border border-slate-200/80 bg-[linear-gradient(135deg,#08111f_0%,#13233a_45%,#deebf7_220%)] px-6 py-7 text-white shadow-[0_28px_90px_rgba(15,23,42,0.16)] md:px-8">
      <div class="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
        <div class="max-w-3xl">
          <p class="text-xs font-black uppercase tracking-[0.32em] text-slate-300">CatchYu Console</p>
          <h1 class="mt-3 flex items-center gap-3 text-3xl font-black tracking-tight md:text-4xl">
            <LayoutDashboard class="h-8 w-8 text-[#9fd3ff]" />
            {{ t('dashboard.title') }}
          </h1>
          <p class="mt-3 max-w-2xl text-sm leading-7 text-slate-300 md:text-base">
            {{ t('dashboard.description') }}
          </p>
        </div>
        <div class="rounded-[28px] border border-white/10 bg-white/10 px-5 py-4 backdrop-blur">
          <p class="text-xs font-black uppercase tracking-[0.28em] text-slate-400">{{ t('dashboard.hero.label') }}</p>
          <p class="mt-2 max-w-sm text-sm leading-7 text-slate-200">{{ t('dashboard.hero.description') }}</p>
        </div>
      </div>

      <div class="mt-6 grid gap-3 lg:grid-cols-3">
        <button
          v-for="item in quickActions"
          :key="item.routeName"
          class="group rounded-[24px] border border-white/10 bg-white/10 p-4 text-left backdrop-blur transition-all hover:-translate-y-0.5 hover:bg-white/14"
          @click="openRoute(item.routeName)"
        >
          <component :is="item.icon" class="h-5 w-5 text-[#a6d0ff]" />
          <h2 class="mt-4 text-base font-black text-white">{{ item.title }}</h2>
          <p class="mt-2 text-sm leading-6 text-slate-300">{{ item.description }}</p>
        </button>
      </div>
    </section>
    <div v-if="error" class="app-alert-error" role="alert">
      {{ error.message }}
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      <Card
        v-for="stat in statCards"
        :key="stat.label"
        class="app-surface border-none transition-all hover:-translate-y-0.5"
      >
        <CardContent class="p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-bold text-slate-400 uppercase tracking-wider">{{ stat.label }}</p>
              <h3 class="text-2xl font-black text-slate-800 mt-1">{{ stat.value }}</h3>
            </div>
            <div :class="[stat.bg, 'p-3 rounded-2xl']">
              <component :is="stat.icon" :class="['w-6 h-6', stat.color]" />
            </div>
          </div>
          <div class="mt-4 text-xs font-bold text-slate-500">
            {{ stat.detail }}
          </div>
        </CardContent>
      </Card>
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <Card class="app-surface border-none lg:col-span-2">
        <CardHeader class="flex flex-col gap-4 border-b border-slate-100/60 pb-5 md:flex-row md:items-start md:justify-between">
          <div class="space-y-2">
            <CardTitle class="text-lg font-bold text-slate-800">
              {{ focusTitle }}
            </CardTitle>
            <p class="text-sm text-slate-500">{{ focusMeta }}</p>
          </div>
          <Badge variant="secondary" class="w-fit bg-blue-100 text-blue-600">
            {{ focusTask?.latest_crawl_time ? t('dashboard.focus.latestUpdate', { time: formatRelativeTimeFromNow(focusTask.latest_crawl_time) }) : t('dashboard.focus.waiting') }}
          </Badge>
        </CardHeader>
        <CardContent class="space-y-6 p-6">
          <div v-if="isLoading" class="rounded-2xl border border-dashed border-slate-200 bg-white/60 px-4 py-10 text-center text-sm text-slate-500">
            {{ t('dashboard.focus.loading') }}
          </div>
          <div v-else-if="!focusTask?.filename" class="rounded-2xl border border-dashed border-slate-200 bg-white/60 px-4 py-10 text-center text-sm text-slate-500">
            {{ t('dashboard.focus.noResults') }}
          </div>
          <template v-else>
            <div class="grid gap-4 md:grid-cols-3">
              <article
                v-for="card in insightCards"
                :key="card.label"
                class="rounded-2xl border border-slate-200/70 bg-slate-50/80 p-4 shadow-sm"
              >
                <p class="text-xs uppercase tracking-[0.18em] text-slate-500">{{ card.label }}</p>
                <p class="mt-3 text-2xl font-semibold text-slate-900">{{ card.value }}</p>
                <p class="mt-2 text-xs text-slate-500">{{ card.hint }}</p>
              </article>
            </div>
            <PriceTrendChart :points="focusInsights?.daily_trend || []" />
            <div class="grid gap-3 rounded-[28px] border border-slate-200/70 bg-white/80 p-5 shadow-sm md:grid-cols-3">
              <div class="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
                {{ t('dashboard.focus.currentMedian') }}
                <span class="font-semibold text-slate-900">
                  {{ focusInsights?.market_summary.median_price ? `¥${focusInsights.market_summary.median_price}` : '—' }}
                </span>
              </div>
              <div class="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
                {{ t('dashboard.focus.historyMin') }}
                <span class="font-semibold text-slate-900">
                  {{ focusInsights?.history_summary.min_price ? `¥${focusInsights.history_summary.min_price}` : '—' }}
                </span>
              </div>
              <div class="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
                {{ t('dashboard.focus.historyMax') }}
                <span class="font-semibold text-slate-900">
                  {{ focusInsights?.history_summary.max_price ? `¥${focusInsights.history_summary.max_price}` : '—' }}
                </span>
              </div>
            </div>
          </template>
        </CardContent>
      </Card>
      <div class="space-y-8">
        <Card class="app-surface border-none">
          <CardHeader>
            <CardTitle class="text-lg font-bold text-slate-800 flex items-center gap-2">
              <Activity class="w-5 h-5 text-rose-500" />
              {{ t('dashboard.activity.title') }}
            </CardTitle>
          </CardHeader>
          <CardContent class="p-0">
            <div v-if="activities.length === 0" class="px-4 pb-4 text-sm text-slate-500">
              {{ t('dashboard.activity.empty') }}
            </div>
            <div v-else class="divide-y divide-slate-100/50">
              <button
                v-for="activity in activities"
                :key="activity.id"
                class="w-full p-4 text-left hover:bg-slate-50/50 transition-colors"
                @click="openActivity(activity)"
              >
                <div class="flex items-center justify-between gap-3">
                  <div class="flex items-center gap-3 min-w-0">
                    <div class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shrink-0"></div>
                    <div class="min-w-0">
                      <p class="text-sm font-bold text-slate-700 truncate">{{ activity.title }}</p>
                      <p class="text-[11px] text-slate-400">
                        {{ activity.task_name }} · {{ formatRelativeTimeFromNow(activity.timestamp) }}
                      </p>
                      <p v-if="activity.detail" class="mt-1 text-xs text-slate-500 truncate">{{ activity.detail }}</p>
                    </div>
                  </div>
                  <Badge variant="outline" class="text-[10px] border-slate-200 shrink-0">
                    {{ activity.status }}
                  </Badge>
                </div>
              </button>
            </div>
            <button
              class="w-full py-3 text-xs font-bold text-primary hover:bg-slate-50 transition-colors flex items-center justify-center gap-2 border-t border-slate-100/50"
              @click="router.push({ name: 'Logs' })"
            >
              {{ t('dashboard.activity.viewAllLogs') }}
              <ArrowRight class="w-3 h-3" />
            </button>
          </CardContent>
        </Card>
        <div class="app-surface border-none p-6">
          <div class="mb-4 flex items-center gap-2">
            <Sparkles class="w-6 h-6 text-primary" />
            <h4 class="font-bold text-lg">{{ t('dashboard.suggestion.sectionTitle') }}</h4>
          </div>
          <p class="mb-2 text-sm leading-relaxed text-slate-800">{{ suggestion.title }}</p>
          <p class="mb-6 text-sm leading-relaxed text-slate-500">{{ suggestion.description }}</p>
          <Button class="w-full" @click="openSuggestion">
            <Sparkles class="mr-2 h-4 w-4" />
            {{ suggestion.actionLabel }}
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>
