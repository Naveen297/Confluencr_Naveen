import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { Dialog } from './Dialog';

export function NewAccountDialog({ open, onClose, onCreated }) {
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) {
      setName('');
      setError('');
    }
  }, [open]);

  const submit = async (e) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) {
      setError('Enter the account holder’s name.');
      return;
    }
    setSaving(true);
    try {
      const account = await api.createAccount(trimmed);
      onCreated(account);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Open an account"
      description="Every account starts at a balance of 0.00. Credits and debits move it from there."
    >
      <form onSubmit={submit} noValidate>
        <div className="dialog__body">
          <div className={`field ${error ? 'has-error' : ''}`}>
            <label htmlFor="account-name" className="field__label">
              Account holder name
            </label>
            <input
              id="account-name"
              className="input"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                if (error) setError('');
              }}
              maxLength={100}
              placeholder="e.g. Asha Raman"
              autoComplete="off"
              autoFocus
              aria-invalid={Boolean(error)}
              aria-describedby={error ? 'account-name-error' : undefined}
            />
            {error && (
              <p id="account-name-error" className="field__error">
                {error}
              </p>
            )}
          </div>
        </div>
        <footer className="dialog__footer">
          <button type="button" className="btn btn--ghost" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn btn--primary" disabled={saving}>
            {saving ? 'Opening…' : 'Open account'}
          </button>
        </footer>
      </form>
    </Dialog>
  );
}
