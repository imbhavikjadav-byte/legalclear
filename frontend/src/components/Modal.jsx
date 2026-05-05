import { useEffect } from 'react'

const CONFIG = {
  error: {
    iconBg: 'rgba(239,68,68,0.15)',
    iconBorder: 'rgba(239,68,68,0.3)',
    iconColor: '#EF4444',
    btnBg: '#EF4444',
    btnText: '#ffffff',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <line x1="18" y1="6" x2="6" y2="18" />
        <line x1="6" y1="6" x2="18" y2="18" />
      </svg>
    ),
  },
  success: {
    iconBg: 'rgba(16,185,129,0.12)',
    iconBorder: 'rgba(16,185,129,0.3)',
    iconColor: '#10B981',
    btnBg: '#10B981',
    btnText: '#ffffff',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="20 6 9 17 4 12" />
      </svg>
    ),
  },
  warning: {
    iconBg: 'rgba(245,158,11,0.12)',
    iconBorder: 'rgba(245,158,11,0.3)',
    iconColor: '#F59E0B',
    btnBg: '#F59E0B',
    btnText: '#000000',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
    ),
  },
}

export default function Modal({ isOpen, type = 'error', title, message, onClose }) {
  const cfg = CONFIG[type] || CONFIG.error

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return
    function onKey(e) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(0,0,0,0.6)',
        padding: '1rem',
        animation: 'modal-backdrop-in 0.2s ease',
      }}
      onClick={onClose}
    >
      <style>{`
        @keyframes modal-backdrop-in {
          from { opacity: 0; }
          to   { opacity: 1; }
        }
        @keyframes modal-card-in {
          from { opacity: 0; transform: scale(0.95); }
          to   { opacity: 1; transform: scale(1); }
        }
      `}</style>

      <div
        style={{
          background: '#1A2F4E',
          border: '1px solid #334155',
          borderRadius: '16px',
          padding: '2rem',
          maxWidth: '420px',
          width: '100%',
          textAlign: 'center',
          animation: 'modal-card-in 0.2s ease',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Icon */}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <div
            style={{
              width: '56px',
              height: '56px',
              borderRadius: '50%',
              background: cfg.iconBg,
              border: `1px solid ${cfg.iconBorder}`,
              color: cfg.iconColor,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {cfg.icon}
          </div>
        </div>

        {/* Title */}
        <p
          style={{
            color: '#F8FAFC',
            fontSize: '18px',
            fontWeight: '700',
            marginTop: '1rem',
            lineHeight: '1.3',
          }}
        >
          {title}
        </p>

        {/* Message */}
        <p
          style={{
            color: '#94A3B8',
            fontSize: '14px',
            lineHeight: '1.7',
            marginTop: '0.5rem',
          }}
        >
          {message}
        </p>

        {/* OK Button */}
        <button
          onClick={onClose}
          style={{
            display: 'block',
            width: '100%',
            marginTop: '1.5rem',
            padding: '12px',
            background: cfg.btnBg,
            color: cfg.btnText,
            border: 'none',
            borderRadius: '12px',
            fontSize: '15px',
            fontWeight: '600',
            cursor: 'pointer',
          }}
        >
          OK
        </button>
      </div>
    </div>
  )
}
