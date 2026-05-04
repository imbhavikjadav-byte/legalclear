import { useState, useMemo } from "react"
import { Toaster } from "react-hot-toast"
import toast from "react-hot-toast"
import Navbar from "./components/Navbar"
import HeroSection from "./components/HeroSection"
import InputPanel from "./components/InputPanel"
import ResultsPanel from "./components/ResultsPanel"
import LoadingIndicator from "./components/LoadingIndicator"
import Footer from "./components/Footer"
import { translateDocumentStream, translateFileStream, generatePdf, sendEmail } from "./services/api"
import { getErrorMessage } from "./utils/formatters"

export default function App() {
  // Streaming state management
  const [streamingMeta, setStreamingMeta] = useState(null)
  const [streamingSections, setStreamingSections] = useState([])
  const [streamingFinal, setStreamingFinal] = useState(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingComplete, setStreamingComplete] = useState(false)
  const [streamError, setStreamError] = useState(null)
  const [originalFilename, setOriginalFilename] = useState(null)
  const [userDocumentName, setUserDocumentName] = useState(null)

  // Assemble complete result for PDF/email when streaming is done
  const assembledResult = useMemo(() => {
    if (!streamingComplete || !streamingMeta || !streamingFinal) return null
    return {
      document_name: streamingMeta.document_name,
      parties: streamingMeta.parties,
      summary: streamingMeta.summary,
      sections: streamingSections,
      overall_risk_level: streamingFinal.overall_risk_level,
      overall_risk_explanation: streamingFinal.overall_risk_explanation,
      total_clauses_reviewed: streamingFinal.total_clauses_reviewed,
      high_risk_count: streamingFinal.high_risk_count,
      medium_risk_count: streamingFinal.medium_risk_count,
      note_count: streamingFinal.note_count
    }
  }, [streamingComplete, streamingMeta, streamingSections, streamingFinal])

  async function handleTranslate(text, name) {
    // Reset all streaming state
    setStreamingMeta(null)
    setStreamingSections([])
    setStreamingFinal(null)
    setStreamingComplete(false)
    setStreamError(null)
    setOriginalFilename(null)
    setUserDocumentName(name)
    setIsStreaming(true)
    window.scrollTo({ top: 0, behavior: 'smooth' })

    await translateDocumentStream(
      text,
      name,
      // onMeta
      (meta) => setStreamingMeta(meta),
      // onSection — append each section as it arrives
      (section) => setStreamingSections(prev => [...prev, section]),
      // onFinal
      (final) => {
        setStreamingFinal(final)
        setStreamingComplete(true)
        setIsStreaming(false)
      },
      // onError
      (error) => {
        setStreamError(error)
        setIsStreaming(false)
        toast.error(getErrorMessage(new Error(error)), { duration: 10000 })
      }
    )
  }

  async function handleTranslateFile(file, name) {
    // Reset all streaming state
    setStreamingMeta(null)
    setStreamingSections([])
    setStreamingFinal(null)
    setStreamingComplete(false)
    setStreamError(null)
    setOriginalFilename(file.name)
    setUserDocumentName(name)
    setIsStreaming(true)
    window.scrollTo({ top: 0, behavior: 'smooth' })

    await translateFileStream(
      file,
      name,
      // onMeta
      (meta) => setStreamingMeta(meta),
      // onSection — append each section as it arrives
      (section) => setStreamingSections(prev => [...prev, section]),
      // onFinal
      (final) => {
        setStreamingFinal(final)
        setStreamingComplete(true)
        setIsStreaming(false)
      },
      // onError
      (error) => {
        setStreamError(error)
        setIsStreaming(false)
        toast.error(getErrorMessage(new Error(error)), { duration: 10000 })
      }
    )
  }

  async function handleDownloadPdf() {
    if (!assembledResult) return

    try {
      const response = await generatePdf(assembledResult, userDocumentName, originalFilename)
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `LegalClear-${userDocumentName.replace(/\s+/g, '-')}.pdf`
      a.click()
      URL.revokeObjectURL(url)
      toast.success('PDF downloaded successfully!')
    } catch (err) {
      toast.error(getErrorMessage(err), { duration: 10000 })
    }
  }

  async function handleSendEmail(email) {
    if (!assembledResult) return

    try {
      await sendEmail(email, assembledResult, userDocumentName, originalFilename)
      toast.success(`Report sent to ${email}!`)
    } catch (err) {
      toast.error(getErrorMessage(err), { duration: 10000 })
    }
  }

  function handleReset() {
    setStreamingMeta(null)
    setStreamingSections([])
    setStreamingFinal(null)
    setStreamingComplete(false)
    setStreamError(null)
    setOriginalFilename(null)
    setUserDocumentName(null)
  }

  return (
    <div className="min-h-screen bg-[#0F1A2E] flex flex-col">
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "#1A2F4E",
            color: "#F8FAFC",
            border: "1px solid #334155",
          },
          success: { iconTheme: { primary: "#10B981", secondary: "#1A2F4E" } },
          error: { iconTheme: { primary: "#EF4444", secondary: "#1A2F4E" } },
        }}
      />
      <Navbar centered={streamingComplete} />

      <main className="flex-1 pt-16 flex flex-col">
        {!streamingMeta && !isStreaming && (
          <div className="w-full">
            <HeroSection />
            <div className="max-w-3xl mx-auto w-full px-4 sm:px-6 lg:px-8 pb-20">
              <InputPanel
                onTranslate={handleTranslate}
                onTranslateFile={handleTranslateFile}
                isLoading={isStreaming}
              />
            </div>
          </div>
        )}



        {isStreaming && !streamingMeta && (
          <div className="flex-1 flex items-center justify-center px-4">
            <LoadingIndicator />
          </div>
        )}

        {streamingMeta && (
          <ResultsPanel
            streamingMeta={streamingMeta}
            streamingSections={streamingSections}
            streamingFinal={streamingFinal}
            streamingComplete={streamingComplete}
            documentName={userDocumentName || streamingMeta.document_name}
            originalFilename={originalFilename}
            onReset={handleReset}
            onDownloadPdf={handleDownloadPdf}
            onSendEmail={handleSendEmail}
          />
        )}
      </main>

      <Footer />
    </div>
  )
}
