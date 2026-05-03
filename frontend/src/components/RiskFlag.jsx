const SEVERITY_CONFIG = {
  HIGH: {
    bg: 'bg-[#FEF2F2]',
    border: 'border-l-4 border-[#EF4444]',
    label: '🔴 HIGH RISK',
    labelColour: 'text-[#DC2626]',
  },
  MEDIUM: {
    bg: 'bg-[#FFFBEB]',
    border: 'border-l-4 border-[#F59E0B]',
    label: '🟡 MEDIUM RISK',
    labelColour: 'text-[#D97706]',
  },
  NOTE: {
    bg: 'bg-[#EFF6FF]',
    border: 'border-l-4 border-[#3B82F6]',
    label: '🔵 NOTE',
    labelColour: 'text-[#2563EB]',
  },
}

export default function RiskFlag({ flag }) {
  const config = SEVERITY_CONFIG[flag.severity] || SEVERITY_CONFIG.NOTE
  return (
    <div className={`rounded-r-lg p-3 mt-2 ${config.bg} ${config.border}`}>
      <p className={`font-bold text-xs mb-0.5 ${config.labelColour}`}>
        {config.label}: {flag.title}
      </p>
      <p className="text-[#374151] text-xs leading-relaxed">{flag.explanation}</p>
    </div>
  )
}
