<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import {
  createActivationCodes,
  getActivationCodes,
  getTenantAccessSettings,
  updateTenantAccessSettings,
} from '@/api/settings'
import type { ActivationCodeItem, TenantAccessItem } from '@/api/settings'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { toast } from '@/components/ui/toast'

const { t } = useI18n()
const router = useRouter()

const tenantItems = ref<TenantAccessItem[]>([])
const activationCodes = ref<ActivationCodeItem[]>([])
const latestCreatedCodes = ref<ActivationCodeItem[]>([])
const tenantAccessError = ref<string | null>(null)
const isTenantAccessLoading = ref(false)
const isTenantAccessSaving = ref(false)
const activationCodeQuantity = ref(5)
const activationCodeDurationPreset = ref('1d')
const activationCodeDurationValue = ref(1)
const activationCodeDurationUnit = ref<'minutes' | 'hours' | 'days'>('days')
const activationCodeNote = ref('')
const activationCodeStatusFilter = ref<'all' | 'unused' | 'redeemed'>('all')
const activationCodeKeyword = ref('')
const renewPresets = [
  { label: '1天', minutes: 1440 },
  { label: '3天', minutes: 4320 },
  { label: '7天', minutes: 10080 },
] as const

const durationPresetOptions = [
  { label: '1 小时', value: '1h', amount: 1, unit: 'hours' },
  { label: '6 小时', value: '6h', amount: 6, unit: 'hours' },
  { label: '12 小时', value: '12h', amount: 12, unit: 'hours' },
  { label: '1 天', value: '1d', amount: 1, unit: 'days' },
  { label: '3 天', value: '3d', amount: 3, unit: 'days' },
  { label: '7 天', value: '7d', amount: 7, unit: 'days' },
  { label: '30 天', value: '30d', amount: 30, unit: 'days' },
  { label: '自定义', value: 'custom', amount: null, unit: null },
] as const

const durationUnitOptions = [
  { label: '分钟', value: 'minutes' },
  { label: '小时', value: 'hours' },
  { label: '天', value: 'days' },
] as const

const filteredActivationCodes = computed(() => {
  const keyword = activationCodeKeyword.value.trim().toLowerCase()
  return activationCodes.value.filter((item) => {
    if (activationCodeStatusFilter.value !== 'all' && item.status !== activationCodeStatusFilter.value) {
      return false
    }
    if (!keyword) {
      return true
    }
    return [
      item.code,
      item.note || '',
      item.redeemed_tenant_name || '',
    ].some((field) => field.toLowerCase().includes(keyword))
  })
})

function notifySuccess(title: string, description?: string) {
  toast({ title, description })
}

function notifyError(title: string, description?: string) {
  toast({ title, description, variant: 'destructive' })
}

function getDurationUnitMultiplier(unit: 'minutes' | 'hours' | 'days') {
  if (unit === 'hours') return 60
  if (unit === 'days') return 1440
  return 1
}

function getResolvedDurationMinutes() {
  const normalizedValue = Math.max(1, Number(activationCodeDurationValue.value || 1))
  return normalizedValue * getDurationUnitMultiplier(activationCodeDurationUnit.value)
}

function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return t('common.empty')
  }
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }
  return parsed.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatDurationMinutes(minutes: number | null | undefined) {
  const totalMinutes = Number(minutes || 0)
  if (!totalMinutes) {
    return t('settings.tenantAccess.durationUnknown')
  }
  const days = Math.floor(totalMinutes / 1440)
  const hours = Math.floor((totalMinutes % 1440) / 60)
  const mins = totalMinutes % 60
  const parts: string[] = []
  if (days) parts.push(`${days}${t('settings.tenantAccess.dayUnit')}`)
  if (hours) parts.push(`${hours}${t('settings.tenantAccess.hourUnit')}`)
  if (mins || parts.length === 0) parts.push(`${mins}${t('settings.tenantAccess.minuteUnit')}`)
  return parts.join(' ')
}

