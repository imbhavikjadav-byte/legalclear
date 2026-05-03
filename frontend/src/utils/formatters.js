export function formatDate(date = new Date()) {
  return date.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

export function formatDateTime(date = new Date()) {
  const d = formatDate(date)
  const t = date.toLocaleTimeString('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
  })
  return `${d} at ${t}`
}

export function formatNumber(n) {
  return new Intl.NumberFormat().format(n)
}

export function truncateText(text, maxLength = 300) {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength - 3) + '...'
}

export function getErrorMessage(error) {
  if (error?.response?.data?.detail?.message) {
    return error.response.data.detail.message
  }
  if (error?.response?.data?.message) {
    return error.response.data.message
  }
  if (error?.message) {
    return error.message
  }
  return 'An unexpected error occurred. Please try again.'
}
