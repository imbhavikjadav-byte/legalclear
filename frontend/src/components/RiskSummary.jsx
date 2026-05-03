import RiskFlag from './RiskFlag'

export default function RiskSummary({ sections }) {
  const allFlags = []
  for (const sec of sections) {
    for (const flag of sec.risk_flags || []) {
      allFlags.push({ ...flag, sectionTitle: sec.title })
    }
  }

  const high = allFlags.filter((f) => f.severity === 'HIGH')
  const medium = allFlags.filter((f) => f.severity === 'MEDIUM')
  const notes = allFlags.filter((f) => f.severity === 'NOTE')

  if (allFlags.length === 0) {
    return (
      <div className="bg-[#1A2F4E] border border-[#334155] rounded-2xl p-6">
        <h3 className="text-[#F8FAFC] font-bold text-lg mb-2">Risk Summary</h3>
        <p className="text-[#94A3B8] text-sm">No risk flags were identified in this document.</p>
      </div>
    )
  }

  return (
    <div className="bg-[#1A2F4E] border border-[#334155] rounded-2xl p-6 mb-6">
      <h3 className="text-[#F8FAFC] font-bold text-lg mb-4">Risk Summary</h3>

      {high.length > 0 && (
        <Section title="🔴 High Risk" flags={high} />
      )}
      {medium.length > 0 && (
        <Section title="🟡 Medium Risk" flags={medium} />
      )}
      {notes.length > 0 && (
        <Section title="🔵 Notes" flags={notes} />
      )}
    </div>
  )
}

function Section({ title, flags }) {
  return (
    <div className="mb-4">
      <h4 className="text-[#94A3B8] text-xs font-semibold uppercase tracking-wider mb-2">{title}</h4>
      {flags.map((flag, i) => (
        <div key={i}>
          <p className="text-[#64748B] text-xs mb-0.5">From: {flag.sectionTitle}</p>
          <RiskFlag flag={flag} />
          {i < flags.length - 1 && <div className="h-2" />}
        </div>
      ))}
    </div>
  )
}
