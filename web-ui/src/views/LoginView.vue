<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import LocaleToggle from '@/components/layout/LocaleToggle.vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useI18n } from 'vue-i18n'

const loginUsername = ref('')
const loginPassword = ref('')
const registerTenantName = ref('')
const registerDisplayName = ref('')
const registerUsername = ref('')
const registerPassword = ref('')
const registerPasswordConfirm = ref('')
const isLoading = ref(false)
const error = ref('')
const activeTab = ref<'login' | 'register'>('login')

const { login, register } = useAuth()
const router = useRouter()
const route = useRoute()
const { t } = useI18n()

const loginCardTitle = computed(() => (
  activeTab.value === 'login' ? t('login.title') : t('login.registerTitle')
))

watch(activeTab, () => {
  error.value = ''
})

function redirectAfterAuth() {
  const redirectPath = (route.query.redirect as string) || '/'
  router.push(redirectPath)
}

async function handleLogin() {
  if (!loginUsername.value || !loginPassword.value) {
    error.value = t('login.errors.missingCredentials')
    return
  }

  isLoading.value = true
  error.value = ''

  try {
    const success = await login(loginUsername.value, loginPassword.value)
    if (success) {
      redirectAfterAuth()
    } else {
      error.value = t('login.errors.invalidCredentials')
    }
  } catch (_error) {
    error.value = t('login.errors.unexpected')
  } finally {
    isLoading.value = false
  }
}

