import { Download, Mail, RotateCcw } from 'lucide-react'

export default function ActionBar({ onDownload, onEmail, onReset, isGeneratingPdf }) {
  return (
    <div className="sticky top-20 z-40 bg-[#0F1A2E]/95 backdrop-blur border-b border-[#334155] px-4 py-3 mb-6">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
        <p className="text-[#94A3B8] text-sm font-medium">Translation complete</p>
        <div className="flex items-center gap-3">
          <button
            onClick={onDownload}
            disabled={isGeneratingPdf}
            className="flex items-center gap-2 border border-[#334155] hover:border-[#F8FAFC] text-[#F8FAFC] text-sm font-medium px-4 py-2 rounded-lg transition-all disabled:opacity-50"
          >
            <Download className="w-4 h-4" />
            {isGeneratingPdf ? 'Generating…' : 'Download PDF'}
          </button>
          <button
            onClick={onEmail}
            className="flex items-center gap-2 bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-sm font-medium px-4 py-2 rounded-lg transition-all"
          >
            <Mail className="w-4 h-4" />
            Send via Email
          </button>
          <button
            onClick={onReset}
            className="flex items-center gap-2 text-[#94A3B8] hover:text-[#F8FAFC] text-sm transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            New Document
          </button>
        </div>
      </div>
    </div>
  )
}
