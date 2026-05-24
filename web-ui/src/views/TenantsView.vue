<script setup lang="ts">
import { Building2, KeyRound, ShieldCheck, Users2 } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import AdminTenantAccessPanel from '@/components/admin/AdminTenantAccessPanel.vue'

const { t } = useI18n()

const featureCards = [
  {
    icon: Building2,
    titleKey: 'tenants.hero.cards.workspace.title',
    descriptionKey: 'tenants.hero.cards.workspace.description',
  },
  {
    icon: KeyRound,
    titleKey: 'tenants.hero.cards.codes.title',
    descriptionKey: 'tenants.hero.cards.codes.description',
  },
  {
    icon: ShieldCheck,
    titleKey: 'tenants.hero.cards.access.title',
    descriptionKey: 'tenants.hero.cards.access.description',
  },
  {
    icon: Users2,
    titleKey: 'tenants.hero.cards.members.title',
    descriptionKey: 'tenants.hero.cards.members.description',
  },
]
</script>

<template>
  <div class="space-y-6">
    <section class="overflow-hidden rounded-[32px] border border-slate-200/80 bg-[linear-gradient(135deg,#08111f_0%,#13233a_44%,#d2e0ee_220%)] px-6 py-7 text-white shadow-[0_28px_90px_rgba(15,23,42,0.2)] md:px-8">
      <div class="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
        <div class="max-w-3xl">
          <p class="text-xs font-black uppercase tracking-[0.32em] text-slate-300">
            CatchYu Console
          </p>
          <h1 class="mt-3 text-3xl font-black tracking-tight text-white md:text-4xl">
            {{ t('tenants.hero.title') }}
          </h1>
          <p class="mt-3 max-w-2xl text-sm leading-7 text-slate-300 md:text-base">
            {{ t('tenants.hero.description') }}
          </p>
        </div>
        <div class="rounded-[28px] border border-white/10 bg-white/8 px-5 py-4 backdrop-blur">
          <p class="text-xs font-black uppercase tracking-[0.24em] text-slate-400">
            {{ t('tenants.hero.panelLabel') }}
          </p>
          <p class="mt-2 text-sm leading-7 text-slate-200">
            {{ t('tenants.hero.panelDescription') }}
          </p>
        </div>
      </div>

      <div class="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <article
          v-for="card in featureCards"
          :key="card.titleKey"
          class="rounded-[24px] border border-white/10 bg-white/10 p-4 backdrop-blur"
        >
          <component :is="card.icon" class="h-5 w-5 text-[#a6d0ff]" />
          <h2 class="mt-4 text-base font-black text-white">
            {{ t(card.titleKey) }}
          </h2>
          <p class="mt-2 text-sm leading-6 text-slate-300">
            {{ t(card.descriptionKey) }}
          </p>
        </article>
      </div>
    </section>

    <AdminTenantAccessPanel />
  </div>
</template>
