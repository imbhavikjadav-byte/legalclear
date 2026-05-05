import { useState, useCallback } from 'react'

const DEFAULT_TITLES = {
  error: 'Something went wrong',
  success: 'Success',
  warning: 'Heads up',
}

export function useModal() {
  const [modalState, setModalState] = useState({
    isOpen: false,
    type: 'error',
    title: '',
    message: '',
  })

  const showModal = useCallback(({ type = 'error', title, message }) => {
    setModalState({
      isOpen: true,
      type,
      title: title || DEFAULT_TITLES[type] || DEFAULT_TITLES.error,
      message,
    })
  }, [])

  const hideModal = useCallback(() => {
    setModalState((prev) => ({ ...prev, isOpen: false }))
  }, [])

  return { showModal, hideModal, modalState }
}
