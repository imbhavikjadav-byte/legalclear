import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30s for all non-translate calls
})

/**
 * _readSSEStream
 *
 * Reads a Server-Sent Events stream from a fetch() Response.
 * Returns the payload of the first 'result' event.
 * Ignores 'ping' and 'status' events — they only exist to keep proxies alive.
 * Throws on 'error' events or if the stream closes without a result.
 *
 * WHY fetch() instead of axios:
 *   axios does not support reading SSE streams. fetch() with response.body
 *   gives direct access to the ReadableStream so we can process each chunk
 *   as it arrives instead of waiting for the full response.
 */
async function _readSSEStream(response) {
  if (!response.ok) {
    let msg = `HTTP ${response.status}`
    try { const j = await response.json(); msg = j?.detail?.message || msg } catch (_) {}
    throw new Error(msg)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    // SSE events may use LF or CRLF delimiters.
    const parts = buffer.split(/\r?\n\r?\n/)
    buffer = parts.pop() // keep any incomplete trailing chunk

    for (const part of parts) {
      const line = part.trim()
      if (!line.startsWith('data: ')) continue
      const data = JSON.parse(line.slice(6))

      if (data.type === 'result') return data.data
      if (data.type === 'error') throw new Error(data.message || 'Translation failed')
      // 'ping' and 'status' are intentionally ignored — they're just keepalives
    }
  }

  throw new Error('Stream ended without a result. Please try again.')
}

export async function translateDocument(documentText, documentName) {
  const response = await fetch(`${API_BASE_URL}/api/translate-stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ document_text: documentText, document_name: documentName }),
  })
  return _readSSEStream(response)
}

export async function translateFile(file, documentName) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('document_name', documentName)
  const response = await fetch(`${API_BASE_URL}/api/translate-file-stream`, {
    method: 'POST',
    body: formData,
    // No Content-Type header — browser sets it automatically with the correct boundary
  })
  return _readSSEStream(response)
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
