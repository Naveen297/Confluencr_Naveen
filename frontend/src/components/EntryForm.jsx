import { useEffect, useRef, useState } from 'react';
import { api } from '../api/client';
import { formatDateTime, formatMoney, generateReference, parseAmount } from '../lib/format';
import { Icon } from './Icon';

const emptyForm = () => ({
  type: 'credit',
  amount: '',
  description: '',
  reference_id: generateReference(),
});

export function EntryForm({ account, onPosted, onShowEntry }) {
  const [form, setForm] = useState(emptyForm);
  const [errors, setErrors] = useState({});
  const [notice, setNotice] = useState(null);
  const [saving, setSaving] = useState(false);
  const amountRef = useRef(null);

  useEffect(() => {
    setForm(emptyForm());
    setErrors({});
    setNotice(null);
  }, [account.id]);

  const set = (key) => (e) => {
    const value = e.target.value;
    setForm((f) => ({ ...f, [key]: value }));
    if (errors[key]) setErrors((x) => ({ ...x, [key]: undefined }));
    if (notice) setNotice(null);
  };

  const setType = (type) => {
    setForm((f) => ({ ...f, type }));
    if (notice) setNotice(null);
  };

  const parsed = parseAmount(form.amount);
  const overdraws = form.type === 'debit' && parsed.amount > account.balance;

  const validate = () => {
    const next = {};
    if (parsed.error) next.amount = parsed.error;
    if (!form.description.trim()) next.description = 'Add a short description.';
    const ref = form.reference_id.trim();
    if (!ref) next.reference_id = 'A reference is required.';
    else if (!/^[A-Za-z0-9][A-Za-z0-9._:-]*$/.test(ref))
      next.reference_id = 'Use letters, digits and . _ : - only.';
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const submit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setSaving(true);
    setNotice(null);
    try {
      const tx = await api.createTransaction(account.id, {
        type: form.type,
        amount: form.amount.trim(),
        description: form.description.trim(),
        reference_id: form.reference_id.trim(),
      });
      setForm((f) => ({ ...emptyForm(), type: f.type }));
      onPosted(tx);
      amountRef.current?.focus();
    } catch (err) {
      if (err.code === 'DUPLICATE_TRANSACTION') {
        setNotice({ kind: 'duplicate', existing: err.details?.transaction });
      } else if (err.code === 'INSUFFICIENT_FUNDS') {
        setNotice({ kind: 'funds', ...err.details });
      } else if (err.code === 'VALIDATION_ERROR' && Array.isArray(err.details)) {
        const fieldErrors = {};
        err.details.forEach((d) => (fieldErrors[d.field] = d.message));
        setErrors(fieldErrors);
      } else {
        setNotice({ kind: 'error', message: err.message });
      }
    } finally {
      setSaving(false);
    }
  };

  const isCredit = form.type === 'credit';

  return (
    <form className={`entry entry--${form.type}`} onSubmit={submit} noValidate aria-labelledby="entry-title">
      <div className="entry__head">
        <h2 id="entry-title" className="section-title">
          Record an entry
        </h2>
        <div className="segmented" role="radiogroup" aria-label="Entry type">
          {['credit', 'debit'].map((t) => (
            <button
              key={t}
              type="button"
              role="radio"
              aria-checked={form.type === t}
              className={`segmented__option segmented__option--${t} ${form.type === t ? 'is-active' : ''}`}
              onClick={() => setType(t)}
            >
              <Icon name={t === 'credit' ? 'arrowIn' : 'arrowOut'} size={15} strokeWidth={2} />
              {t === 'credit' ? 'Credit' : 'Debit'}
            </button>
          ))}
        </div>
      </div>

      <div className="entry__grid">
        <div className={`field field--amount ${errors.amount ? 'has-error' : ''}`}>
          <label className="field__label" htmlFor="entry-amount">
            Amount
          </label>
          <div className="input-affix">
            <span className="input-affix__sign" aria-hidden="true">
              {isCredit ? '+' : '−'}
            </span>
            <input
              ref={amountRef}
              id="entry-amount"
              className="input num"
              inputMode="decimal"
              placeholder="0.00"
              value={form.amount}
              onChange={set('amount')}
              autoComplete="off"
              aria-invalid={Boolean(errors.amount)}
              aria-describedby="entry-amount-help"
            />
          </div>
          <p id="entry-amount-help" className={errors.amount ? 'field__error' : overdraws ? 'field__warn' : 'field__hint'}>
            {errors.amount ||
              (overdraws
                ? `More than the available ${formatMoney(account.balance)}. The server will reject it.`
                : `Available ${formatMoney(account.balance)}`)}
          </p>
        </div>

        <div className={`field field--description ${errors.description ? 'has-error' : ''}`}>
          <label className="field__label" htmlFor="entry-description">
            Description
          </label>
          <input
            id="entry-description"
            className="input"
            placeholder={isCredit ? 'e.g. Salary for October' : 'e.g. Rent for November'}
            value={form.description}
            onChange={set('description')}
            maxLength={255}
            autoComplete="off"
            aria-invalid={Boolean(errors.description)}
          />
          {errors.description && <p className="field__error">{errors.description}</p>}
        </div>

        <div className={`field field--reference ${errors.reference_id ? 'has-error' : ''}`}>
          <label className="field__label" htmlFor="entry-reference">
            Reference ID
          </label>
          <div className="input-affix input-affix--end">
            <input
              id="entry-reference"
              className="input input--code"
              value={form.reference_id}
              onChange={set('reference_id')}
              maxLength={64}
              autoComplete="off"
              spellCheck={false}
              aria-invalid={Boolean(errors.reference_id)}
            />
            <button
              type="button"
              className="icon-btn icon-btn--sm input-affix__action"
              onClick={() => setForm((f) => ({ ...f, reference_id: generateReference() }))}
              aria-label="Generate a new reference"
              title="Generate a new reference"
            >
              <Icon name="refresh" size={14} strokeWidth={2} />
            </button>
          </div>
          {errors.reference_id && <p className="field__error">{errors.reference_id}</p>}
        </div>

        <div className="entry__submit">
          <button type="submit" className={`btn btn--${form.type} btn--block`} disabled={saving}>
            {saving ? 'Posting…' : isCredit ? 'Post credit' : 'Post debit'}
          </button>
        </div>
      </div>

      {notice && <Notice notice={notice} onShowEntry={onShowEntry} onDismiss={() => setNotice(null)} />}
    </form>
  );
}

