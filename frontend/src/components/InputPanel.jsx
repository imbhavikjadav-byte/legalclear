import { useState } from 'react'
import { Scale, X } from 'lucide-react'
import FileUpload from './FileUpload'
import { formatNumber } from '../utils/formatters'

const MAX_CHARS = 50000
const MIN_CHARS = 100

export default function InputPanel({ onTranslate, onTranslateFile, isLoading, isTestMode = false, showModal }) {
  const [documentText, setDocumentText] = useState('')
  const [documentName, setDocumentName] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)
  const [errors, setErrors] = useState({})

  const charCount = documentText.length
  const isOverLimit = charCount > MAX_CHARS
  const hasText = documentText.length > 0
  const hasFile = !!selectedFile

  function validate() {
    const errs = {}
    if (!documentName.trim()) {
      errs.documentName = 'Please enter a name for this document.'
    } else if (documentName.length > 100) {
      errs.documentName = 'Document name must be 100 characters or fewer.'
    }

    if (!selectedFile) {
      if (!documentText.trim()) {
        errs.documentText = 'Please paste or upload a legal document to translate.'
      } else if (charCount < MIN_CHARS) {
        errs.documentText = 'Your document is too short. Please provide at least 100 characters.'
      } else if (charCount > MAX_CHARS) {
        errs.documentText = `Your document exceeds the ${formatNumber(MAX_CHARS)} character limit.`
      }
    }

    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  function handleSubmit(e) {
    e.preventDefault()
    if (!validate()) return
    // Priority rule: if a file is uploaded, use it for translation (file wins).
    // If only textarea has text, use that. If somehow both have content (edge case),
    // file takes priority and textarea content is ignored.
    if (selectedFile) {
      onTranslateFile(selectedFile, documentName.trim())
    } else {
      onTranslate(documentText.trim(), documentName.trim())
    }
  }

  function handleClear() {
    setDocumentText('')
    setDocumentName('')
    setSelectedFile(null)
    setErrors({})
  }

  return (
    <div className="bg-[#1A2F4E] border border-[#334155] rounded-2xl p-6 shadow-2xl">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h2 className="text-[#F8FAFC] font-semibold text-lg">Translate Document</h2>
          {isTestMode && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#F59E0B]/15 text-[#F59E0B] border border-[#F59E0B]/40">
              <span className="w-1.5 h-1.5 rounded-full bg-[#F59E0B] animate-pulse" />
              Test Mode
            </span>
          )}
        </div>
        {(documentText || documentName || selectedFile) && (
          <button
            onClick={handleClear}
            className="text-[#94A3B8] hover:text-[#F8FAFC] flex items-center gap-1.5 text-sm transition-colors"
          >
            <X className="w-4 h-4" /> Clear
          </button>
        )}
      </div>

      <form onSubmit={handleSubmit} noValidate>
        {/* Document Name */}
        <div className="mb-4">
          <label className="block text-[#94A3B8] text-sm font-medium mb-1.5">
            Report Title <span className="text-[#EF4444]">*</span>
            <span className="text-[#475569] font-normal text-xs ml-1">— appears on your report</span>
          </label>
          <input
            type="text"
            value={documentName}
            onChange={(e) => { setDocumentName(e.target.value); setErrors((p) => ({ ...p, documentName: '' })) }}
            placeholder="e.g. Spotify Terms of Service, My Employment Contract"
            maxLength={100}
            className={`w-full bg-[#0F1A2E] border rounded-lg px-4 py-2.5 text-[#F8FAFC] placeholder-[#475569] focus:outline-none focus:ring-2 focus:ring-[#2563EB] transition ${
              errors.documentName ? 'border-[#EF4444]' : 'border-[#334155]'
            }`}
          />
          {errors.documentName && (
            <p className="text-[#EF4444] text-xs mt-1">{errors.documentName}</p>
          )}
        </div>

        {/* Text Area */}
        <div className="mb-4">
          <label className="block text-[#94A3B8] text-sm font-medium mb-1.5">
            Legal Document Text
          </label>
          <textarea
            value={documentText}
            onChange={(e) => {
              const val = e.target.value
              setDocumentText(val)
              setErrors((p) => ({ ...p, documentText: '' }))
              if (val && selectedFile) setSelectedFile(null)
            }}
            placeholder="Paste your Terms of Service, contract, NDA, lease, or any legal document here…"
            disabled={hasFile}
            style={{
              opacity: hasFile ? 0.4 : 1,
              transition: 'opacity 0.2s ease',
              resize: hasFile ? 'none' : undefined,
              cursor: hasFile ? 'not-allowed' : undefined,
            }}
            className={`w-full min-h-[300px] bg-[#0F1A2E] border rounded-lg px-4 py-3 text-[#F8FAFC] placeholder-[#475569] focus:outline-none focus:ring-2 focus:ring-[#2563EB] resize-y transition text-sm leading-relaxed ${
              errors.documentText ? 'border-[#EF4444]' : 'border-[#334155]'
            }`}
          />
          <div className="flex justify-between mt-1">
            {errors.documentText ? (
              <p className="text-[#EF4444] text-xs">{errors.documentText}</p>
            ) : (
              <span />
            )}
            <span className={`text-xs ${isOverLimit ? 'text-[#EF4444] font-semibold' : 'text-[#475569]'}`}>
              {formatNumber(charCount)} / {formatNumber(MAX_CHARS)} characters
            </span>
          </div>
          {hasFile && (
            <p style={{ fontSize: '12px', color: '#64748B', marginTop: '6px', fontStyle: 'italic' }}>
              Remove the uploaded file to type text instead
            </p>
          )}
        </div>

        {/* Divider */}
        <div className="flex items-center gap-3 my-4">
          <div className="flex-1 h-px bg-[#334155]" />
          <span className="text-[#475569] text-xs uppercase tracking-wider">or upload a file</span>
          <div className="flex-1 h-px bg-[#334155]" />
        </div>

        {/* File Upload */}
        <div
          className="mb-6"
          style={{
            opacity: hasText ? 0.4 : 1,
            transition: 'opacity 0.2s ease',
            cursor: hasText ? 'not-allowed' : undefined,
            pointerEvents: hasText ? 'none' : undefined,
          }}
        >
          <FileUpload
            onFileSelect={(f) => { setSelectedFile(f); setErrors((p) => ({ ...p, documentText: '' })) }}
            selectedFile={selectedFile}
            onClear={() => setSelectedFile(null)}
            onError={showModal}
            disabled={hasText}
          />
          {hasText && (
            <p style={{ fontSize: '12px', color: '#64748B', marginTop: '6px', fontStyle: 'italic' }}>
              Clear the text above to upload a file instead
            </p>
          )}
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={isLoading || isOverLimit}
          className="w-full flex items-center justify-center gap-3 bg-[#2563EB] hover:bg-[#1D4ED8] disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3.5 px-6 rounded-xl transition-all duration-200 hover:scale-[1.01] active:scale-[0.99] shadow-lg"
        >
          <Scale className="w-5 h-5" />
          {isLoading ? 'Translating…' : 'Translate Document'}
        </button>
      </form>
    </div>
  )
}
