import { create } from 'zustand'
import { v4 as uuid } from 'uuid'
import type { ConnectionState, TranscriptEntry, TranscriptRole, VoiceState } from '../types/voice'

const allowedTransitions: Record<VoiceState, VoiceState[]> = {
  REQUIRES_INTERACTION: ['IDLE', 'ERROR'],
  IDLE: ['LISTENING', 'RECONNECTING', 'ERROR'],
  LISTENING: ['PROCESSING', 'SPEAKING', 'RECONNECTING', 'ERROR', 'IDLE'],
  PROCESSING: ['SPEAKING', 'LISTENING', 'RECONNECTING', 'ERROR'],
  SPEAKING: ['INTERRUPTED', 'LISTENING', 'RECONNECTING', 'ERROR', 'IDLE'],
  INTERRUPTED: ['LISTENING', 'PROCESSING', 'RECONNECTING', 'ERROR'],
  ERROR: ['IDLE', 'RECONNECTING', 'LISTENING'],
  RECONNECTING: ['IDLE', 'LISTENING', 'ERROR'],
}

interface VoiceStore {
  state: VoiceState
  connectionState: ConnectionState
  partialTranscript: string
  transcripts: TranscriptEntry[]
  error: string | null
  assistantQueue: string[]
  transitionTo: (nextState: VoiceState) => boolean
  setConnectionState: (connectionState: ConnectionState) => void
  setPartialTranscript: (text: string) => void
  clearPartialTranscript: () => void
  addTranscript: (role: TranscriptRole, text: string, final?: boolean) => void
  setError: (message: string) => void
  clearError: () => void
  enqueueAssistantSpeech: (text: string) => void
  dequeueAssistantSpeech: () => string | undefined
  clearAssistantQueue: () => void
  resetSession: () => void
}

export const useVoiceStore = create<VoiceStore>((set, get) => ({
  state: 'REQUIRES_INTERACTION',
  connectionState: 'disconnected',
  partialTranscript: '',
  transcripts: [],
  error: null,
  assistantQueue: [],

  transitionTo: (nextState) => {
    const currentState = get().state
    const canTransition = allowedTransitions[currentState].includes(nextState)

    if (!canTransition) {
      console.warn(`Invalid voice state transition: ${currentState} -> ${nextState}`)
      return false
    }

    set({ state: nextState })
    return true
  },

  setConnectionState: (connectionState) => set({ connectionState }),
  setPartialTranscript: (partialTranscript) => set({ partialTranscript }),
  clearPartialTranscript: () => set({ partialTranscript: '' }),

  addTranscript: (role, text, final = true) =>
    set((current) => ({
      transcripts: [
        ...current.transcripts,
        {
          id: uuid(),
          role,
          text,
          final,
          createdAt: new Date().toISOString(),
        },
      ],
    })),

  setError: (message) => set({ error: message, state: 'ERROR' }),
  clearError: () => set({ error: null }),

  enqueueAssistantSpeech: (text) =>
    set((current) => ({ assistantQueue: [...current.assistantQueue, text] })),

  dequeueAssistantSpeech: () => {
    const [next, ...remaining] = get().assistantQueue
    set({ assistantQueue: remaining })
    return next
  },

  clearAssistantQueue: () => set({ assistantQueue: [] }),

  resetSession: () =>
    set({
      state: 'REQUIRES_INTERACTION',
      connectionState: 'disconnected',
      partialTranscript: '',
      transcripts: [],
      error: null,
      assistantQueue: [],
    }),
}))
