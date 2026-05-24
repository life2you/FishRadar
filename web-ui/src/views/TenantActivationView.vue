<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuth } from '@/composables/useAuth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from '@/components/ui/toast'

const router = useRouter()
const { t } = useI18n()
const {
  tenantName,
  displayName,
  workspaceEnabled,
  redeemActivationCode,
  canUseAi,
  tenantAccessExpiresAt,
  tenantAccessExpired,
} = useAuth()

const code = ref('')
const isSubmitting = ref(false)
const error = ref('')

const tenantTitle = computed(() => tenantName.value || displayName.value || t('common.unnamed'))
const accessExpiryText = computed(() => {
  if (!tenantAccessExpiresAt.value) {
    return t('activation.noExpiry')
  }
  const parsed = new Date(tenantAccessExpiresAt.value)
  if (Number.isNaN(parsed.getTime())) {
    return tenantAccessExpiresAt.value
  }
  return parsed.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
})

async function handleActivate() {
  if (!code.value.trim()) {
    error.value = t('activation.errors.codeRequired')
    return
  }
  isSubmitting.value = true
  error.value = ''
  try {
    await redeemActivationCode(code.value.trim())
    toast({ title: t('activation.successTitle'), description: t('activation.successDescription') })
    router.push('/tasks')
  } catch (err) {
    error.value = (err as Error).message || t('activation.errors.unexpected')
  } finally {
    isSubmitting.value = false
  }
}

function enterWorkspace() {
  router.push('/tasks')
}
</script>

<template>
  <div class="mx-auto max-w-4xl space-y-6">
    <section class="overflow-hidden rounded-[32px] border border-[#e7d7bf] bg-[linear-gradient(135deg,#fff8ee_0%,#f7ead7_100%)] p-6 shadow-[0_24px_80px_rgba(79,58,33,0.10)] md:p-8">
      <p class="text-[11px] font-bold uppercase tracking-[0.26em] text-[#9f7d58]">{{ t('activation.eyebrow') }}</p>
      <h1 class="mt-4 text-3xl font-black tracking-[-0.04em] text-[#241a12] md:text-4xl">
        {{ t('activation.title', { tenant: tenantTitle }) }}
      </h1>
      <p class="mt-4 max-w-2xl text-sm leading-7 text-[#675240]">
        {{ workspaceEnabled ? t('activation.activeDescription') : (tenantAccessExpired ? t('activation.expiredDescription') : t('activation.description')) }}
      </p>

      <div class="mt-6 grid gap-4 md:grid-cols-3">
        <article class="rounded-[24px] border border-white/90 bg-white/82 p-4 shadow-sm">
          <p class="text-[11px] font-bold uppercase tracking-[0.22em] text-[#9f7d58]">{{ t('activation.cards.registered') }}</p>
          <p class="mt-3 text-base font-bold text-[#2b1d13]">{{ tenantTitle }}</p>
          <p class="mt-2 text-sm leading-6 text-[#6d5947]">{{ t('activation.cards.registeredHint') }}</p>
        </article>
        <article class="rounded-[24px] border border-white/90 bg-white/82 p-4 shadow-sm">
          <p class="text-[11px] font-bold uppercase tracking-[0.22em] text-[#9f7d58]">{{ t('activation.cards.workspace') }}</p>
          <p class="mt-3 text-base font-bold text-[#2b1d13]">{{ workspaceEnabled ? t('activation.workspaceReady') : t('activation.workspacePending') }}</p>
          <p class="mt-2 text-sm leading-6 text-[#6d5947]">
            {{ tenantAccessExpired ? t('activation.cards.workspaceExpiredHint') : t('activation.cards.workspaceHint') }}
          </p>
          <p class="mt-2 text-xs text-[#8b745e]">
            {{ t('activation.expiryAt', { value: accessExpiryText }) }}
          </p>
        </article>
        <article class="rounded-[24px] border border-white/90 bg-white/82 p-4 shadow-sm">
          <p class="text-[11px] font-bold uppercase tracking-[0.22em] text-[#9f7d58]">{{ t('activation.cards.ai') }}</p>
          <p class="mt-3 text-base font-bold text-[#2b1d13]">{{ canUseAi ? t('activation.aiReady') : t('activation.aiPending') }}</p>
          <p class="mt-2 text-sm leading-6 text-[#6d5947]">{{ t('activation.cards.aiHint') }}</p>
        </article>
      </div>
    </section>

    <Card class="border-[#eadbc8] bg-white/90 shadow-[0_20px_70px_rgba(77,56,35,0.08)]">
      <CardHeader>
        <CardTitle>{{ t('activation.formTitle') }}</CardTitle>
        <CardDescription>{{ workspaceEnabled ? t('activation.formReadyDescription') : t('activation.formDescription') }}</CardDescription>
      </CardHeader>
      <CardContent class="space-y-4">
        <template v-if="!workspaceEnabled">
          <div class="grid gap-2">
            <Label for="activation-code">{{ t('activation.codeLabel') }}</Label>
            <Input
              id="activation-code"
              v-model="code"
              class="h-12 rounded-2xl border-[#dfcfbb] bg-[#fffdf8] uppercase tracking-[0.18em]"
              :placeholder="t('activation.codePlaceholder')"
            />
          </div>
          <div v-if="error" class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {{ error }}
          </div>
          <div v-if="tenantAccessExpired" class="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
            {{ t('activation.expiredNotice') }}
          </div>
          <Button
            class="h-12 rounded-full bg-[#21160f] px-6 text-white hover:bg-[#2f2016]"
            :disabled="isSubmitting"
            @click="handleActivate"
          >
            {{ isSubmitting ? t('activation.submitting') : t('activation.submit') }}
          </Button>
        </template>

        <template v-else>
          <div class="rounded-[24px] border border-[#d8e5d8] bg-[#edf7ef] px-4 py-4 text-sm leading-6 text-[#35523d]">
            {{ t('activation.readyNotice') }}
          </div>
          <Button class="h-12 rounded-full bg-[#21160f] px-6 text-white hover:bg-[#2f2016]" @click="enterWorkspace">
            {{ t('activation.enterWorkspace') }}
          </Button>
        </template>
      </CardContent>
    </Card>
  </div>
</template>
