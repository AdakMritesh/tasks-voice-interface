import type { ClientVoiceEvent, ServerVoiceEvent } from '../types/voice'
import { parseServerVoiceEvent } from './voiceProtocol'

type MessageHandler = (event: ServerVoiceEvent) => void
type ConnectionHandler = () => void

export interface VoiceSocket {
  connect(): void
  close(): void
  send(event: ClientVoiceEvent): void
  onMessage(handler: MessageHandler): () => void
  onOpen(handler: ConnectionHandler): () => void
  onClose(handler: ConnectionHandler): () => void
}

export class BrowserVoiceWebSocket implements VoiceSocket {
  private messageHandlers = new Set<MessageHandler>()
  private openHandlers = new Set<ConnectionHandler>()
  private closeHandlers = new Set<ConnectionHandler>()
  private socket: WebSocket | null = null
  private readonly url: string

  constructor(url: string) {
    this.url = url
  }

  connect() {
    if (this.socket && this.socket.readyState !== WebSocket.CLOSED) return

    const socket = new WebSocket(this.url)
    this.socket = socket

    socket.onopen = () => {
      this.openHandlers.forEach((handler) => handler())
    }

    socket.onclose = () => {
      this.closeHandlers.forEach((handler) => handler())
    }

    socket.onerror = () => {
      socket.close()
    }

    socket.onmessage = (message) => {
      if (typeof message.data !== 'string') return

      const event = parseServerVoiceEvent(message.data)
      if (!event) return

      this.messageHandlers.forEach((handler) => handler(event))
    }
  }

  close() {
    this.socket?.close()
    this.socket = null
  }

  send(event: ClientVoiceEvent) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) return

    this.socket.send(JSON.stringify(event))
  }

  onMessage(handler: MessageHandler) {
    this.messageHandlers.add(handler)
    return () => this.messageHandlers.delete(handler)
  }

  onOpen(handler: ConnectionHandler) {
    this.openHandlers.add(handler)
    return () => this.openHandlers.delete(handler)
  }

  onClose(handler: ConnectionHandler) {
    this.closeHandlers.add(handler)
    return () => this.closeHandlers.delete(handler)
  }
}

const assistantEcho = (text: string) =>
  `I heard: "${text}". This is the mock voice backend echoing your transcript.`

export class MockVoiceWebSocket implements VoiceSocket {
  private messageHandlers = new Set<MessageHandler>()
  private openHandlers = new Set<ConnectionHandler>()
  private closeHandlers = new Set<ConnectionHandler>()
  private connected = false
  private timers = new Set<number>()

  connect() {
    if (this.connected) return

    const timer = window.setTimeout(() => {
      this.connected = true
      this.openHandlers.forEach((handler) => handler())
      this.timers.delete(timer)
    }, 250)

    this.timers.add(timer)
  }

  close() {
    this.timers.forEach((timer) => window.clearTimeout(timer))
    this.timers.clear()

    if (!this.connected) return

    this.connected = false
    this.closeHandlers.forEach((handler) => handler())
  }

  send(event: ClientVoiceEvent) {
    if (!this.connected && event.type !== 'SESSION_START') return

    if (event.type === 'INTERRUPT') {
      return
    }

    if (event.type === 'SESSION_START') {
      this.emitLater({
        type: 'ASSISTANT_RESPONSE',
        payload: {
          text: 'Voice session ready. Tell me what you want to do with your tasks.',
        },
      })
      return
    }

    const text = event.payload.text.trim()

    this.emitLater({
      type: 'ASSISTANT_RESPONSE',
      payload: {
        text: assistantEcho(text),
      },
    })
  }

  onMessage(handler: MessageHandler) {
    this.messageHandlers.add(handler)
    return () => this.messageHandlers.delete(handler)
  }

  onOpen(handler: ConnectionHandler) {
    this.openHandlers.add(handler)
    return () => this.openHandlers.delete(handler)
  }

  onClose(handler: ConnectionHandler) {
    this.closeHandlers.add(handler)
    return () => this.closeHandlers.delete(handler)
  }

  private emitLater(event: ServerVoiceEvent) {
    const timer = window.setTimeout(() => {
      this.messageHandlers.forEach((handler) => handler(event))
      this.timers.delete(timer)
    }, 650)

    this.timers.add(timer)
  }
}

export const createVoiceSocket = (): VoiceSocket => {
  if (import.meta.env.VITE_USE_MOCK_VOICE === 'true') {
    return new MockVoiceWebSocket()
  }

  return new BrowserVoiceWebSocket(
    import.meta.env.VITE_VOICE_WS_URL ?? 'ws://localhost:8000/ws/voice',
  )
}
