import RiskFlag from './RiskFlag'

export default function RiskSummary({ sections, isStreaming = false, streamingComplete = false }) {
  const allFlags = []
  for (const sec of sections || []) {
    for (const raw of sec.risk_flags || []) {
      // Skip anything that isn't a plain object (e.g. strings from a bad API response)
      if (!raw || typeof raw !== 'object' || Array.isArray(raw)) continue
      // Normalise alternate key names Claude might use
      const flag = {
        severity: (raw.severity || raw.level || raw.type || 'NOTE').toUpperCase(),
        title: raw.title || raw.name || raw.label || '',
        explanation: raw.explanation || raw.description || raw.text || '',
        sectionTitle: sec.title,
        sectionId: sec.section_id,
      }
      allFlags.push(flag)
    }
  }

  const highRisks = allFlags.filter((f) => f.severity === 'HIGH').slice(0, 5) // Max 5 HIGH risks

  const streaming = isStreaming && !streamingComplete

  if (highRisks.length === 0) {
    if (streaming) {
      return (
        <div className="bg-[#1A2F4E] border border-[#F59E0B] shadow-[0_0_0_2px_rgba(245,158,11,0.2)] animate-pulse-border rounded-2xl p-6 mb-6 transition-colors">
          <h3 className="text-[#F8FAFC] font-bold text-lg mb-2">What to Watch Out For</h3>
          <p className="text-[#94A3B8] text-sm mb-4">Scanning for high-risk issues...</p>
          <div className="pt-3 border-t border-[#334155] flex items-center gap-2 text-[#10B981] text-xs">
            <div className="w-2 h-2 bg-[#10B981] rounded-full animate-pulse"></div>
            Processing this section...
          </div>
        </div>
      )
    }
    return (
      <div className="bg-[#1A2F4E] border border-[#334155] rounded-2xl p-6 mb-6">
        <h3 className="text-[#F8FAFC] font-bold text-lg mb-2">What to Watch Out For</h3>
        <p className="text-[#94A3B8] text-sm">No high-risk issues were identified in this document.</p>
      </div>
    )
  }

  return (
    <div className={`bg-[#1A2F4E] border rounded-2xl p-6 mb-6 transition-colors ${
      streaming ? 'border-[#F59E0B] shadow-[0_0_0_2px_rgba(245,158,11,0.2)] animate-pulse-border' : 'border-[#334155]'
    }`}>
      <h3 className="text-[#F8FAFC] font-bold text-lg mb-4">What to Watch Out For</h3>
      <div className="space-y-3">
        {highRisks.map((flag, i) => (
          <div key={i} className="border-l-4 border-[#EF4444] pl-4 bg-[#EF4444]/5 rounded-r-lg p-3">
            <p className="text-[#F8FAFC] text-sm font-semibold mb-1">{flag.title}</p>
            <p className="text-[#94A3B8] text-xs mb-2">From: {flag.sectionTitle}</p>
            <p className="text-[#64748B] text-sm">{flag.explanation}</p>
          </div>
        ))}
      </div>
      {streaming && (
        <div className="mt-4 pt-3 border-t border-[#334155] flex items-center gap-2 text-[#10B981] text-xs">
          <div className="w-2 h-2 bg-[#10B981] rounded-full animate-pulse"></div>
          Processing this section...
        </div>
      )}
    </div>
  )
}
