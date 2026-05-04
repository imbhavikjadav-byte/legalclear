import { useState, useEffect } from 'react'

const STATUS_MESSAGES = [
  "Identifying parties and their roles...",
  "Translating legal clauses into plain English...",
  "Checking for risk flags and unusual terms...",
  "Cross-referencing dependent clauses...",
  "Reviewing liability and dispute clauses...",
  "Checking data privacy and sharing terms...",
  "Analysing termination and renewal conditions...",
]

export default function StreamingProgress({ isStreaming, streamingComplete, sectionsCount = 0, onStop }) {
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    if (!isStreaming) return

    const messageInterval = setInterval(() => {
      setCurrentMessageIndex(prev => (prev + 1) % STATUS_MESSAGES.length)
    }, 4000)

    return () => clearInterval(messageInterval)
  }, [isStreaming])

  useEffect(() => {
    if (streamingComplete) {
      setProgress(100)
      // Fade out after completion
      const timeout = setTimeout(() => {
        // Component will be unmounted by parent
      }, 1500)
      return () => clearTimeout(timeout)
    }
  }, [streamingComplete])

  if (!isStreaming || streamingComplete) return null

  return (
    <div className="bg-[#1A2F4E] border border-[#334155] rounded-2xl p-6 mb-6 mx-4 sm:mx-6 lg:mx-8">
      <div className="mb-4">
        <h3 className="text-[#F8FAFC] font-semibold text-base mb-2 whitespace-nowrap">
          Analysing your document
          <span className="inline-flex gap-1 ml-1.5 align-middle">
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                className="inline-block w-1 h-1 rounded-full bg-[#F59E0B] animate-bounce"
                style={{ animationDelay: `${i * 0.15}s` }}
              />
            ))}
          </span>
        </h3>
        <p className="text-[#94A3B8] text-sm">
          {STATUS_MESSAGES[currentMessageIndex]}
        </p>
      </div>

      <div className="mb-4">
        <p className="text-[#64748B] text-xs">
          Sections will appear below as they are ready
        </p>
      </div>

      <div className="w-full bg-[#0F1A2E] rounded-full h-2 overflow-hidden">
        <div
          className={`h-full transition-all duration-300 ${
            streamingComplete ? 'bg-[#10B981]' : 'bg-[#F59E0B]'
          }`}
          style={{
            width: streamingComplete ? '100%' : `${Math.min(90, sectionsCount * 10)}%`,
            background: streamingComplete
              ? 'linear-gradient(90deg, #10B981, #34D399)'
              : 'linear-gradient(90deg, #F59E0B, #FCD34D)'
          }}
        ></div>
      </div>

      {sectionsCount > 0 && !streamingComplete && (
        <div className="mt-3">
          <p className="text-[#94A3B8] text-xs">
            ✓ {sectionsCount} sections analysed
          </p>
        </div>
      )}

      {onStop && (
        <div className="mt-4">
          <button
            onClick={onStop}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-[#475569] text-[#94A3B8] hover:border-[#EF4444] hover:text-[#EF4444] text-sm transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
            Cancel and go back
          </button>
        </div>
      )}
    </div>
  )
}