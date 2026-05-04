import { Scale } from 'lucide-react'

export default function Navbar({ centered = false }) {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0F1A2E] border-b border-[#334155]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center h-16 justify-center sm:justify-start">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-[#F59E0B] rounded-lg">
              <Scale className="w-6 h-6 text-[#0F1A2E]" strokeWidth={2.5} />
            </div>
            <span className="text-[#F8FAFC] font-bold text-2xl tracking-tight">
              Legal<span className="text-[#F59E0B]">Clear</span>
            </span>
          </div>
        </div>
      </div>
    </nav>
  )
}
