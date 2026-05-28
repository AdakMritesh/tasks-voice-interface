import { ConnectionBanner } from '../components/ConnectionBanner'
import { TranscriptPanel } from '../components/TranscriptPanel'
import { VoiceOrb } from '../components/VoiceOrb'
import { useVoiceSession } from '../hooks/useVoiceSession'

export const App = () => {
  const {
    state,
    connectionState,
    partialTranscript,
    transcripts,
    error,
    startSession,
    endSession,
    supportsSpeechRecognition,
  } = useVoiceSession()

  return (
    <main className="app-shell">
      <ConnectionBanner connectionState={connectionState} voiceState={state} error={error} />

      <section className="workspace">
        <div className="session-column">
          <div>
            <p className="eyebrow">Voice task manager</p>
            <h1>Frontend voice runtime</h1>
            <p className="lede">Phase 1 browser session with mock realtime responses.</p>
          </div>

          <VoiceOrb
            state={state}
            supportsSpeechRecognition={supportsSpeechRecognition}
            onStart={startSession}
            onEnd={endSession}
          />

          {error ? <p className="error-message">{error}</p> : null}
        </div>

        <TranscriptPanel partialTranscript={partialTranscript} transcripts={transcripts} />
      </section>
    </main>
  )
}
