import { useCallback, useEffect, useRef } from 'react'
import { createVoiceSocket, type VoiceSocket } from '../services/websocket'
import {
  createInterruptEvent,
  createSessionStartEvent,
  createUserTranscriptEvent,
} from '../services/voiceProtocol'
import { useVoiceStore } from '../store/voiceStore'
import type {
  BrowserSpeechRecognition,
  ServerVoiceEvent,
  SpeechRecognitionEvent,
} from '../types/voice'

const INTERRUPTION_RMS_THRESHOLD = 0.045
const INTERRUPTION_FRAMES_REQUIRED = 5
const RECONNECT_BASE_DELAY_MS = 500
const RECONNECT_MAX_DELAY_MS = 8000
const RECONNECT_MAX_ATTEMPTS = 8

const getSpeechRecognitionCtor = () =>
  window.SpeechRecognition ?? window.webkitSpeechRecognition

const isSpeechRecognitionSupported = () => Boolean(getSpeechRecognitionCtor())

export const useVoiceSession = () => {
  const socketRef = useRef<VoiceSocket | null>(null)
  const recognitionRef = useRef<BrowserSpeechRecognition | null>(null)
  const mediaStreamRef = useRef<MediaStream | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animationFrameRef = useRef<number | null>(null)
  const isRecognitionActiveRef = useRef(false)
  const shouldListenRef = useRef(false)
  const isSpeakingRef = useRef(false)
  const cancelingForInterruptRef = useRef(false)
  const interruptionFrameCountRef = useRef(0)
  const reconnectAttemptRef = useRef(0)
  const reconnectTimerRef = useRef<number | null>(null)
  const sessionActiveRef = useRef(false)
  const intentionalCloseRef = useRef(false)
  const connectSocketRef = useRef<(() => void) | null>(null)

  const {
    state,
    connectionState,
    partialTranscript,
    transcripts,
    error,
    assistantQueue,
    transitionTo,
    setConnectionState,
    setPartialTranscript,
    clearPartialTranscript,
    addTranscript,
    setError,
    clearError,
    enqueueAssistantSpeech,
    dequeueAssistantSpeech,
    clearAssistantQueue,
  } = useVoiceStore()

  const stopRecognition = useCallback(() => {
    shouldListenRef.current = false

    if (!recognitionRef.current || !isRecognitionActiveRef.current) return

    try {
      recognitionRef.current.stop()
    } catch {
      isRecognitionActiveRef.current = false
    }
  }, [])

  const clearReconnectTimer = useCallback(() => {
    if (reconnectTimerRef.current === null) return

    window.clearTimeout(reconnectTimerRef.current)
    reconnectTimerRef.current = null
  }, [])

  const startRecognition = useCallback(() => {
    if (!recognitionRef.current || isRecognitionActiveRef.current) return

    shouldListenRef.current = true

    try {
      recognitionRef.current.start()
      isRecognitionActiveRef.current = true
      transitionTo('LISTENING')
    } catch (speechError) {
      const message = speechError instanceof Error ? speechError.message : 'Speech recognition failed'
      setError(message)
    }
  }, [setError, transitionTo])

  const cleanupAudio = useCallback(() => {
    if (animationFrameRef.current !== null) {
      window.cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = null
    }

    recognitionRef.current?.abort()
    recognitionRef.current = null
    isRecognitionActiveRef.current = false
    shouldListenRef.current = false

    mediaStreamRef.current?.getTracks().forEach((track) => track.stop())
    mediaStreamRef.current = null

    audioContextRef.current?.close()
    audioContextRef.current = null
    analyserRef.current = null

    cancelingForInterruptRef.current = true
    window.speechSynthesis.cancel()
    isSpeakingRef.current = false
  }, [])

  const handleInterrupt = useCallback(() => {
    if (!isSpeakingRef.current) return

    window.speechSynthesis.cancel()
    isSpeakingRef.current = false
    clearAssistantQueue()
    socketRef.current?.send(createInterruptEvent())
    transitionTo('INTERRUPTED')
    addTranscript('system', 'Assistant speech interrupted.', true)

    window.setTimeout(() => {
      if (recognitionRef.current) {
        startRecognition()
      }
    }, 100)
  }, [addTranscript, clearAssistantQueue, startRecognition, transitionTo])

  const monitorInterruption = useCallback(() => {
    const analyser = analyserRef.current

    if (!analyser) return

    const samples = new Uint8Array(analyser.fftSize)

    const tick = () => {
      analyser.getByteTimeDomainData(samples)

      let sum = 0
      for (const sample of samples) {
        const normalized = (sample - 128) / 128
        sum += normalized * normalized
      }

      const rms = Math.sqrt(sum / samples.length)

      if (isSpeakingRef.current && rms > INTERRUPTION_RMS_THRESHOLD) {
        interruptionFrameCountRef.current += 1
      } else {
        interruptionFrameCountRef.current = 0
      }

      if (interruptionFrameCountRef.current >= INTERRUPTION_FRAMES_REQUIRED) {
        interruptionFrameCountRef.current = 0
        handleInterrupt()
      }

      animationFrameRef.current = window.requestAnimationFrame(tick)
    }

    animationFrameRef.current = window.requestAnimationFrame(tick)
  }, [handleInterrupt])

  const speakText = useCallback(
    (text: string) => {
      stopRecognition()
      window.speechSynthesis.cancel()

      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 1
      utterance.pitch = 1

      utterance.onstart = () => {
        isSpeakingRef.current = true
        transitionTo('SPEAKING')
      }

      utterance.onend = () => {
        isSpeakingRef.current = false
        if (useVoiceStore.getState().state === 'SPEAKING') {
          startRecognition()
        }
      }

      utterance.onerror = () => {
        if (cancelingForInterruptRef.current) {
          cancelingForInterruptRef.current = false
          return
        }

        isSpeakingRef.current = false
        setError('Speech synthesis failed.')
      }

      window.speechSynthesis.speak(utterance)
    },
    [setError, startRecognition, stopRecognition, transitionTo],
  )

  const handleServerEvent = useCallback(
    (event: ServerVoiceEvent) => {
      if (event.type === 'ERROR') {
        setError(event.payload.message)
        addTranscript('system', event.payload.message, true)
        return
      }

      const text = event.payload.text
      addTranscript('assistant', text, true)
      enqueueAssistantSpeech(text)
    },
    [addTranscript, enqueueAssistantSpeech, setError],
  )

  const connectSocket = useCallback(() => {
    clearReconnectTimer()

    const socket = createVoiceSocket()
    socketRef.current = socket
    intentionalCloseRef.current = false
    setConnectionState(reconnectAttemptRef.current > 0 ? 'reconnecting' : 'connecting')

    socket.onOpen(() => {
      reconnectAttemptRef.current = 0
      clearReconnectTimer()
      setConnectionState('connected')
      clearError()
      socket.send(createSessionStartEvent())
      startRecognition()
    })

    socket.onClose(() => {
      socketRef.current = null

      if (intentionalCloseRef.current || !sessionActiveRef.current) {
        setConnectionState('disconnected')
        return
      }

      setConnectionState('reconnecting')
      if (useVoiceStore.getState().state !== 'RECONNECTING') {
        transitionTo('RECONNECTING')
      }
      shouldListenRef.current = false

      if (isRecognitionActiveRef.current) {
        try {
          recognitionRef.current?.stop()
        } catch {
          isRecognitionActiveRef.current = false
        }
      }

      if (reconnectAttemptRef.current >= RECONNECT_MAX_ATTEMPTS) {
        setError('Connection lost. Please start the session again.')
        sessionActiveRef.current = false
        return
      }

      const delay = Math.min(
        RECONNECT_BASE_DELAY_MS * 2 ** reconnectAttemptRef.current,
        RECONNECT_MAX_DELAY_MS,
      )
      reconnectAttemptRef.current += 1

      reconnectTimerRef.current = window.setTimeout(() => {
        reconnectTimerRef.current = null
        if (sessionActiveRef.current && !intentionalCloseRef.current) {
          connectSocketRef.current?.()
        }
      }, delay)
    })

    socket.onMessage(handleServerEvent)
    socket.connect()
  }, [
    clearError,
    clearReconnectTimer,
    handleServerEvent,
    setConnectionState,
    setError,
    startRecognition,
    transitionTo,
  ])

  useEffect(() => {
    connectSocketRef.current = connectSocket
  }, [connectSocket])

  const initializeRecognition = useCallback(() => {
    const SpeechRecognition = getSpeechRecognitionCtor()

    if (!SpeechRecognition) {
      setError('This browser does not support the Web Speech API.')
      return null
    }

    const recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.maxAlternatives = 1
    recognition.lang = navigator.language || 'en-US'

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interim = ''
      let finalText = ''

      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const result = event.results[index]
        const transcript = result[0]?.transcript ?? ''

        if (result.isFinal) {
          finalText += transcript
        } else {
          interim += transcript
        }
      }

      if (interim.trim()) {
        setPartialTranscript(interim.trim())
      }

      if (finalText.trim()) {
        const text = finalText.trim()
        clearPartialTranscript()
        addTranscript('user', text, true)
        transitionTo('PROCESSING')
        socketRef.current?.send(createUserTranscriptEvent(text))
      }
    }

    recognition.onerror = (event) => {
      if (event.error === 'no-speech' || event.error === 'aborted') return
      setError(event.message || `Speech recognition error: ${event.error}`)
    }

    recognition.onend = () => {
      isRecognitionActiveRef.current = false

      if (shouldListenRef.current && !isSpeakingRef.current) {
        window.setTimeout(() => startRecognition(), 150)
      }
    }

    recognitionRef.current = recognition
    return recognition
  }, [
    addTranscript,
    clearPartialTranscript,
    setError,
    setPartialTranscript,
    startRecognition,
    transitionTo,
  ])

  const initializeInterruptionMonitor = useCallback(async () => {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    })

    const audioContext = new AudioContext()
    const source = audioContext.createMediaStreamSource(stream)
    const analyser = audioContext.createAnalyser()
    analyser.fftSize = 1024
    source.connect(analyser)

    mediaStreamRef.current = stream
    audioContextRef.current = audioContext
    analyserRef.current = analyser

    monitorInterruption()
  }, [monitorInterruption])

  const startSession = useCallback(async () => {
    clearError()

    if (state === 'REQUIRES_INTERACTION') {
      transitionTo('IDLE')
    }

    try {
      if (!isSpeechRecognitionSupported()) {
        setError('This browser does not support the Web Speech API.')
        return
      }

      await initializeInterruptionMonitor()
      initializeRecognition()
      sessionActiveRef.current = true
      reconnectAttemptRef.current = 0
      connectSocket()
    } catch (sessionError) {
      const message =
        sessionError instanceof Error ? sessionError.message : 'Unable to start the voice session.'
      setError(message)
    }
  }, [
    clearError,
    connectSocket,
    initializeInterruptionMonitor,
    initializeRecognition,
    setError,
    state,
    transitionTo,
  ])

  const endSession = useCallback(() => {
    intentionalCloseRef.current = true
    sessionActiveRef.current = false
    reconnectAttemptRef.current = 0
    clearReconnectTimer()
    socketRef.current?.close()
    socketRef.current = null
    cleanupAudio()
    setConnectionState('disconnected')
    transitionTo('IDLE')
  }, [cleanupAudio, clearReconnectTimer, setConnectionState, transitionTo])

  useEffect(() => {
    if (assistantQueue.length === 0 || isSpeakingRef.current) return

    const next = dequeueAssistantSpeech()
    if (next) {
      speakText(next)
    }
  }, [assistantQueue.length, dequeueAssistantSpeech, speakText])

  useEffect(
    () => () => {
      intentionalCloseRef.current = true
      sessionActiveRef.current = false
      clearReconnectTimer()
      socketRef.current?.close()
      cleanupAudio()
    },
    [cleanupAudio, clearReconnectTimer],
  )

  return {
    state,
    connectionState,
    partialTranscript,
    transcripts,
    error,
    startSession,
    endSession,
    supportsSpeechRecognition: isSpeechRecognitionSupported(),
  }
}
