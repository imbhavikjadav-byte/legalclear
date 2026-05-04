import { useState } from 'react'
import toast from 'react-hot-toast'
import SummaryCard from './SummaryCard'
import SectionAccordion from './SectionAccordion'
import RiskSummary from './RiskSummary'
import ActionBar from './ActionBar'
import EmailModal from './EmailModal'
import { generatePdf, sendEmail } from '../services/api'
import { getErrorMessage } from '../utils/formatters'
import { Copy, CheckCheck } from 'lucide-react'

export default function ResultsPanel({ data, documentName, originalFilename, onReset }) {
  // documentName is always what the user typed — never the AI-interpreted name
  const pdfName = documentName || data.document_name
  const [showEmailModal, setShowEmailModal] = useState(false)
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [copied, setCopied] = useState(false)

  async function handleDownloadPdf() {
    setIsGeneratingPdf(true)
    try {
      const response = await generatePdf(data, pdfName, originalFilename)
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `LegalClear-${pdfName.replace(/\s+/g, '-')}.pdf`
      a.click()
      URL.revokeObjectURL(url)
      toast.success('PDF downloaded successfully!')
    } catch (err) {
      toast.error(getErrorMessage(err), { duration: 10000 })
    } finally {
      setIsGeneratingPdf(false)
    }
  }

  async function handleSendEmail(email) {
    setIsSending(true)
    try {
      await sendEmail(email, data, pdfName, originalFilename)
      toast.success(`Report sent to ${email}!`)
      setShowEmailModal(false)
    } catch (err) {
      toast.error(getErrorMessage(err), { duration: 10000 })
    } finally {
      setIsSending(false)
    }
  }

  function handleCopyTranslation() {
    const text = data.sections
      .map((s) => `## ${s.section_id}. ${s.title}\n${s.plain_english}`)
      .join('\n\n')
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      toast.success('Translation copied to clipboard!')
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <div className="animate-fade-in">
      <ActionBar
        onDownload={handleDownloadPdf}
        onEmail={() => setShowEmailModal(true)}
        onReset={onReset}
        isGeneratingPdf={isGeneratingPdf}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <SummaryCard data={data} />
        <RiskSummary sections={data.sections} />

        {/* Sections Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-[#F8FAFC] font-bold text-lg">Full Translation</h3>
          <button
            onClick={handleCopyTranslation}
            className="flex items-center gap-2 text-[#94A3B8] hover:text-[#F8FAFC] text-sm transition-colors"
          >
            {copied ? <CheckCheck className="w-4 h-4 text-[#10B981]" /> : <Copy className="w-4 h-4" />}
            {copied ? 'Copied!' : 'Copy Translation'}
          </button>
        </div>

        {data.sections.map((section, i) => (
          <SectionAccordion key={section.section_id} section={section} defaultOpen={i === 0} />
        ))}
      </div>

      {showEmailModal && (
        <EmailModal
          onSend={handleSendEmail}
          onClose={() => setShowEmailModal(false)}
          isSending={isSending}
        />
      )}
    </div>
  )
}
