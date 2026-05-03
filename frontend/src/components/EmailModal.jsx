import { useState } from 'react'
import { X, Mail, Send } from 'lucide-react'

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

export default function EmailModal({ onSend, onClose, isSending }) {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    if (!email.trim()) {
      setError('Please enter an email address.')
      return
    }
    if (!isValidEmail(email.trim())) {
      setError('Please enter a valid email address.')
      return
    }
    setError('')
    onSend(email.trim())
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />
      {/* Modal */}
      <div className="relative bg-[#1A2F4E] border border-[#334155] rounded-2xl w-full max-w-md p-6 shadow-2xl animate-fade-in">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[#2563EB] rounded-lg">
              <Mail className="w-5 h-5 text-white" />
            </div>
            <h3 className="text-[#F8FAFC] font-bold text-lg">Send Translation Report</h3>
          </div>
          <button
            onClick={onClose}
            className="text-[#94A3B8] hover:text-[#F8FAFC] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-[#94A3B8] text-sm mb-5 leading-relaxed">
          We'll generate a PDF of this translation and send it to your email.
        </p>

        <form onSubmit={handleSubmit} noValidate>
          <div className="mb-4">
            <label className="block text-[#94A3B8] text-sm font-medium mb-1.5">
              Email Address <span className="text-[#EF4444]">*</span>
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => { setEmail(e.target.value); setError('') }}
              placeholder="you@example.com"
              autoFocus
              className={`w-full bg-[#0F1A2E] border rounded-lg px-4 py-2.5 text-[#F8FAFC] placeholder-[#475569] focus:outline-none focus:ring-2 focus:ring-[#2563EB] transition ${
                error ? 'border-[#EF4444]' : 'border-[#334155]'
              }`}
            />
            {error && <p className="text-[#EF4444] text-xs mt-1">{error}</p>}
          </div>

          <button
            type="submit"
            disabled={isSending}
            className="w-full flex items-center justify-center gap-2 bg-[#2563EB] hover:bg-[#1D4ED8] disabled:opacity-50 text-white font-semibold py-3 rounded-xl transition-all"
          >
            <Send className="w-4 h-4" />
            {isSending ? 'Sending…' : 'Send Report'}
          </button>

          <button
            type="button"
            onClick={onClose}
            className="w-full text-[#94A3B8] hover:text-[#F8FAFC] text-sm mt-3 transition-colors"
          >
            Cancel
          </button>
        </form>
      </div>
    </div>
  )
}
