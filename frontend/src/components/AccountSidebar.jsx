import { useMemo, useState } from 'react';
import { formatMoney, shortId } from '../lib/format';
import { Icon } from './Icon';

export function AccountSidebar({ accounts, loading, error, selectedId, onSelect, onCreate, onRetry, open, onClose }) {
  const [query, setQuery] = useState('');

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return accounts;
    return accounts.filter((a) => a.name.toLowerCase().includes(q) || a.id.startsWith(q));
  }, [accounts, query]);

  return (
    <>
      <div className={`scrim ${open ? 'is-visible' : ''}`} onClick={onClose} aria-hidden="true" />
      <aside className={`sidebar ${open ? 'is-open' : ''}`} aria-label="Accounts">
        <div className="sidebar__head">
          <h2 className="sidebar__title">
            Accounts
            {accounts.length > 0 && <span className="count">{accounts.length}</span>}
          </h2>
          <button className="btn btn--primary btn--sm" onClick={onCreate}>
            <Icon name="plus" size={15} strokeWidth={2.2} />
            New account
          </button>
        </div>

        {accounts.length > 0 && (
          <label className="search">
            <Icon name="search" size={16} />
            <input
              type="search"
              placeholder="Search by name or ID"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              aria-label="Search accounts"
            />
          </label>
        )}

        <div className="sidebar__list">
          {loading && accounts.length === 0 && (
            <ul className="account-list" aria-hidden="true">
              {[0, 1, 2].map((i) => (
                <li key={i} className="account-item account-item--skeleton">
                  <span className="skeleton skeleton--text" />
                  <span className="skeleton skeleton--num" />
                </li>
              ))}
            </ul>
          )}

          {error && (
            <div className="sidebar__note">
              <p>{error}</p>
              <button className="btn btn--ghost btn--sm" onClick={onRetry}>
                <Icon name="refresh" size={14} /> Try again
              </button>
            </div>
          )}

          {!loading && !error && accounts.length === 0 && (
            <div className="sidebar__note">
              <p>No accounts yet. Open one to start recording credits and debits.</p>
            </div>
          )}

          {accounts.length > 0 && filtered.length === 0 && (
            <div className="sidebar__note">
              <p>No account matches “{query}”.</p>
            </div>
          )}

          <ul className="account-list">
            {filtered.map((a) => (
              <li key={a.id}>
                <button
                  className={`account-item ${a.id === selectedId ? 'is-active' : ''}`}
                  onClick={() => onSelect(a.id)}
                  aria-current={a.id === selectedId ? 'true' : undefined}
                >
                  <span className="account-item__avatar" aria-hidden="true">
                    {initials(a.name)}
                  </span>
                  <span className="account-item__text">
                    <span className="account-item__name">{a.name}</span>
                    <span className="account-item__id">{shortId(a.id)}</span>
                  </span>
                  <span className="account-item__balance num">{formatMoney(a.balance)}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      </aside>
    </>
  );
}

function initials(name) {
  const parts = name.trim().split(/\s+/);
  return ((parts[0]?.[0] ?? '') + (parts.length > 1 ? parts[parts.length - 1][0] : '')).toUpperCase();
}