function updateDurationPreset(value: string) {
  activationCodeDurationPreset.value = value
  const selected = durationPresetOptions.find((option) => option.value === value)
  if (selected && selected.value !== 'custom' && selected.amount && selected.unit) {
    activationCodeDurationValue.value = selected.amount
    activationCodeDurationUnit.value = selected.unit
  }
}

async function copyText(value: string, successMessage: string) {
  try {
    await navigator.clipboard.writeText(value)
    notifySuccess(successMessage)
  } catch (e) {
    notifyError(t('settings.tenantAccess.copyFailed'), (e as Error).message)
  }
}

async function fetchTenantAccessData() {
  isTenantAccessLoading.value = true
  tenantAccessError.value = null
  try {
    const [tenantResponse, codeResponse] = await Promise.all([
      getTenantAccessSettings(),
      getActivationCodes(),
    ])
    tenantItems.value = tenantResponse.items
    activationCodes.value = codeResponse.items
  } catch (e) {
    tenantAccessError.value = (e as Error).message || t('settings.tenantAccess.loadFailed')
  } finally {
    isTenantAccessLoading.value = false
  }
}

function openTenantDetail(item: TenantAccessItem) {
  router.push({ name: 'TenantDetail', params: { tenantId: item.id } })
}

async function handleToggleTenantStatus(item: TenantAccessItem) {
  isTenantAccessSaving.value = true
  try {
    const nextStatus = item.status === 'active' ? 'disabled' : 'active'
    const response = await updateTenantAccessSettings(item.id, { status: nextStatus })
    tenantItems.value = tenantItems.value.map((tenant) => tenant.id === item.id ? response.item : tenant)
    notifySuccess(t('settings.tenantAccess.statusSaved'))
  } catch (e) {
    notifyError(t('settings.tenantAccess.saveFailed'), (e as Error).message)
  } finally {
    isTenantAccessSaving.value = false
  }
}

async function handleToggleTenantAi(item: TenantAccessItem) {
  isTenantAccessSaving.value = true
  try {
    const response = await updateTenantAccessSettings(item.id, { ai_enabled: !item.ai_enabled })
    tenantItems.value = tenantItems.value.map((tenant) => tenant.id === item.id ? response.item : tenant)
    notifySuccess(t('settings.tenantAccess.aiSaved'))
  } catch (e) {
    notifyError(t('settings.tenantAccess.saveFailed'), (e as Error).message)
  } finally {
    isTenantAccessSaving.value = false
  }
}

async function handleToggleActivationRequirement(item: TenantAccessItem) {
  isTenantAccessSaving.value = true
  try {
    const response = await updateTenantAccessSettings(item.id, {
      activation_required: !item.activation_required,
    })
    tenantItems.value = tenantItems.value.map((tenant) => tenant.id === item.id ? response.item : tenant)
    notifySuccess(t('settings.tenantAccess.activationSaved'))
  } catch (e) {
    notifyError(t('settings.tenantAccess.saveFailed'), (e as Error).message)
  } finally {
    isTenantAccessSaving.value = false
  }
}

async function handleCreateActivationCodes() {
  const durationMinutes = getResolvedDurationMinutes()
  if (!Number.isFinite(durationMinutes) || durationMinutes < 1) {
    notifyError(t('settings.tenantAccess.codeCreateFailed'), t('settings.tenantAccess.durationInvalid'))
    return
  }
  isTenantAccessSaving.value = true
  try {
    const response = await createActivationCodes({
      quantity: activationCodeQuantity.value,
      duration_minutes: durationMinutes,
      note: activationCodeNote.value.trim() || null,
    })
    latestCreatedCodes.value = response.items
    activationCodeNote.value = ''
    notifySuccess(t('settings.tenantAccess.codesCreated'))
    await fetchTenantAccessData()
  } catch (e) {
    notifyError(t('settings.tenantAccess.codeCreateFailed'), (e as Error).message)
  } finally {
    isTenantAccessSaving.value = false
  }
}