async function handleRegister() {
  if (!registerTenantName.value || !registerUsername.value || !registerPassword.value) {
    error.value = t('login.errors.registerRequired')
    return
  }
  if (registerPassword.value.length < 6) {
    error.value = t('login.errors.passwordTooShort')
    return
  }
  if (registerPassword.value !== registerPasswordConfirm.value) {
    error.value = t('login.errors.passwordMismatch')
    return
  }

  isLoading.value = true
  error.value = ''

  try {
    await register({
      tenant_name: registerTenantName.value.trim(),
      display_name: registerDisplayName.value.trim(),
      username: registerUsername.value.trim(),
      password: registerPassword.value,
    })
    router.push('/activate')
  } catch (err) {
    error.value = (err as Error).message || t('login.errors.registerFailed')
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#f6efe5] px-4 py-10">
    <div aria-hidden="true" class="absolute inset-0">
      <div class="absolute left-[-8%] top-[-10%] h-80 w-80 rounded-full bg-[#d9c1a0]/30 blur-3xl"></div>
      <div class="absolute bottom-[-12%] right-[-4%] h-96 w-96 rounded-full bg-[#e9d8be]/40 blur-3xl"></div>
      <div class="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.65),transparent_42%)]"></div>
    </div>

    <div class="absolute right-6 top-6">
      <LocaleToggle />
    </div>

    <div class="relative z-10 grid w-full max-w-6xl gap-6 lg:grid-cols-[1.05fr_0.95fr]">
      <section class="rounded-[36px] border border-white/70 bg-[linear-gradient(135deg,rgba(255,251,245,0.92)_0%,rgba(247,234,215,0.92)_100%)] p-8 shadow-[0_28px_90px_rgba(82,60,35,0.10)] lg:p-10">
        <p class="text-[11px] font-bold uppercase tracking-[0.3em] text-[#9f7d58]">{{ t('login.brandEyebrow') }}</p>
        <h1 class="mt-5 text-4xl font-black tracking-[-0.05em] text-[#251b12] lg:text-5xl">{{ t('login.heroTitle') }}</h1>
        <p class="mt-5 max-w-2xl text-sm leading-7 text-[#65503f]">
          {{ t('login.heroDescription') }}
        </p>

        <div class="mt-8 grid gap-4 md:grid-cols-3">
          <article class="rounded-[24px] border border-white/80 bg-white/80 p-4 shadow-sm">
            <p class="text-[11px] font-bold uppercase tracking-[0.22em] text-[#9a7a57]">{{ t('login.cards.register') }}</p>
            <p class="mt-3 text-base font-bold text-[#2b1d13]">{{ t('login.cards.registerTitle') }}</p>
            <p class="mt-2 text-sm leading-6 text-[#6c5948]">{{ t('login.cards.registerDescription') }}</p>
          </article>
          <article class="rounded-[24px] border border-white/80 bg-white/80 p-4 shadow-sm">
            <p class="text-[11px] font-bold uppercase tracking-[0.22em] text-[#9a7a57]">{{ t('login.cards.activate') }}</p>
            <p class="mt-3 text-base font-bold text-[#2b1d13]">{{ t('login.cards.activateTitle') }}</p>
            <p class="mt-2 text-sm leading-6 text-[#6c5948]">{{ t('login.cards.activateDescription') }}</p>
          </article>
          <article class="rounded-[24px] border border-white/80 bg-white/80 p-4 shadow-sm">
            <p class="text-[11px] font-bold uppercase tracking-[0.22em] text-[#9a7a57]">{{ t('login.cards.workspace') }}</p>
            <p class="mt-3 text-base font-bold text-[#2b1d13]">{{ t('login.cards.workspaceTitle') }}</p>
            <p class="mt-2 text-sm leading-6 text-[#6c5948]">{{ t('login.cards.workspaceDescription') }}</p>
          </article>
        </div>
      </section>

      <Card class="border-none bg-white/88 shadow-[0_26px_90px_rgba(82,60,35,0.12)]">
        <CardHeader>
          <CardTitle class="text-2xl text-center text-[#241a12]">{{ loginCardTitle }}</CardTitle>
          <CardDescription class="text-center text-[#6a5744]">
            {{ activeTab === 'login' ? t('login.description') : t('login.registerDescription') }}
          </CardDescription>
        </CardHeader>

        <CardContent class="space-y-4">
          <Tabs v-model="activeTab" class="w-full">
            <TabsList class="grid h-12 w-full grid-cols-2 rounded-full bg-[#f4eadb] p-1">
              <TabsTrigger value="login">{{ t('login.tabs.login') }}</TabsTrigger>
              <TabsTrigger value="register">{{ t('login.tabs.register') }}</TabsTrigger>
            </TabsList>

            <TabsContent value="login" class="mt-5">
              <form class="space-y-4" @submit.prevent="handleLogin">
                <div class="grid gap-2">
                  <Label for="username">{{ t('login.username') }}</Label>
                  <Input id="username" v-model="loginUsername" type="text" placeholder="admin" required />
                </div>
                <div class="grid gap-2">
                  <Label for="password">{{ t('login.password') }}</Label>
                  <Input id="password" v-model="loginPassword" type="password" required />
                </div>
                <Button class="h-11 w-full rounded-full bg-[#21160f] text-white hover:bg-[#2f2016]" type="submit" :disabled="isLoading">
                  {{ isLoading ? t('login.submitting') : t('login.submit') }}
                </Button>
              </form>
            </TabsContent>

            <TabsContent value="register" class="mt-5">
              <form class="space-y-4" @submit.prevent="handleRegister">
                <div class="grid gap-2">
                  <Label for="tenant-name">{{ t('login.tenantName') }}</Label>
                  <Input id="tenant-name" v-model="registerTenantName" type="text" :placeholder="t('login.tenantNamePlaceholder')" required />
                </div>
                <div class="grid gap-2">
                  <Label for="display-name">{{ t('login.displayName') }}</Label>
                  <Input id="display-name" v-model="registerDisplayName" type="text" :placeholder="t('login.displayNamePlaceholder')" />
                </div>
                <div class="grid gap-2">
                  <Label for="register-username">{{ t('login.username') }}</Label>
                  <Input id="register-username" v-model="registerUsername" type="text" :placeholder="t('login.usernamePlaceholder')" required />
                </div>
                <div class="grid gap-2">
                  <Label for="register-password">{{ t('login.password') }}</Label>
                  <Input id="register-password" v-model="registerPassword" type="password" required />
                </div>
                <div class="grid gap-2">
                  <Label for="register-password-confirm">{{ t('login.passwordConfirm') }}</Label>
                  <Input id="register-password-confirm" v-model="registerPasswordConfirm" type="password" required />
                </div>
                <Button class="h-11 w-full rounded-full bg-[#21160f] text-white hover:bg-[#2f2016]" type="submit" :disabled="isLoading">
                  {{ isLoading ? t('login.registerSubmitting') : t('login.registerSubmit') }}
                </Button>
              </form>
            </TabsContent>
          </Tabs>

          <div v-if="error" class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-600" role="alert">
            {{ error }}
          </div>
        </CardContent>

        <CardFooter class="justify-center text-center text-xs leading-6 text-[#7b6651]">
          {{ activeTab === 'login' ? t('login.footer') : t('login.registerFooter') }}
        </CardFooter>
      </Card>
    </div>
  </div>
</template>