function Notice({ notice, onShowEntry, onDismiss }) {
  let tone = 'error';
  let title;
  let body;

  if (notice.kind === 'duplicate') {
    const tx = notice.existing;
    tone = 'warning';
    title = 'Already recorded';
    body = tx ? (
      <>
        Reference <code>{tx.reference_id}</code> was posted on {formatDateTime(tx.created_at)} as a{' '}
        {tx.type} of {formatMoney(tx.amount)}. Nothing new was recorded and the balance is unchanged.
      </>
    ) : (
      'This reference already exists on the account. Nothing new was recorded.'
    );
  } else if (notice.kind === 'funds') {
    title = 'Not enough balance';
    body = (
      <>
        This debit needs {formatMoney(notice.requested)} but the balance is only {formatMoney(notice.balance)}.
        Nothing was recorded and the balance is unchanged.
      </>
    );
  } else {
    title = 'Entry not posted';
    body = notice.message;
  }

  return (
    <div className={`notice notice--${tone}`} role="alert">
      <Icon name={tone === 'warning' ? 'info' : 'alert'} size={18} className="notice__icon" />
      <div className="notice__text">
        <p className="notice__title">{title}</p>
        <p>{body}</p>
      </div>
      <div className="notice__actions">
        {notice.kind === 'duplicate' && notice.existing && (
          <button type="button" className="btn btn--ghost btn--sm" onClick={() => onShowEntry(notice.existing)}>
            View entry
          </button>
        )}
        <button type="button" className="icon-btn icon-btn--sm" onClick={onDismiss} aria-label="Dismiss">
          <Icon name="x" size={14} />
        </button>
      </div>
    </div>
  );
}
