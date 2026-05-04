import { formatDateTime } from '../utils/formatters'

const RISK_COLOUR = {
  LOW: 'bg-[#10B981] text-white',
  MEDIUM: 'bg-[#F59E0B] text-white',
  HIGH: 'bg-[#EF4444] text-white',
}

export default function SummaryCard({ data }) {
  // Handle incomplete data during streaming
  const riskColour = data.overall_risk_level ? (RISK_COLOUR[data.overall_risk_level] || 'bg-[#64748B] text-white') : 'bg-[#64748B] text-white'

  return (
    <div className="bg-[#1A2F4E] border border-[#334155] rounded-2xl p-6 mb-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
        <div>
          <h2 className="text-[#F8FAFC] font-bold text-2xl mb-1">{data.document_name || 'Document Analysis'}</h2>
          <p className="text-[#94A3B8] text-sm">{formatDateTime()}</p>
        </div>
        {data.overall_risk_level && (
          <span className={`px-4 py-1.5 rounded-full font-bold text-sm ${riskColour}`}>
            {data.overall_risk_level} RISK
          </span>
        )}
      </div>

      {/* Risk explanation */}
      {data.overall_risk_explanation && (
        <p className="text-[#94A3B8] text-sm mb-5 leading-relaxed">{data.overall_risk_explanation}</p>
      )}

      {/* Stats chips */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
        <StatChip label="Sections" value={data.total_clauses_reviewed || data.sections?.length || 0} colour="text-[#3B82F6]" />
        <StatChip label="🔴 High Risk" value={data.high_risk_count || 0} colour="text-[#EF4444]" />
        <StatChip label="🟡 Medium Risk" value={data.medium_risk_count || 0} colour="text-[#F59E0B]" />
        <StatChip label="🔵 Notes" value={data.note_count || 0} colour="text-[#3B82F6]" />
      </div>

      {/* Summary */}
      {data.summary && (
        <div className="bg-[#0F1A2E] rounded-xl p-4 mb-5">
          <p className="text-[#94A3B8] text-xs font-semibold uppercase tracking-wider mb-2">Overview</p>
          <p className="text-[#F8FAFC] text-sm leading-relaxed">{data.summary}</p>
        </div>
      )}

      {/* Parties */}
      {data.parties?.length > 0 && (
        <div>
          <p className="text-[#94A3B8] text-xs font-semibold uppercase tracking-wider mb-2">
            Parties Identified
          </p>
          <div className="flex flex-wrap gap-2">
            {data.parties.map((p, i) => (
              <div key={i} className="bg-[#0F1A2E] border border-[#334155] rounded-lg px-3 py-2 max-w-[200px]" title={p.description || ''}>
                <p className="text-[#F8FAFC] text-xs font-semibold truncate">{p.name || '—'}</p>
                <p className="text-[#94A3B8] text-xs truncate">{p.role || '—'}</p>
                {p.description && (
                  <p className="text-[#64748B] text-xs mt-0.5 line-clamp-2 leading-snug">{p.description}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function StatChip({ label, value, colour }) {
  return (
    <div className="bg-[#0F1A2E] border border-[#334155] rounded-xl p-3 text-center">
      <p className={`font-bold text-2xl ${colour}`}>{value}</p>
      <p className="text-[#94A3B8] text-xs mt-0.5">{label}</p>
    </div>
  )
}
