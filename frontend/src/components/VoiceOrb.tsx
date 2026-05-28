import type { VoiceState } from '../types/voice'

interface VoiceOrbProps {
  state: VoiceState
  supportsSpeechRecognition: boolean
  onStart: () => void
  onEnd: () => void
}

const labels: Record<VoiceState, string> = {
  REQUIRES_INTERACTION: 'Start Session',
  IDLE: 'Session Ready',
  LISTENING: 'Listening',
  PROCESSING: 'Processing',
  SPEAKING: 'Speaking',
  INTERRUPTED: 'Interrupted',
  ERROR: 'Retry Session',
  RECONNECTING: 'Reconnecting',
}

export const VoiceOrb = ({
  state,
  supportsSpeechRecognition,
  onStart,
  onEnd,
}: VoiceOrbProps) => {
  const needsStart = state === 'REQUIRES_INTERACTION' || state === 'ERROR'

  return (
    <section className="voice-stage" aria-label="Voice session controls">
      <button
        className={`voice-orb voice-orb-${state.toLowerCase()}`}
        type="button"
        onClick={needsStart ? onStart : onEnd}
        disabled={!supportsSpeechRecognition && needsStart}
      >
        <span className="orb-core" />
        <span className="orb-label">{needsStart ? 'Start Session' : labels[state]}</span>
      </button>

      <p className="voice-caption">
        {supportsSpeechRecognition ? labels[state] : 'Web Speech API unavailable.'}
      </p>
    </section>
  )
}
