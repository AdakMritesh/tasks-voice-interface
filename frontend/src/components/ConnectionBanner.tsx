import type { ConnectionState, VoiceState } from '../types/voice'

interface ConnectionBannerProps {
  connectionState: ConnectionState
  voiceState: VoiceState
  error: string | null
}

const connectionLabels: Record<ConnectionState, string> = {
  disconnected: 'Disconnected',
  connecting: 'Connecting',
  connected: 'Connected to mock voice socket',
  reconnecting: 'Reconnecting',
}

export const ConnectionBanner = ({ connectionState, voiceState, error }: ConnectionBannerProps) => (
  <header className="connection-banner">
    <div>
      <span className={`status-dot status-dot-${connectionState}`} />
      <span>{connectionLabels[connectionState]}</span>
    </div>
    <div className="state-pill">{error ? 'ERROR' : voiceState}</div>
  </header>
)
