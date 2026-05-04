import RiskFlag from './RiskFlag'

export default function RiskSummary({ sections }) {
  const allFlags = []
  for (const sec of sections) {
    for (const raw of sec.risk_flags || []) {
      // Skip anything that isn't a plain object (e.g. strings from a bad API response)
      if (!raw || typeof raw !== 'object' || Array.isArray(raw)) continue
      // Normalise alternate key names Claude might use
      const flag = {
        severity: (raw.severity || raw.level || raw.type || 'NOTE').toUpperCase(),
        title: raw.title || raw.name || raw.label || '',
        explanation: raw.explanation || raw.description || raw.text || '',
        sectionTitle: sec.title,
      }
      allFlags.push(flag)
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
      {high.length > 0 && medium.length > 0 && (
        <hr className="border-[#334155] my-5" />
      )}
      {medium.length > 0 && (
        <Section title="🟡 Medium Risk" flags={medium} />
      )}
      {(high.length > 0 || medium.length > 0) && notes.length > 0 && (
        <hr className="border-[#334155] my-5" />
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
