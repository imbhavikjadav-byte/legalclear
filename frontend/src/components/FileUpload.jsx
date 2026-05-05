import { useRef, useState } from 'react'
import { Upload, FileText, X } from 'lucide-react'

const ACCEPTED = '.txt,.pdf,.docx'

export default function FileUpload({ onFileSelect, selectedFile, onClear, onError, disabled = false }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)

  function handleFiles(files) {
    const file = files[0]
    if (!file) return
    const allowedExtensions = ['.txt', '.pdf', '.docx']
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase()
    if (!allowedExtensions.includes(fileExtension)) {
      onError({
        type: 'error',
        title: 'Unsupported file type',
        message: 'Only .txt, .pdf, and .docx files are supported. Please upload one of these file types.',
      })
      return
    }
    if (file.size > 5 * 1024 * 1024) {
      onError({
        type: 'error',
        title: 'File too large',
        message: 'File exceeds the 5 MB size limit.',
      })
      return
    }
    onFileSelect(file)
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    handleFiles(e.dataTransfer.files)
  }

  return (
    <div>
      {selectedFile ? (
        <div className="flex items-center gap-3 p-3 bg-[#1A2F4E] border border-[#334155] rounded-lg">
          <FileText className="w-5 h-5 text-[#F59E0B] shrink-0" />
          <span className="text-[#F8FAFC] text-sm truncate flex-1">{selectedFile.name}</span>
          <button
            onClick={onClear}
            className="text-[#94A3B8] hover:text-[#F8FAFC] transition-colors p-1"
            aria-label="Remove file"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ) : (
        <div
          className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
            dragging
              ? 'border-[#F59E0B] bg-[#1A2F4E]'
              : 'border-[#334155] hover:border-[#F59E0B] hover:bg-[#1A2F4E]'
          }`}
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
        >
          <Upload className="w-8 h-8 text-[#94A3B8] mx-auto mb-2" />
          <p className="text-[#94A3B8] text-sm">
            <span className="text-[#F59E0B] font-medium">Click to upload</span> or drag &amp; drop
          </p>
          <p className="text-[#94A3B8] text-xs mt-1">Supported formats: PDF, DOCX, TXT — max 5MB</p>
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED}
            className="hidden"
            disabled={disabled}
            onChange={(e) => handleFiles(e.target.files)}
          />
        </div>
      )}
    </div>
  )
}
