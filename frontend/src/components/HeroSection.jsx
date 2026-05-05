import { Scale, Shield, FileText } from 'lucide-react'

export default function HeroSection() {
  return (
    <div className="text-center py-16 px-4">
      <div className="flex items-center justify-center gap-2 mb-6">
        <span className="inline-flex items-center gap-2 bg-[#1A2F4E] text-[#F59E0B] text-sm font-medium px-4 py-1.5 rounded-full border border-[#334155]">
          <Shield className="w-4 h-4" />
          Powered by Claude AI
        </span>
      </div>
      <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-[#F8FAFC] mb-4 leading-tight">
        Understand What{' '}
        <span className="text-[#F59E0B]">You're Signing. Bhavik</span>
      </h1>
      <p className="text-lg sm:text-xl text-[#94A3B8] max-w-2xl mx-auto mb-8 leading-relaxed">
        Paste any legal document and get a plain-English breakdown with risk
        flags — in seconds.
      </p>
      <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-[#94A3B8]">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-[#F59E0B]" />
          Terms of Service
        </div>
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-[#F59E0B]" />
          Privacy Policies
        </div>
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-[#F59E0B]" />
          Employment Contracts
        </div>
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-[#F59E0B]" />
          NDAs &amp; Leases
        </div>
      </div>
    </div>
  )
}
