import { useState, useEffect } from 'react'
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

export default function StreamingSection({ section, index, isLast = false }) {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    const timeout = setTimeout(() => setIsVisible(true), index * 150)
    return () => clearTimeout(timeout)
  }, [index])

  const flagCount = section.risk_flags?.length || 0
  const catColour = CATEGORY_COLOURS[section.category] || CATEGORY_COLOURS['Other']

  return (
    <div
      className={`transform transition-all duration-500 ease-out ${
        isVisible ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'
      }`}
    >
      <div className={`bg-[#1A2F4E] border rounded-xl overflow-hidden mb-3 transition-colors ${
          isLast ? 'border-[#F59E0B] shadow-[0_0_0_2px_rgba(245,158,11,0.2)] animate-pulse-border' : 'border-[#334155]'
        }`}>
        {/* Header row — matches SectionAccordion */}
        <div className="flex items-center justify-between gap-4 px-4 py-4">
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
          </div>
        </div>

        {/* Body */}
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

          {section.risk_flags?.map((raw, i) => {
            if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return null
            const flag = {
              severity: (raw.severity || raw.level || raw.type || 'NOTE').toUpperCase(),
              title: raw.title || raw.name || raw.label || '',
              explanation: raw.explanation || raw.description || raw.text || '',
            }
            return <RiskFlag key={i} flag={flag} />
          })}

          {isLast && (
            <div className="mt-4 pt-3 border-t border-[#334155] flex items-center gap-2 text-[#10B981] text-xs">
              <div className="w-2 h-2 bg-[#10B981] rounded-full animate-pulse"></div>
              Processing this section...
            </div>
          )}
        </div>
      </div>
    </div>
  )
}