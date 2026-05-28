import type { TranscriptEntry } from '../types/voice'

interface TranscriptPanelProps {
  partialTranscript: string
  transcripts: TranscriptEntry[]
}

export const TranscriptPanel = ({ partialTranscript, transcripts }: TranscriptPanelProps) => (
  <section className="transcript-panel" aria-label="Conversation transcript">
    <div className="panel-heading">
      <h2>Transcript</h2>
      <span>{transcripts.length} messages</span>
    </div>

    <div className="transcript-list">
      {transcripts.length === 0 ? (
        <p className="empty-transcript">The session transcript will appear here.</p>
      ) : (
        transcripts.map((entry) => (
          <article key={entry.id} className={`transcript-entry transcript-${entry.role}`}>
            <span>{entry.role}</span>
            <p>{entry.text}</p>
          </article>
        ))
      )}

      {partialTranscript ? (
        <article className="transcript-entry transcript-user transcript-partial">
          <span>listening</span>
          <p>{partialTranscript}</p>
        </article>
      ) : null}
    </div>
  </section>
)
