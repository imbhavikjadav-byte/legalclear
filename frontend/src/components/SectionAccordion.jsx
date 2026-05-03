import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import RiskFlag from './RiskFlag'

const CATEGORY_COLOURS = {
  'Your Rights': 'bg-[#10B981] text-white',
  'Company Rights': 'bg-[#EF4444] text-white',
  'Your Obligations': 'bg-[#F59E0B] text-white',
  'Company Obligations': 'bg-[#6366F1] text-white',
  'Termination': 'bg-[#EF4444] text-white',
  'Liability & Disputes': 'bg-[#DC2626] text-white',
  'Data & Privacy': 'bg-[#7C3AED] text-white',
  'Payment & Fees': 'bg-[#D97706] text-white',
  'Intellectual Property': 'bg-[#0891B2] text-white',
  'Other': 'bg-[#64748B] text-white',
}

export default function SectionAccordion({ section, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)
  const flagCount = section.risk_flags?.length || 0
  const catColour = CATEGORY_COLOURS[section.category] || CATEGORY_COLOURS['Other']

  return (
    <div className="bg-[#1A2F4E] border border-[#334155] rounded-xl overflow-hidden mb-3 transition-all">
      {/* Header */}
      <button
        onClick={() => setOpen((p) => !p)}
        className="w-full flex items-center justify-between gap-4 px-4 py-4 text-left hover:bg-[#243552] transition-colors"
      >
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <span className="text-[#94A3B8] text-sm font-mono shrink-0">§{section.section_id}</span>
          <span className="text-[#F8FAFC] font-semibold text-sm truncate">{section.title}</span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${catColour}`}>
            {section.category}
          </span>
          {flagCount > 0 && (
            <span className="bg-[#EF4444] text-white text-xs font-bold px-2 py-0.5 rounded-full">
              {flagCount} flag{flagCount > 1 ? 's' : ''}
            </span>
          )}
          {open ? (
            <ChevronUp className="w-4 h-4 text-[#94A3B8]" />
          ) : (
            <ChevronDown className="w-4 h-4 text-[#94A3B8]" />
          )}
        </div>
      </button>

      {/* Content */}
      {open && (
        <div className="px-4 pb-4 border-t border-[#334155]">
          {section.original_excerpt && (
            <details className="mt-3 mb-2">
              <summary className="text-[#94A3B8] text-xs cursor-pointer hover:text-[#F8FAFC] transition-colors mb-1">
                Original text
              </summary>
              <p className="text-[#64748B] text-xs font-mono italic leading-relaxed bg-[#0F1A2E] rounded p-3 mt-1">
                "{section.original_excerpt}"
              </p>
            </details>
          )}
          <p className="text-[#F8FAFC] text-sm leading-relaxed mt-3">{section.plain_english}</p>
          {section.risk_flags?.map((flag, i) => (
            <RiskFlag key={i} flag={flag} />
          ))}
        </div>
      )}
    </div>
  )
}