async function handleExtendTenantAccess(item: TenantAccessItem, minutes: number) {
  isTenantAccessSaving.value = true
  try {
    const response = await updateTenantAccessSettings(item.id, { extend_access_minutes: minutes })
    tenantItems.value = tenantItems.value.map((tenant) => tenant.id === item.id ? response.item : tenant)
    notifySuccess(t('settings.tenantAccess.renewSaved'))
  } catch (e) {
    notifyError(t('settings.tenantAccess.saveFailed'), (e as Error).message)
  } finally {
    isTenantAccessSaving.value = false
  }
}

onMounted(() => {
  fetchTenantAccessData()
})
</script>

<template>
  <div class="grid gap-6">
    <Card class="border border-slate-200/80 bg-white/90 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
      <CardHeader class="border-b border-slate-100/80 pb-5">
        <CardTitle class="text-xl font-black text-slate-900">{{ t('settings.tenantAccess.title') }}</CardTitle>
        <CardDescription class="max-w-3xl text-sm leading-6 text-slate-500">
          {{ t('settings.tenantAccess.description') }}
        </CardDescription>
      </CardHeader>
      <CardContent class="space-y-5 p-6">
        <div v-if="tenantAccessError" class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {{ tenantAccessError }}
        </div>

        <div class="grid gap-5 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
          <section class="rounded-3xl border border-slate-200 bg-[linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] p-5 shadow-sm">
            <h3 class="text-base font-black text-slate-900">{{ t('settings.tenantAccess.generateTitle') }}</h3>
            <p class="mt-1 text-sm text-slate-500">{{ t('settings.tenantAccess.generateDescription') }}</p>

            <div class="mt-5 grid gap-4 md:grid-cols-2">
              <div class="grid gap-2">
                <Label>{{ t('settings.tenantAccess.codeCount') }}</Label>
                <Input v-model.number="activationCodeQuantity" type="number" min="1" max="100" />
              </div>
              <div class="grid gap-2">
                <Label>{{ t('settings.tenantAccess.codeNote') }}</Label>
                <Input v-model="activationCodeNote" :placeholder="t('settings.tenantAccess.codeNotePlaceholder')" />
              </div>
            </div>

            <div class="mt-4 grid gap-2">
              <Label>{{ t('settings.tenantAccess.codeDurationPreset') }}</Label>
              <div class="grid grid-cols-2 gap-2 lg:grid-cols-4">
                <Button
                  v-for="option in durationPresetOptions"
                  :key="option.value"
                  type="button"
                  variant="outline"
                  class="justify-center rounded-2xl"
                  :class="activationCodeDurationPreset === option.value ? 'border-slate-900 bg-slate-900 text-white hover:bg-slate-900 hover:text-white' : ''"
                  @click="updateDurationPreset(option.value)"
                >
                  {{ option.label }}
                </Button>
              </div>
            </div>

            <div v-if="activationCodeDurationPreset === 'custom'" class="mt-4 grid gap-4 md:grid-cols-[minmax(0,1fr)_220px]">
              <div class="grid gap-2">
                <Label>{{ t('settings.tenantAccess.customDurationValue') }}</Label>
                <Input v-model.number="activationCodeDurationValue" type="number" min="1" max="525600" step="1" />
              </div>
              <div class="grid gap-2">
                <Label>{{ t('settings.tenantAccess.customDurationUnit') }}</Label>
                <Select :model-value="activationCodeDurationUnit" @update:model-value="(value) => activationCodeDurationUnit = value as 'minutes' | 'hours' | 'days'">
                  <SelectTrigger>
                    <SelectValue :placeholder="t('settings.tenantAccess.customDurationUnit')" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem
                      v-for="option in durationUnitOptions"
                      :key="option.value"
                      :value="option.value"
                    >
                      {{ option.label }}
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div class="mt-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
              {{ t('settings.tenantAccess.codeDurationHint', { duration: formatDurationMinutes(getResolvedDurationMinutes()) }) }}
            </div>

            <Button class="mt-4 rounded-2xl px-5" :disabled="isTenantAccessSaving" @click="handleCreateActivationCodes">
              {{ isTenantAccessSaving ? t('common.saving') : t('settings.tenantAccess.generateAction') }}
            </Button>

            <div v-if="latestCreatedCodes.length" class="mt-5 rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <p class="text-sm font-black text-emerald-900">{{ t('settings.tenantAccess.latestCodes') }}</p>
                <Button
                  variant="outline"
                  size="sm"
                  class="border-emerald-300 bg-white text-emerald-900"
                  @click="copyText(latestCreatedCodes.map((item) => item.code).join('\\n'), t('settings.tenantAccess.copiedBatch'))"
                >
                  {{ t('settings.tenantAccess.copyBatch') }}
                </Button>
              </div>
              <div class="mt-3 grid gap-2">
                <div
                  v-for="item in latestCreatedCodes"
                  :key="item.code"
                  class="flex items-center justify-between gap-3 rounded-xl bg-white px-3 py-2 text-sm text-emerald-900"
                >
                  <code>{{ item.code }} · {{ formatDurationMinutes(item.duration_minutes) }}</code>
                  <Button
                    variant="ghost"
                    size="sm"
                    class="h-8 px-2 text-emerald-900"
                    @click="copyText(item.code, t('settings.tenantAccess.copiedCode'))"
                  >
                    {{ t('settings.tenantAccess.copyCode') }}
                  </Button>
                </div>
              </div>
            </div>
          </section>

          <section class="rounded-3xl border border-slate-200 bg-slate-50/70 p-5 shadow-sm">
            <h3 class="text-base font-black text-slate-900">{{ t('settings.tenantAccess.codesListTitle') }}</h3>
            <p class="mt-1 text-sm text-slate-500">{{ t('settings.tenantAccess.codesListDescription') }}</p>
            <div class="mt-4 grid gap-3 md:grid-cols-[180px_minmax(0,1fr)]">
              <Select v-model="activationCodeStatusFilter">
                <SelectTrigger>
                  <SelectValue :placeholder="t('settings.tenantAccess.codeStatusFilter')" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{{ t('settings.tenantAccess.filterAll') }}</SelectItem>
                  <SelectItem value="unused">{{ t('settings.tenantAccess.filterUnused') }}</SelectItem>
                  <SelectItem value="redeemed">{{ t('settings.tenantAccess.filterRedeemed') }}</SelectItem>
                </SelectContent>
              </Select>
              <Input
                v-model="activationCodeKeyword"
                :placeholder="t('settings.tenantAccess.codeSearchPlaceholder')"
              />
            </div>

            <div v-if="isTenantAccessLoading" class="mt-4 text-sm text-slate-500">
              {{ t('common.loading') }}
            </div>
            <div v-else class="mt-4 max-h-[420px] space-y-3 overflow-y-auto pr-1">
              <div
                v-for="item in filteredActivationCodes"
                :key="item.id || item.code"
                class="rounded-2xl border border-slate-200 bg-white p-4"
              >
                <div class="flex flex-wrap items-center justify-between gap-2">
                  <code class="text-sm font-black text-slate-900">{{ item.code }}</code>
                  <div class="flex items-center gap-2">
                    <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">
                      {{ item.status }}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      class="h-8 px-2"
                      @click="copyText(item.code, t('settings.tenantAccess.copiedCode'))"
                    >
                      {{ t('settings.tenantAccess.copyCode') }}
                    </Button>
                  </div>
                </div>
                <p class="mt-2 text-xs text-slate-500">
                  {{ t('settings.tenantAccess.durationText', { duration: formatDurationMinutes(item.duration_minutes) }) }}
                </p>
                <p class="mt-1 text-xs text-slate-500">
                  {{ item.note || t('settings.tenantAccess.noNote') }}
                </p>
                <p class="mt-1 text-xs text-slate-500">
                  {{ item.redeemed_tenant_name ? t('settings.tenantAccess.redeemedBy', { tenant: item.redeemed_tenant_name }) : t('settings.tenantAccess.notRedeemed') }}
                </p>
              </div>
            </div>
          </section>
        </div>

        <section class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 class="text-base font-black text-slate-900">{{ t('settings.tenantAccess.tenantsTitle') }}</h3>
          <p class="mt-1 text-sm text-slate-500">{{ t('settings.tenantAccess.tenantsDescription') }}</p>

          <div v-if="isTenantAccessLoading" class="mt-4 text-sm text-slate-500">
            {{ t('common.loading') }}
          </div>
          <div v-else class="mt-4 space-y-3">
            <div
              v-for="item in tenantItems"
              :key="item.id"
              class="rounded-3xl border border-slate-200 bg-[linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] p-4"
            >
              <div class="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
                <div>
                  <div class="flex flex-wrap items-center gap-2">
                    <h4 class="text-base font-black text-slate-900">{{ item.name }}</h4>
                    <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">
                      {{ item.slug }}
                    </span>
                    <span class="rounded-full px-3 py-1 text-xs font-bold" :class="item.status === 'active' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'">
                      {{ item.status }}
                    </span>
                  </div>
                  <p class="mt-2 text-sm text-slate-500">
                    {{ t('settings.tenantAccess.memberCount', { count: item.member_count }) }}
                  </p>
                  <p class="mt-1 text-xs text-slate-500">
                    {{ item.activated_at ? t('settings.tenantAccess.activatedAt', { value: formatDateTime(item.activated_at) }) : t('settings.tenantAccess.pendingActivation') }}
                  </p>
                  <p class="mt-1 text-xs text-slate-500">
                    {{ item.access_expires_at ? t('settings.tenantAccess.expiresAt', { value: formatDateTime(item.access_expires_at) }) : t('settings.tenantAccess.noExpiry') }}
                  </p>
                  <p class="mt-1 text-xs font-semibold" :class="item.workspace_enabled ? 'text-emerald-700' : 'text-amber-700'">
                    {{ item.workspace_enabled ? t('settings.tenantAccess.workspaceReady') : t('settings.tenantAccess.workspacePending') }}
                  </p>
                </div>
                <div class="flex flex-wrap gap-2 xl:max-w-[520px] xl:justify-end">
                  <Button variant="outline" size="sm" :disabled="isTenantAccessSaving" @click="openTenantDetail(item)">
                    {{ t('settings.tenantAccess.viewTenant') }}
                  </Button>
                  <Button variant="outline" size="sm" :disabled="isTenantAccessSaving" @click="handleToggleTenantStatus(item)">
                    {{ item.status === 'active' ? t('settings.tenantAccess.disableTenant') : t('settings.tenantAccess.enableTenant') }}
                  </Button>
                  <Button variant="outline" size="sm" :disabled="isTenantAccessSaving" @click="handleToggleTenantAi(item)">
                    {{ item.ai_enabled ? t('settings.tenantAccess.disableAi') : t('settings.tenantAccess.enableAi') }}
                  </Button>
                  <Button variant="outline" size="sm" :disabled="isTenantAccessSaving" @click="handleToggleActivationRequirement(item)">
                    {{ item.activation_required ? t('settings.tenantAccess.removeActivationRequirement') : t('settings.tenantAccess.requireActivation') }}
                  </Button>
                  <Button
                    v-for="preset in renewPresets"
                    :key="preset.minutes"
                    variant="outline"
                    size="sm"
                    :disabled="isTenantAccessSaving"
                    @click="handleExtendTenantAccess(item, preset.minutes)"
                  >
                    {{ t('settings.tenantAccess.renewAction', { duration: preset.label }) }}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </section>
      </CardContent>
    </Card>
  </div>
</template>
