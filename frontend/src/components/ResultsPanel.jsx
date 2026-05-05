import { useState, useEffect, useRef } from 'react'
import toast from 'react-hot-toast'
import SummaryCard from './SummaryCard'
import SectionAccordion from './SectionAccordion'
import RiskSummary from './RiskSummary'
import ActionBar from './ActionBar'
import EmailModal from './EmailModal'
import StreamingProgress from './StreamingProgress'
import StreamingSection from './StreamingSection'
import { generatePdf, sendEmail } from '../services/api'
import { getErrorMessage } from '../utils/formatters'
import { Copy, CheckCheck } from 'lucide-react'

export default function ResultsPanel({
  data, // legacy prop for non-streaming
  streamingMeta,
  streamingSections,
  streamingFinal,
  streamingComplete,
  documentName,
  originalFilename,
  forcedOpenSectionIds,
  setForcedOpenSectionIds,
  onReset,
  onStop,
  onDownloadPdf,
  onSendEmail
}) {
  // Support both legacy and streaming modes
  const isStreaming = streamingMeta !== undefined
  const currentData = isStreaming ? {
    document_name: streamingMeta?.document_name,
    verdict: streamingMeta?.verdict,
    parties: Array.isArray(streamingMeta?.parties) ? streamingMeta.parties : [],
    summary: streamingMeta?.summary,
    sections: streamingSections,
    overall_risk_level: streamingFinal?.overall_risk_level,
    overall_risk_explanation: streamingFinal?.overall_risk_explanation,
    total_clauses_reviewed: streamingFinal?.total_clauses_reviewed,
    high_risk_count: streamingFinal?.high_risk_count,
    medium_risk_count: streamingFinal?.medium_risk_count,
    note_count: streamingFinal?.note_count
  } : data

  const pdfName = documentName || currentData?.document_name
  const [showEmailModal, setShowEmailModal] = useState(false)

  // Scroll to top when streaming finishes so user sees the summary
  const didScrollRef = useRef(false)
  useEffect(() => {
    if (streamingComplete && !didScrollRef.current) {
      didScrollRef.current = true
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }, [streamingComplete])
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [copied, setCopied] = useState(false)

  async function handleDownloadPdf() {
    if (onDownloadPdf) {
      onDownloadPdf()
      return
    }

    setIsGeneratingPdf(true)
    try {
      const response = await generatePdf(currentData, pdfName, originalFilename)
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
    if (onSendEmail) {
      onSendEmail(email)
      setShowEmailModal(false)
      return
    }

    setIsSending(true)
    try {
      await sendEmail(email, currentData, pdfName, originalFilename)
      toast.success(`Report sent to ${email}!`)
      setShowEmailModal(false)
    } catch (err) {
      toast.error(getErrorMessage(err), { duration: 10000 })
    } finally {
      setIsSending(false)
    }
  }

  function handleCopyTranslation() {
    const text = currentData.sections
      .map((s) => `## ${s.section_id}. ${s.title}\n${s.plain_english}`)
      .join('\n\n')
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      toast.success('Translation copied to clipboard!')
      setTimeout(() => setCopied(false), 2000)
    })
  }

  const [actionBarHeight, setActionBarHeight] = useState(0)

  return (
    <div className="animate-fade-in">
      <ActionBar
        onDownload={handleDownloadPdf}
        onEmail={() => setShowEmailModal(true)}
        onReset={onReset}
        isGeneratingPdf={isGeneratingPdf}
        disabled={!streamingComplete && isStreaming}
        onHeightChange={setActionBarHeight}
      />
      {/* Mobile-only spacer: compensates for fixed ActionBar being out of flow, +24px gap below bar */}
      <div className="sm:hidden" style={{ height: actionBarHeight + 24 }} />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {isStreaming && (
          <StreamingProgress
            isStreaming={!streamingComplete}
            streamingComplete={streamingComplete}
            sectionsCount={streamingSections.length}
            onStop={onStop}
          />
        )}

        {currentData && <SummaryCard data={currentData} meta={streamingMeta} sections={streamingSections} final={streamingFinal} isStreaming={isStreaming} streamingComplete={streamingComplete} forcedOpenSectionIds={forcedOpenSectionIds} setForcedOpenSectionIds={setForcedOpenSectionIds} />}
        {currentData && <RiskSummary sections={currentData.sections} isStreaming={isStreaming} streamingComplete={streamingComplete} />}

        {/* Sections Header */}
        {currentData?.sections && currentData.sections.length > 0 && (
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-[#F8FAFC] font-bold text-lg">Full Translation</h3>
            <button
              onClick={handleCopyTranslation}
              className="flex items-center gap-2 text-[#94A3B8] hover:text-[#F8FAFC] text-sm transition-colors"
              disabled={!streamingComplete && isStreaming}
            >
              {copied ? <CheckCheck className="w-4 h-4 text-[#10B981]" /> : <Copy className="w-4 h-4" />}
              {copied ? 'Copied!' : 'Copy Translation'}
            </button>
          </div>
        )}

        {isStreaming ? (
          // Streaming sections with animations
          streamingSections.map((section, i) => (
            <StreamingSection
              key={section.section_id || i}
              section={section}
              index={i}
              isLast={i === streamingSections.length - 1 && !streamingComplete}
              forcedOpenSectionIds={forcedOpenSectionIds}
            />
          ))
        ) : (
          // Legacy non-streaming sections
          currentData?.sections?.map((section, i) => (
            <SectionAccordion key={section.section_id} section={section} defaultOpen={i === 0} />
          ))
        )}
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
