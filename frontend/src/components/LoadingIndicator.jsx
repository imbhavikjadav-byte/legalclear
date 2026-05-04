import { Scale, X } from 'lucide-react'

export default function LoadingIndicator({ onStop }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-6">
      <div className="relative">
        <div className="w-16 h-16 rounded-full border-4 border-[#334155] border-t-[#F59E0B] animate-spin" />
        <div className="absolute inset-0 flex items-center justify-center">
          <Scale className="w-6 h-6 text-[#F59E0B]" />
        </div>
      </div>
      <div className="text-center">
        <p className="text-[#F8FAFC] font-semibold text-lg animate-pulse">
          Uploading your file and connecting to the server…
        </p>
        <p className="text-[#94A3B8] text-sm mt-1">
          Preparing your document for analysis and waiting for the server to begin streaming.
        </p>
      </div>
      <div className="flex gap-1.5">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="w-2 h-2 rounded-full bg-[#F59E0B] animate-bounce"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
      {onStop && (
        <button
          onClick={onStop}
          className="flex items-center gap-2 mt-2 px-4 py-2 rounded-lg border border-[#475569] text-[#94A3B8] hover:border-[#EF4444] hover:text-[#EF4444] text-sm transition-colors"
        >
          <X className="w-4 h-4" />
          Cancel and go back
        </button>
      )}
    </div>
  )
}
