import { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react';
import { Icon } from './Icon';

const ToastContext = createContext(null);

const ICONS = { success: 'check', error: 'alert', warning: 'info', info: 'info' };

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const nextId = useRef(1);

  const dismiss = useCallback((id) => {
    setToasts((list) => list.filter((t) => t.id !== id));
  }, []);

  const push = useCallback(
    (toast) => {
      const id = nextId.current++;
      setToasts((list) => [...list.slice(-3), { tone: 'info', ...toast, id }]);
      window.setTimeout(() => dismiss(id), toast.duration ?? 4200);
    },
    [dismiss],
  );

  const value = useMemo(() => ({ push, dismiss }), [push, dismiss]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toasts" role="region" aria-label="Notifications" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={`toast toast--${t.tone}`} role="status">
            <span className="toast__icon">
              <Icon name={ICONS[t.tone]} size={16} strokeWidth={2} />
            </span>
            <div className="toast__body">
              <p className="toast__title">{t.title}</p>
              {t.message && <p className="toast__message">{t.message}</p>}
            </div>
            <button className="icon-btn icon-btn--sm" onClick={() => dismiss(t.id)} aria-label="Dismiss">
              <Icon name="x" size={14} />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used inside <ToastProvider>');
  return ctx;
}
