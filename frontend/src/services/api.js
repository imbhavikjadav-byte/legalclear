import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30s for all non-translate calls
})

// Translate calls can take 3-5 minutes for large documents
const TRANSLATE_TIMEOUT = 600000 // 10 minutes

export async function translateDocument(documentText, documentName) {
  const response = await api.post(
    '/api/translate',
    { document_text: documentText, document_name: documentName },
    { timeout: TRANSLATE_TIMEOUT }
  )
  return response.data
}

export async function translateFile(file, documentName) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('document_name', documentName)
  const response = await api.post('/api/translate-file', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: TRANSLATE_TIMEOUT,
  })
  return response.data
}

// PDF generation and email can take time with large documents
const PDF_EMAIL_TIMEOUT = 120000 // 2 minutes

export async function generatePdf(translationData, documentName, originalFilename = null) {
  const response = await api.post(
    '/api/generate-pdf',
    {
      translation_data: translationData,
      document_name: documentName,
      ...(originalFilename ? { original_filename: originalFilename } : {}),
    },
    { responseType: 'blob', timeout: PDF_EMAIL_TIMEOUT }
  )
  return response
}

export async function sendEmail(email, translationData, documentName, originalFilename = null) {
  const response = await api.post(
    '/api/send-email',
    {
      email,
      translation_data: translationData,
      document_name: documentName,
      ...(originalFilename ? { original_filename: originalFilename } : {}),
    },
    { timeout: PDF_EMAIL_TIMEOUT }
  )
  return response.data
}

export default api
