<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import TheHeader from '@/components/layout/TheHeader.vue'
import TheSidebar from '@/components/layout/TheSidebar.vue'
import { useAuth } from '@/composables/useAuth'
import { useMobileNav } from '@/composables/useMobileNav'

const { isMobileNavOpen, closeMobileNav } = useMobileNav()
const { role } = useAuth()
const { t } = useI18n()
const isTenant = computed(() => role.value === 'tenant')
</script>

<template>
  <div
    v-if="isTenant"
    class="relative min-h-screen w-full overflow-hidden bg-[linear-gradient(180deg,#fbf8f1_0%,#f2f6ef_44%,#eef5f3_100%)] selection:bg-primary/15"
  >
    <a
      href="#main-content"
      class="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[120] focus:rounded-lg focus:bg-primary focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-primary-foreground"
    >
      {{ t('common.skipToContent') }}
    </a>

    <div aria-hidden="true" class="pointer-events-none fixed inset-0 overflow-hidden">
      <div class="absolute left-[-8%] top-[-3%] h-[34rem] w-[34rem] rounded-full bg-[#cfe0bf]/28 blur-[140px]"></div>
      <div class="absolute right-[-10%] top-[8%] h-[28rem] w-[28rem] rounded-full bg-[#b8d7ce]/24 blur-[130px]"></div>
      <div class="absolute bottom-[-14%] left-[24%] h-[28rem] w-[28rem] rounded-full bg-[#f0d9b6]/22 blur-[135px]"></div>
      <div class="absolute inset-x-[10%] top-[8.5rem] h-px bg-gradient-to-r from-transparent via-[#a8beaa]/45 to-transparent"></div>
      <div class="absolute inset-x-[6%] bottom-0 h-[38%] bg-[radial-gradient(circle_at_bottom,rgba(255,255,255,0.22),transparent_68%)]"></div>
    </div>

    <TheHeader class="relative z-20" />

    <main id="main-content" tabindex="-1" class="relative z-10 px-4 py-6 focus:outline-none md:px-8 md:py-10">
      <div class="mx-auto max-w-[1320px] animate-fade-in">
        <RouterView v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </RouterView>
      </div>
    </main>
  </div>

  <div v-else class="relative min-h-screen w-full flex flex-col bg-[linear-gradient(180deg,#f7f8f2_0%,#f1f6f2_46%,#eef4f6_100%)] selection:bg-primary/15">
    <a
      href="#main-content"
      class="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[120] focus:rounded-lg focus:bg-primary focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-primary-foreground"
    >
      {{ t('common.skipToContent') }}
    </a>

    <!-- 背景装饰渐变 -->
    <div aria-hidden="true" class="fixed inset-0 pointer-events-none overflow-hidden">
      <div class="absolute -top-[12%] -left-[8%] h-[42%] w-[38%] rounded-full bg-[#c8dacb]/24 blur-[130px]"></div>
      <div class="absolute top-[16%] -right-[8%] h-[38%] w-[34%] rounded-full bg-[#c7dbe8]/28 blur-[120px]"></div>
      <div class="absolute -bottom-[12%] left-[16%] h-[34%] w-[30%] rounded-full bg-[#ead5b8]/20 blur-[110px]"></div>
    </div>

    <!-- Header -->
    <TheHeader class="sticky top-0 z-50 glass" />

    <transition name="mobile-nav">
      <div v-if="isMobileNavOpen" class="fixed inset-0 z-[90] md:hidden">
        <button
          type="button"
          class="absolute inset-0 bg-slate-950/25 backdrop-blur-[2px]"
          :aria-label="t('common.close')"
          @click="closeMobileNav"
        />
        <aside class="relative h-full w-72 border-r border-slate-200/60 bg-[linear-gradient(180deg,rgba(255,255,255,0.96)_0%,rgba(244,247,250,0.94)_100%)] p-4 shadow-2xl backdrop-blur-xl">
          <TheSidebar class="pt-16" @navigate="closeMobileNav" />
        </aside>
      </div>
    </transition>

    <div class="flex flex-grow relative z-10">
      <!-- Sidebar -->
      <aside class="hidden md:block w-64 flex-shrink-0 border-r border-slate-200/70 bg-[linear-gradient(180deg,rgba(255,255,255,0.9)_0%,rgba(243,246,249,0.92)_100%)] backdrop-blur-sm">
        <TheSidebar class="sticky top-16 h-[calc(100vh-4rem)] p-4" />
      </aside>

      <!-- Main Content Area -->
      <main id="main-content" tabindex="-1" class="flex-grow overflow-x-hidden p-4 focus:outline-none md:p-8">
        <div class="max-w-7xl mx-auto animate-fade-in">
          <RouterView v-slot="{ Component }">
            <transition name="page" mode="out-in">
              <component :is="Component" />
            </transition>
          </RouterView>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.page-enter-active,
.page-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.mobile-nav-enter-active,
.mobile-nav-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.mobile-nav-enter-from,
.mobile-nav-leave-to {
  opacity: 0;
  transform: translateX(-12px);
}

@media (prefers-reduced-motion: reduce) {
  .page-enter-active,
  .page-leave-active,
  .mobile-nav-enter-active,
  .mobile-nav-leave-active {
    transition: none;
  }

  .page-enter-from,
  .page-leave-to,
  .mobile-nav-enter-from,
  .mobile-nav-leave-to {
    opacity: 1;
    transform: none;
  }
}
</style>
