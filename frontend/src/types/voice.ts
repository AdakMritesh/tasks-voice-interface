export type VoiceState =
  | 'REQUIRES_INTERACTION'
  | 'IDLE'
  | 'LISTENING'
  | 'PROCESSING'
  | 'SPEAKING'
  | 'INTERRUPTED'
  | 'ERROR'
  | 'RECONNECTING'

export type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'reconnecting'

export type TranscriptRole = 'user' | 'assistant' | 'system'

export interface TranscriptEntry {
  id: string
  role: TranscriptRole
  text: string
  createdAt: string
  final: boolean
}

export interface UserTranscriptEvent {
  type: 'USER_TRANSCRIPT'
  payload: {
    text: string
  }
}

export interface InterruptEvent {
  type: 'INTERRUPT'
}

export interface SessionStartEvent {
  type: 'SESSION_START'
}

export type ClientVoiceEvent = UserTranscriptEvent | InterruptEvent | SessionStartEvent

export interface AssistantResponseEvent {
  type: 'ASSISTANT_RESPONSE'
  payload: {
    text: string
  }
}

export interface ActionConfirmationRequiredEvent {
  type: 'ACTION_CONFIRMATION_REQUIRED'
  payload: {
    text: string
  }
}

export interface ServerErrorEvent {
  type: 'ERROR'
  payload: {
    message: string
  }
}

export type ServerVoiceEvent =
  | AssistantResponseEvent
  | ActionConfirmationRequiredEvent
  | ServerErrorEvent

export interface SpeechRecognitionAlternative {
  transcript: string
  confidence: number
}

export interface SpeechRecognitionResult {
  readonly isFinal: boolean
  readonly length: number
  item(index: number): SpeechRecognitionAlternative
  [index: number]: SpeechRecognitionAlternative
}

export interface SpeechRecognitionResultList {
  readonly length: number
  item(index: number): SpeechRecognitionResult
  [index: number]: SpeechRecognitionResult
}

export interface SpeechRecognitionEvent extends Event {
  readonly resultIndex: number
  readonly results: SpeechRecognitionResultList
}

export interface SpeechRecognitionErrorEvent extends Event {
  readonly error: string
  readonly message?: string
}

export interface BrowserSpeechRecognition extends EventTarget {
  continuous: boolean
  interimResults: boolean
  lang: string
  maxAlternatives: number
  onend: ((event: Event) => void) | null
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null
  onresult: ((event: SpeechRecognitionEvent) => void) | null
  onspeechstart: ((event: Event) => void) | null
  start(): void
  stop(): void
  abort(): void
}

export interface BrowserSpeechRecognitionConstructor {
  new (): BrowserSpeechRecognition
}

declare global {
  interface Window {
    SpeechRecognition?: BrowserSpeechRecognitionConstructor
    webkitSpeechRecognition?: BrowserSpeechRecognitionConstructor
  }
}
