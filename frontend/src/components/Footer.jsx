import { Scale } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="bg-[#0F1A2E] border-t border-[#334155] mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-[#F59E0B] rounded-md">
              <Scale className="w-4 h-4 text-[#0F1A2E]" />
            </div>
            <span className="text-[#F8FAFC] font-semibold">
              Legal<span className="text-[#F59E0B]">Clear</span>
            </span>

          </div>
          <p className="text-[#94A3B8] text-xs text-center sm:text-right max-w-md leading-relaxed">
            LegalClear provides plain-English summaries for informational
            purposes only. This is not legal advice. Consult a qualified lawyer
            for important legal decisions.
          </p>
        </div>
      </div>
    </footer>
  )
}
