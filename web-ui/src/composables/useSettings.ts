import { ref, onMounted } from 'vue'
import * as settingsApi from '@/api/settings'
import type {
  AiAccountItem,
  AiAccountPayload,
  AiSettings,
  RotationSettings,
  SystemStatus,
  TenantNotificationChannel,
} from '@/api/settings'

export function useSettings() {
  const tenantNotificationChannels = ref<TenantNotificationChannel[]>([])
  const aiAccounts = ref<AiAccountItem[]>([])
  const aiSettings = ref<AiSettings>({})
  const rotationSettings = ref<RotationSettings>({})
  const systemStatus = ref<SystemStatus | null>(null)
  const isReady = ref(false)
  
  const isLoading = ref(false)
  const isSaving = ref(false)
  const error = ref<Error | null>(null)

  async function fetchAll() {
    isLoading.value = true
    error.value = null
    try {
      const [tenantChannels, aiAccountResponse, aiConfig, rotation, status] = await Promise.all([
        settingsApi.getTenantNotificationChannels(),
        settingsApi.getAiAccounts(),
        settingsApi.getAiSettings(),
        settingsApi.getRotationSettings(),
        settingsApi.getSystemStatus()
      ])
      tenantNotificationChannels.value = tenantChannels.channels
      aiAccounts.value = aiAccountResponse.items
      aiSettings.value = aiConfig
      rotationSettings.value = rotation
      systemStatus.value = status
    } catch (e) {
      if (e instanceof Error) error.value = e
    } finally {
      isLoading.value = false
      isReady.value = true
    }
  }

  async function refreshStatus() {
    isLoading.value = true
    error.value = null
    try {
      systemStatus.value = await settingsApi.getSystemStatus()
    } catch (e) {
      if (e instanceof Error) error.value = e
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function saveTenantNotificationChannels(channels: TenantNotificationChannel[]) {
    isSaving.value = true
    try {
      const [channelSettings, status] = await Promise.all([
        settingsApi.updateTenantNotificationChannels(channels),
        settingsApi.getSystemStatus()
      ])
      tenantNotificationChannels.value = channelSettings.channels
      systemStatus.value = status
    } catch (e) {
      if (e instanceof Error) error.value = e
      throw e
    } finally {
      isSaving.value = false
    }
  }

  async function saveAiSettings() {
    isSaving.value = true
    try {
      const payload = { ...aiSettings.value }
      const apiKey = (payload.OPENAI_API_KEY || '').trim()
      if (apiKey) {
        payload.OPENAI_API_KEY = apiKey
      } else {
        delete payload.OPENAI_API_KEY
      }
      await settingsApi.updateAiSettings(payload)
      if (aiSettings.value.OPENAI_API_KEY) {
        aiSettings.value.OPENAI_API_KEY = ''
      }
      // Refresh status
      systemStatus.value = await settingsApi.getSystemStatus()
    } catch (e) {
      if (e instanceof Error) error.value = e
      throw e
    } finally {
      isSaving.value = false
    }
  }

  async function refreshAiAccounts() {
    aiAccounts.value = (await settingsApi.getAiAccounts()).items
  }

  async function createAiAccount(payload: AiAccountPayload) {
    isSaving.value = true
    try {
      await settingsApi.createAiAccount(payload)
      await refreshAiAccounts()
      systemStatus.value = await settingsApi.getSystemStatus()
    } catch (e) {
      if (e instanceof Error) error.value = e
      throw e
    } finally {
      isSaving.value = false
    }
  }

  async function updateAiAccount(accountId: number, payload: Partial<AiAccountPayload>) {
    isSaving.value = true
    try {
      await settingsApi.updateAiAccount(accountId, payload)
      await refreshAiAccounts()
      systemStatus.value = await settingsApi.getSystemStatus()
    } catch (e) {
      if (e instanceof Error) error.value = e
      throw e
    } finally {
      isSaving.value = false
    }
  }

  async function deleteAiAccount(accountId: number) {
    isSaving.value = true
    try {
      await settingsApi.deleteAiAccount(accountId)
      await refreshAiAccounts()
      systemStatus.value = await settingsApi.getSystemStatus()
    } catch (e) {
      if (e instanceof Error) error.value = e
      throw e
    } finally {
      isSaving.value = false
    }
  }

  async function testAiAccount(payload: {
    api_key?: string | null
    base_url: string
    model_name: string
  }) {
    isSaving.value = true
    try {
      return await settingsApi.testAiAccount(payload)
    } catch (e) {
      if (e instanceof Error) error.value = e
      throw e
    } finally {
      isSaving.value = false
    }
  }

  async function testExistingAiAccount(accountId: number) {
    isSaving.value = true
    try {
      const result = await settingsApi.testExistingAiAccount(accountId)
      await refreshAiAccounts()
      systemStatus.value = await settingsApi.getSystemStatus()
      return result
    } catch (e) {
      if (e instanceof Error) error.value = e
      throw e
    } finally {
      isSaving.value = false
    }
  }

  async function saveRotationSettings() {
    isSaving.value = true
    try {
      await settingsApi.updateRotationSettings(rotationSettings.value)
    } catch (e) {
      if (e instanceof Error) error.value = e
      throw e
    } finally {
      isSaving.value = false
    }
  }

  async function testAiConnection() {
    isSaving.value = true
    try {
      const payload = { ...aiSettings.value }
      const apiKey = (payload.OPENAI_API_KEY || '').trim()
      if (apiKey) {
        payload.OPENAI_API_KEY = apiKey
      } else {
        delete payload.OPENAI_API_KEY
      }
      const res = await settingsApi.testAiSettings(payload)
      return res
    } catch (e) {
      if (e instanceof Error) error.value = e
      throw e
    } finally {
      isSaving.value = false
    }
  }

  onMounted(fetchAll)

  return {
    tenantNotificationChannels,
    aiAccounts,
    aiSettings,
    rotationSettings,
    systemStatus,
    isLoading,
    isSaving,
    isReady,
    error,
    fetchAll,
    saveTenantNotificationChannels,
    saveAiSettings,
    createAiAccount,
    updateAiAccount,
    deleteAiAccount,
    testAiAccount,
    testExistingAiAccount,
    saveRotationSettings,
    testAiConnection,
    refreshStatus,
  }
}
