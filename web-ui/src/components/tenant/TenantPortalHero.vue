<script setup lang="ts">
import { Sparkles } from 'lucide-vue-next'

interface HeroStat {
  label: string
  value: string
  detail?: string
}

defineProps<{
  eyebrow: string
  title: string
  description: string
  note?: string
  stats: HeroStat[]
}>()
</script>

<template>
  <section class="relative overflow-hidden rounded-[36px] border border-[#eadfce] bg-[radial-gradient(circle_at_top_left,rgba(178,214,196,0.36),transparent_34%),radial-gradient(circle_at_top_right,rgba(198,88,46,0.18),transparent_28%),linear-gradient(145deg,#fffdf7_0%,#f7f0e4_46%,#f5efe8_100%)] px-6 py-7 shadow-[0_32px_90px_rgba(64,45,30,0.12)] md:px-8 md:py-9">
    <div aria-hidden="true" class="pointer-events-none absolute inset-0">
      <div class="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#b9936b]/45 to-transparent"></div>
      <div class="absolute bottom-0 left-[10%] h-40 w-40 rounded-full bg-[#d9b26f]/12 blur-3xl"></div>
      <div class="absolute right-[8%] top-[18%] h-44 w-44 rounded-full bg-[#91b7a0]/16 blur-3xl"></div>
    </div>

    <div class="relative z-10 flex flex-col gap-8 xl:flex-row xl:items-end xl:justify-between">
      <div class="max-w-3xl space-y-5">
        <div class="flex flex-wrap items-center gap-3">
          <span class="inline-flex items-center gap-2 rounded-full border border-[#d7c8b4] bg-white/70 px-4 py-1.5 text-[11px] font-bold uppercase tracking-[0.28em] text-[#7a6144] shadow-sm backdrop-blur">
            <Sparkles class="h-3.5 w-3.5 text-[#c6582e]" />
            CatchYu
          </span>
          <span class="inline-flex rounded-full border border-white/70 bg-[#f7f2ea]/80 px-4 py-1.5 text-[11px] font-semibold tracking-[0.18em] text-[#8a7358]">
            {{ eyebrow }}
          </span>
        </div>

        <div class="space-y-4">
          <h1 class="max-w-3xl text-3xl font-black tracking-[-0.04em] text-[#241a12] md:text-[3.4rem] md:leading-[1.03]">
            {{ title }}
          </h1>
          <p class="max-w-2xl text-sm leading-7 text-[#685542] md:text-base">
            {{ description }}
          </p>
        </div>

        <div class="flex flex-wrap gap-3">
          <p class="inline-flex rounded-full border border-[#decfb9] bg-white/78 px-4 py-2 text-xs font-semibold text-[#64503d] shadow-sm">
            {{ note }}
          </p>
          <p class="inline-flex rounded-full border border-[#d6dece] bg-[#edf4ef]/82 px-4 py-2 text-xs font-semibold text-[#426251] shadow-sm">
            实时联动当前租户的任务与结果
          </p>
        </div>
      </div>

      <div class="flex flex-wrap gap-3 xl:max-w-[24rem] xl:justify-end">
        <slot name="actions" />
      </div>
    </div>

    <div class="relative z-10 mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <article
        v-for="stat in stats"
        :key="stat.label"
        class="rounded-[28px] border border-white/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.78)_0%,rgba(251,247,240,0.94)_100%)] p-5 shadow-[0_22px_48px_rgba(95,70,47,0.09)]"
      >
        <p class="text-[11px] font-bold uppercase tracking-[0.24em] text-[#9b8165]">
          {{ stat.label }}
        </p>
        <p class="mt-3 text-[2rem] font-black tracking-[-0.05em] text-[#241a12]">
          {{ stat.value }}
        </p>
        <p v-if="stat.detail" class="mt-2 text-xs leading-5 text-[#6d5a48]">
          {{ stat.detail }}
        </p>
      </article>
    </div>
  </section>
</template>
