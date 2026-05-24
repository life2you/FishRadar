<script setup lang="ts">
import { computed, ref, toRefs } from 'vue'
import { ArrowUpRight, Eye, EyeOff, Tag, UserRound } from 'lucide-vue-next'
import type { ResultItem } from '@/types/result.d.ts'
import { formatDateTime } from '@/i18n'
import { Button } from '@/components/ui/button'

const props = defineProps<{
  item: ResultItem
}>()
const { item } = toRefs(props)

const emit = defineEmits<{
  (e: 'toggle-block', item: ResultItem): void
}>()

const expanded = ref(false)
const info = props.item.商品信息
const seller = props.item.卖家信息
const ai = props.item.ai_analysis
const priceInsight = props.item.price_insight
const imageUrl = info.商品图片列表?.[0] || info.商品主图链接 || ''
const isHidden = computed(() => props.item._effective_hidden === true || props.item._status === 'hidden')
const canToggleBlock = computed(() => props.item._hidden_reason !== 'rule' && props.item._hidden_reason !== 'expired')
const statusLabel = computed(() => {
  if (props.item._hidden_reason === 'rule') return '黑名单隐藏'
  if (props.item._hidden_reason === 'expired') return '已过期'
  if (isHidden.value) return '已隐藏'
  return ai?.is_recommended ? '推荐中' : '观察中'
})
const recommendationTone = computed(() => {
  if (props.item._hidden_reason === 'rule' || props.item._hidden_reason === 'expired' || isHidden.value) {
    return 'border-[#ddd6cc] bg-[#f3f0eb] text-[#64594d]'
  }
  if (ai?.is_recommended) {
    return 'border-[#d2e3d5] bg-[#edf6ef] text-[#305541]'
  }
  return 'border-[#ead8c7] bg-[#fbefe1] text-[#8d4f1f]'
})
const matchedTags = computed(() => {
  const values = [
    ...(ai?.matched_keywords || []),
    ...(ai?.risk_tags || []),
    ...(info.商品标签 || []),
  ]
  return Array.from(new Set(values)).slice(0, 5)
})
const priceSummary = computed(() => {
  if (priceInsight?.market_avg_price) return `市场均价 ¥${priceInsight.market_avg_price}`
  if (priceInsight?.avg_price) return `历史均价 ¥${priceInsight.avg_price}`
  return '等待价格样本积累'
})
const crawlTime = computed(() => {
  if (!props.item.爬取时间) return '时间未知'
  return formatDateTime(props.item.爬取时间, {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
})
</script>

<template>
  <article class="overflow-hidden rounded-[32px] border border-[#eadfce] bg-[linear-gradient(180deg,rgba(255,252,247,0.98)_0%,rgba(252,247,240,0.98)_100%)] shadow-[0_24px_60px_rgba(77,56,35,0.08)]" :class="{ 'opacity-70': isHidden }">
    <div class="grid gap-0 lg:grid-cols-[240px_minmax(0,1fr)]">
      <div class="relative h-full min-h-[220px] overflow-hidden bg-[#f2e7d5]">
        <img
          v-if="imageUrl"
          :src="imageUrl"
          :alt="info.商品标题"
          class="h-full w-full object-cover"
          loading="lazy"
        />
        <div v-else class="flex h-full items-center justify-center text-sm font-semibold text-[#8c7358]">
          暂无商品图片
        </div>
        <div class="absolute left-4 top-4">
          <span class="inline-flex rounded-full border px-3 py-1 text-xs font-bold" :class="recommendationTone">
            {{ statusLabel }}
          </span>
        </div>
      </div>

      <div class="flex flex-col gap-5 p-5 md:p-6">
        <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div class="min-w-0">
            <h3 class="line-clamp-2 text-[1.45rem] font-black tracking-[-0.04em] text-[#241a12]">
              {{ info.商品标题 }}
            </h3>
            <p class="mt-3 text-[1.45rem] font-black tracking-[-0.03em] text-[#b34921]">
              {{ info.当前售价 }}
            </p>
            <p class="mt-2 text-sm text-[#6a5744]">
              {{ priceSummary }}
            </p>
          </div>

          <div class="flex shrink-0 gap-2">
            <Button
              v-if="canToggleBlock"
              variant="outline"
              class="rounded-full border-[#e2d5c4] bg-white/85 px-4 text-[#493326] hover:bg-white"
              @click="emit('toggle-block', item)"
            >
              <EyeOff v-if="!isHidden" class="mr-2 h-4 w-4" />
              <Eye v-else class="mr-2 h-4 w-4" />
              {{ isHidden ? '恢复' : '隐藏' }}
            </Button>
            <a
              :href="info.商品链接"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center rounded-full bg-[#21160f] px-4 py-2 text-sm font-bold text-white hover:bg-[#2f2016]"
            >
              查看原帖
              <ArrowUpRight class="ml-2 h-4 w-4" />
            </a>
          </div>
        </div>

        <div class="grid gap-4 md:grid-cols-[minmax(0,1fr)_220px]">
          <div class="rounded-[26px] border border-white/90 bg-white/86 p-4 shadow-sm">
            <p class="text-[11px] font-bold uppercase tracking-[0.22em] text-[#9b8165]">简要分析</p>
            <p class="mt-3 text-sm leading-7 text-[#5f4d3d]" :class="{ 'line-clamp-3': !expanded }">
              {{ ai?.reason || '当前记录还没有分析说明。' }}
            </p>
            <button
              v-if="ai?.reason && ai.reason.length > 72"
              type="button"
              class="mt-3 text-xs font-bold text-[#9b5524]"
              @click="expanded = !expanded"
            >
              {{ expanded ? '收起分析' : '展开分析' }}
            </button>

            <div class="mt-4 flex flex-wrap gap-2">
              <span
                v-for="tag in matchedTags"
                :key="tag"
                class="inline-flex items-center gap-1 rounded-full border border-[#e7ddce] bg-[#faf4eb] px-3 py-1 text-xs font-semibold text-[#694f39]"
              >
                <Tag class="h-3 w-3" />
                {{ tag }}
              </span>
            </div>
          </div>

          <div class="rounded-[26px] border border-white/90 bg-white/86 p-4 shadow-sm">
            <p class="text-[11px] font-bold uppercase tracking-[0.22em] text-[#9b8165]">线索摘要</p>
            <div class="mt-4 space-y-3 text-sm leading-6 text-[#5f4d3d]">
              <p>
                <span class="font-semibold text-[#2b1d13]">推荐分：</span>
                {{ ai?.value_score ?? '—' }}%
              </p>
              <p>
                <span class="font-semibold text-[#2b1d13]">价格波动：</span>
                {{ priceInsight?.price_change_percent ? `${priceInsight.price_change_percent}%` : '暂无' }}
              </p>
              <p>
                <span class="font-semibold text-[#2b1d13]">Deal 标记：</span>
                {{ priceInsight?.deal_label || '待判断' }}
              </p>
              <p class="flex items-center gap-2">
                <UserRound class="h-4 w-4 text-[#8c6b50]" />
                {{ seller.卖家昵称 || info.卖家昵称 || '匿名卖家' }}
              </p>
              <p>{{ crawlTime }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </article>
</template>
