import { useEffect, useRef } from 'react';
import { Icon } from './Icon';

export function Dialog({ open, onClose, title, description, children, size = 'md' }) {
  const ref = useRef(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (open && !el.open) el.showModal();
    if (!open && el.open) el.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      className={`dialog dialog--${size}`}
      onClose={onClose}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
      onMouseDown={(e) => {
        if (e.target === ref.current) onClose();
      }}
      aria-labelledby="dialog-title"
    >
      {open && (
        <div className="dialog__panel">
          <header className="dialog__header">
            <div>
              <h2 id="dialog-title" className="dialog__title">
                {title}
              </h2>
              {description && <p className="dialog__description">{description}</p>}
            </div>
            <button className="icon-btn" onClick={onClose} aria-label="Close">
              <Icon name="x" size={16} />
            </button>
          </header>
          {children}
        </div>
      )}
    </dialog>
  );
}
