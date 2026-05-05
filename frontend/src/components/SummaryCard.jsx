import { useEffect } from 'react'
import { formatDateTime } from '../utils/formatters'

const RISK_COLOUR = {
  LOW: { bg: 'bg-[#10B981]', border: 'border-[#10B981]', text: 'text-[#10B981]' },
  MEDIUM: { bg: 'bg-[#F59E0B]', border: 'border-[#F59E0B]', text: 'text-[#F59E0B]' },
  HIGH: { bg: 'bg-[#EF4444]', border: 'border-[#EF4444]', text: 'text-[#EF4444]' },
}

export default function SummaryCard({ data, meta, sections, final, isStreaming, streamingComplete, forcedOpenSectionIds, setForcedOpenSectionIds }) {
  // Extract HIGH risks from sections
  const highRisks = sections?.flatMap(section =>
    section.risk_flags?.filter(flag => flag.severity === 'HIGH') || []
  ) || []

  const topRisks = highRisks.slice(0, 3)

  const handlePillClick = (sectionId) => {
    const element = document.getElementById(`section-${sectionId}`)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' })
      setForcedOpenSectionIds(prev => [...prev, sectionId])
    }
  }

  const verdict = meta?.verdict || data?.verdict
  const riskLevel = final?.overall_risk_level || data?.overall_risk_level
  const riskExplanation = final?.overall_risk_explanation || data?.overall_risk_explanation
  const summary = meta?.summary || data?.summary
  const rawParties = meta?.parties ?? data?.parties
  const parties = Array.isArray(rawParties) ? rawParties.filter(p => p && typeof p === 'object') : []
  const totalSections = sections?.length || data?.sections?.length || 0
  const highCount = final?.high_risk_count || data?.high_risk_count || 0
  const mediumCount = final?.medium_risk_count || data?.medium_risk_count || 0
  const noteCount = final?.note_count || data?.note_count || 0

  const streaming = isStreaming && !streamingComplete

  return (
    <div className={`bg-[#1A2F4E] border rounded-2xl p-6 mb-6 transition-colors ${
      streaming ? 'border-[#F59E0B] shadow-[0_0_0_2px_rgba(245,158,11,0.2)] animate-pulse-border' : 'border-[#334155]'
    }`}>
      {/* Section heading */}
      <h3 className="text-[#F8FAFC] font-bold text-lg mb-4">At a Glance</h3>

      {/* ZONE A — Verdict */}
      <div className="mb-6">
        <div className={`border-l-4 rounded-r-lg p-4 ${riskLevel ? RISK_COLOUR[riskLevel]?.border : 'border-[#64748B]'} bg-opacity-8`} style={{ backgroundColor: riskLevel ? `${RISK_COLOUR[riskLevel].bg.replace('bg-', '')}08` : '#64748B08' }}>
          <p className="text-[#94A3B8] text-xs font-mono uppercase tracking-wider mb-2">Quick Verdict</p>
          {verdict ? (
            <p className="text-[#F8FAFC] text-lg leading-relaxed">{verdict}</p>
          ) : (
            <div className={`border rounded-lg p-3 transition-colors ${streaming ? 'border-[#F59E0B] shadow-[0_0_0_2px_rgba(245,158,11,0.2)] animate-pulse-border' : 'border-[#334155]'}`}>
              <div className="flex items-center gap-2 text-[#10B981] text-sm">
                <div className="w-2 h-2 bg-[#10B981] rounded-full animate-pulse shrink-0"></div>
                <span className="text-[#64748B]">Analysing document...</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ZONE B — Overall Risk Level Badge + Explanation */}
      {riskLevel && (
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <span className={`px-4 py-2 rounded-full font-bold text-sm ${RISK_COLOUR[riskLevel]?.bg} text-white`}>
              {riskLevel} RISK
            </span>
          </div>
          {riskExplanation && (
            <p className="text-[#94A3B8] text-sm">{riskExplanation}</p>
          )}
        </div>
      )}

      {/* ZONE C — Top 3 Risk Pills */}
      {highCount > 0 && topRisks.length > 0 && (
        <div className="mb-6">
          <p className="text-[#94A3B8] text-sm font-semibold mb-3">Top Risks</p>
          <div className="flex flex-wrap gap-2">
            {topRisks.map((risk, index) => (
              <button
                key={index}
                onClick={() => handlePillClick(risk.sectionId || sections.find(s => s.risk_flags?.includes(risk))?.section_id)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-[#F8FAFC] border border-[#EF4444] bg-[#EF4444]/15 hover:bg-[#EF4444]/25 transition-colors cursor-pointer"
              >
                <div className="w-2 h-2 bg-[#EF4444] rounded-full"></div>
                {risk.title}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ZONE D — Stats Row */}
      <div className="border-t border-[#334155] pt-4 mb-4 space-y-2">
        {/* Row 1: Sections count */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#0F1A2E] border border-[#334155]">
            <span className="text-[#F8FAFC] text-sm font-bold">{totalSections}</span>
            <span className="text-[#94A3B8] text-xs">Sections</span>
          </div>
        </div>
        {/* Row 2: Risk badges — always stay on one line, shrink text if needed */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#EF4444]/10 border border-[#EF4444]/30 whitespace-nowrap">
            <span className="w-2 h-2 rounded-full bg-[#EF4444] shrink-0" />
            <span className="text-[#EF4444] text-xs font-bold">{highCount}</span>
            <span className="text-[#EF4444]/80 text-xs">High Risk</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#F59E0B]/10 border border-[#F59E0B]/30 whitespace-nowrap">
            <span className="w-2 h-2 rounded-full bg-[#F59E0B] shrink-0" />
            <span className="text-[#F59E0B] text-xs font-bold">{mediumCount}</span>
            <span className="text-[#F59E0B]/80 text-xs">Medium Risk</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#3B82F6]/10 border border-[#3B82F6]/30 whitespace-nowrap">
            <span className="w-2 h-2 rounded-full bg-[#3B82F6] shrink-0" />
            <span className="text-[#3B82F6] text-xs font-bold">{noteCount}</span>
            <span className="text-[#3B82F6]/80 text-xs">Notes</span>
          </div>
        </div>
      </div>

      {/* ZONE E — Parties */}
      {parties.length > 0 && (
        <div className="border-t border-[#334155] pt-4 mb-4">
          <p className="text-[#94A3B8] text-xs font-semibold uppercase tracking-wider mb-3">Parties Identified</p>
          <div className="flex flex-wrap gap-2">
            {parties.map((p, i) => (
              <div key={i} className="bg-[#0F1A2E] border border-[#334155] rounded-lg px-3 py-2 min-w-[120px]">
                <p className="text-[#F8FAFC] text-xs font-semibold">{p.name || '—'}</p>
                <p className="text-[#94A3B8] text-xs capitalize">{p.role || '—'}</p>
                {p.description && p.description !== p.role && (
                  <p className="text-[#64748B] text-xs mt-0.5 leading-snug">{p.description}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Processing footer */}
      {streaming && (
        <div className="mt-2 pt-3 border-t border-[#334155] flex items-center gap-2 text-[#10B981] text-xs">
          <div className="w-2 h-2 bg-[#10B981] rounded-full animate-pulse"></div>
          Processing this section...
        </div>
      )}

      {/* Timestamp */}
      <p className="text-[#64748B] text-xs">Translated on {formatDateTime()}</p>
    </div>
  )
}
