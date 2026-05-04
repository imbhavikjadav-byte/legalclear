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

export default function StreamingProgress({ isStreaming, streamingComplete, sectionsCount = 0 }) {
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
      <div className="flex items-center gap-3 mb-4">
        <div className="w-3 h-3 bg-[#F59E0B] rounded-full animate-pulse shrink-0"></div>
        <h3 className="text-[#F8FAFC] font-bold text-lg">
          {STATUS_MESSAGES[currentMessageIndex]}
        </h3>
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
        <div className="mt-3 text-center">
          <p className="text-[#94A3B8] text-xs">
            ✓ {sectionsCount} sections analysed
          </p>
        </div>
      )}
    </div>
  )
}