import { useState } from 'react';
import { Icon } from './Icon';

export function CopyButton({ value, label = 'Copy', className = '' }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(value);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = value;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      ta.remove();
    }
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1400);
  };

  return (
    <button
      type="button"
      className={`icon-btn icon-btn--sm ${copied ? 'is-done' : ''} ${className}`}
      onClick={copy}
      aria-label={copied ? 'Copied' : label}
      title={copied ? 'Copied' : label}
    >
      <Icon name={copied ? 'check' : 'copy'} size={14} strokeWidth={2} />
    </button>
  );
}
