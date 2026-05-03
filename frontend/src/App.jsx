import { useState } from "react"
import { Toaster } from "react-hot-toast"
import toast from "react-hot-toast"
import Navbar from "./components/Navbar"
import HeroSection from "./components/HeroSection"
import InputPanel from "./components/InputPanel"
import ResultsPanel from "./components/ResultsPanel"
import LoadingIndicator from "./components/LoadingIndicator"
import Footer from "./components/Footer"
import { translateDocument, translateFile } from "./services/api"
import { getErrorMessage } from "./utils/formatters"

export default function App() {
  const [translationData, setTranslationData] = useState(null)
  const [originalFilename, setOriginalFilename] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  async function handleTranslate(text, name) {
    setIsLoading(true)
    setTranslationData(null)
    setOriginalFilename(null) // pasted text — no original file
    try {
      const result = await translateDocument(text, name)
      setTranslationData(result)
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  async function handleTranslateFile(file, name) {
    setIsLoading(true)
    setTranslationData(null)
    setOriginalFilename(file.name) // capture the real filename
    try {
      const result = await translateFile(file, name)
      setTranslationData(result)
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  function handleReset() {
    setTranslationData(null)
    setOriginalFilename(null)
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
      <Navbar />

      <main className="flex-1 pt-16">
        {!translationData && !isLoading && (
          <>
            <HeroSection />
            <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
              <InputPanel
                onTranslate={handleTranslate}
                onTranslateFile={handleTranslateFile}
                isLoading={isLoading}
              />
            </div>
          </>
        )}

        {isLoading && (
          <div className="max-w-3xl mx-auto px-4">
            <LoadingIndicator />
          </div>
        )}

        {translationData && !isLoading && (
          <ResultsPanel
            data={translationData}
            originalFilename={originalFilename}
            onReset={handleReset}
          />
        )}
      </main>

      <Footer />
    </div>
  )
}
