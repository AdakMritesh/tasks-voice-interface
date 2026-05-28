import type { ClientVoiceEvent, ServerVoiceEvent } from '../types/voice'

export const createSessionStartEvent = (): ClientVoiceEvent => ({
  type: 'SESSION_START',
})

export const createUserTranscriptEvent = (text: string): ClientVoiceEvent => ({
  type: 'USER_TRANSCRIPT',
  payload: { text },
})

export const createInterruptEvent = (): ClientVoiceEvent => ({
  type: 'INTERRUPT',
})

export const parseServerVoiceEvent = (raw: string): ServerVoiceEvent | null => {
  try {
    const parsed = JSON.parse(raw) as ServerVoiceEvent

    if (
      parsed.type === 'ASSISTANT_RESPONSE' ||
      parsed.type === 'ACTION_CONFIRMATION_REQUIRED' ||
      parsed.type === 'ERROR'
    ) {
      return parsed
    }
  } catch {
    return null
  }

  return null
}
