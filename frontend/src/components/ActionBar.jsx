import { useRef, useEffect } from 'react'
import { Download, Mail, RotateCcw, CheckCircle2 } from 'lucide-react'

export default function ActionBar({ onDownload, onEmail, onReset, isGeneratingPdf, disabled = false, onHeightChange }) {
  const barRef = useRef(null)

  useEffect(() => {
    const el = barRef.current
    if (!el || !onHeightChange) return
    // Report initial height
    onHeightChange(el.getBoundingClientRect().height)
    // Report on any size change (e.g. banner appears/disappears)
    const observer = new ResizeObserver(([entry]) => {
      onHeightChange(entry.contentRect.height)
    })
    observer.observe(el)
    return () => observer.disconnect()
  }, [onHeightChange])

  return (
    <div
      ref={barRef}
      className="fixed left-0 right-0 top-16 z-40 bg-[#0F1A2E] border-b border-[#334155] sm:sticky sm:left-auto sm:right-auto sm:top-16 sm:mb-6"
    >
      {/* Mobile completion banner — centered */}
      {!disabled && (
        <div className="flex sm:hidden flex-col items-center justify-center gap-0.5 pt-2.5 pb-2 border-b border-[#1E3A5F]">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-[#10B981] shrink-0" />
            <p className="text-[#F8FAFC] text-sm font-semibold">Analysis complete</p>
          </div>
          <p className="text-[#64748B] text-xs text-center leading-snug">Your document has been fully reviewed</p>
        </div>
      )}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2.5">
        {/* Desktop: single row with status on left, buttons on right */}
        <div className="hidden sm:flex items-center justify-between gap-3">
          {!disabled && (
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="w-6 h-6 text-[#10B981] shrink-0" />
              <div className="flex flex-col">
                <p className="text-[#F8FAFC] text-base font-bold tracking-tight leading-tight">Analysis complete</p>
                <span className="text-[#64748B] text-xs">Your document has been fully reviewed</span>
              </div>
            </div>
          )}
          <div className="flex items-center gap-3 ml-auto">
            <button
              onClick={onDownload}
              disabled={isGeneratingPdf || disabled}
              className="flex items-center gap-2 border border-[#334155] hover:border-[#F8FAFC] text-[#F8FAFC] text-sm font-medium px-4 py-2 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Download className="w-4 h-4" />
              {isGeneratingPdf ? 'Generating…' : 'Download PDF'}
            </button>
            <button
              onClick={onEmail}
              disabled={disabled}
              className="flex items-center gap-2 bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-sm font-medium px-4 py-2 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-[#2563EB]"
            >
              <Mail className="w-4 h-4" />
              Send via Email
            </button>
            <button
              onClick={onReset}
              disabled={disabled}
              className="flex items-center gap-2 border border-[#334155] hover:border-[#94A3B8] text-[#94A3B8] hover:text-[#F8FAFC] text-sm font-medium px-4 py-2 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RotateCcw className="w-4 h-4" />
              New Document
            </button>
          </div>
        </div>

        {/* Mobile: single-row buttons, text never wraps */}
        <div className="flex sm:hidden gap-2 w-full">
          <button
            onClick={onDownload}
            disabled={isGeneratingPdf || disabled}
            className="flex flex-1 items-center justify-center gap-1 border border-[#334155] text-[#F8FAFC] font-medium px-2 py-2 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap overflow-hidden text-[clamp(0.6rem,2.5vw,0.75rem)]"
          >
            <Download className="w-3 h-3 shrink-0" />
            {isGeneratingPdf ? 'Generating…' : 'Download PDF'}
          </button>
          <button
            onClick={onEmail}
            disabled={disabled}
            className="flex flex-1 items-center justify-center gap-1 bg-[#2563EB] text-white font-medium px-2 py-2 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap overflow-hidden text-[clamp(0.6rem,2.5vw,0.75rem)]"
          >
            <Mail className="w-3 h-3 shrink-0" />
            Send via Email
          </button>
          <button
            onClick={onReset}
            disabled={disabled}
            className="flex flex-1 items-center justify-center gap-1 border border-[#334155] text-[#94A3B8] font-medium px-2 py-2 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap overflow-hidden text-[clamp(0.6rem,2.5vw,0.75rem)]"
          >
            <RotateCcw className="w-3 h-3 shrink-0" />
            New Document
          </button>
        </div>
      </div>
    </div>
  )
}
