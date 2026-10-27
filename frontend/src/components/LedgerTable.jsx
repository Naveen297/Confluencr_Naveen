import { formatDate, formatMoney, formatTime } from '../lib/format';
import { Pagination } from './Pagination';

const FILTERS = [
  { value: null, label: 'All', countKey: 'transaction_count' },
  { value: 'credit', label: 'Credits', countKey: 'credit_count' },
  { value: 'debit', label: 'Debits', countKey: 'debit_count' },
];

export function LedgerTable({ summary, history, loading, error, filter, onFilter, onPage, onLimit, onOpen, highlightId, onRetry }) {
  const rows = history?.data ?? [];

  return (
    <section className="ledger" aria-labelledby="ledger-title">
      <div className="ledger__head">
        <h2 id="ledger-title" className="section-title">
          Transaction history
        </h2>
        <div className="tabs" role="tablist" aria-label="Filter by type">
          {FILTERS.map((f) => (
            <button
              key={f.label}
              role="tab"
              aria-selected={filter === f.value}
              className={`tabs__tab ${f.value ? `tabs__tab--${f.value}` : ''} ${filter === f.value ? 'is-active' : ''}`}
              onClick={() => onFilter(f.value)}
            >
              {f.label}
              <span className="tabs__count num">{summary[f.countKey]}</span>
            </button>
          ))}
        </div>
      </div>

      <div className={`ledger__sheet ${loading && rows.length ? 'is-loading' : ''}`}>
        <table className="ledger__table">
          <thead>
            <tr>
              <th scope="col" className="th-date">
                Date
              </th>
              <th scope="col">Description</th>
              <th scope="col" className="cell-ref">
                Reference
              </th>
              <th scope="col" className="is-money is-debit">
                Debit
              </th>
              <th scope="col" className="is-money is-credit">
                Credit
              </th>
              <th scope="col" className="is-money">
                Balance
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((tx) => (
              <tr
                key={tx.id}
                className={`ledger__row ledger__row--${tx.type} ${tx.id === highlightId ? 'is-new' : ''}`}
                onClick={() => onOpen(tx)}
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onOpen(tx);
                  }
                }}
                aria-label={`${tx.type} of ${formatMoney(tx.amount)}, ${tx.description}`}
              >
                <td className="cell-date">
                  <span className="cell-date__day">{formatDate(tx.created_at)}</span>
                  <span className="cell-date__time">{formatTime(tx.created_at)}</span>
                </td>
                <td className="cell-desc">
                  <span className="cell-desc__text">{tx.description}</span>
                </td>
                <td className="cell-ref">
                  <code>{tx.reference_id}</code>
                </td>
                <td className="is-money is-debit num">{tx.type === 'debit' ? formatMoney(tx.amount) : ''}</td>
                <td className="is-money is-credit num">{tx.type === 'credit' ? formatMoney(tx.amount) : ''}</td>
                <td className="is-money cell-balance num">{formatMoney(tx.balance_after)}</td>
                <td className="cell-mobile-amount num" aria-hidden="true">
                  {tx.type === 'credit' ? '+' : '−'}
                  {formatMoney(tx.amount)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {loading && rows.length === 0 && (
          <div className="ledger__skeleton" aria-label="Loading entries">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="skeleton skeleton--row" />
            ))}
          </div>
        )}

        {error && (
          <div className="ledger__empty">
            <p className="ledger__empty-title">Could not load entries</p>
            <p>{error}</p>
            <button className="btn btn--ghost btn--sm" onClick={onRetry}>
              Try again
            </button>
          </div>
        )}

        {!loading && !error && rows.length === 0 && (
          <div className="ledger__empty">
            <p className="ledger__empty-title">
              {filter ? `No ${filter}s on this account yet` : 'No entries yet'}
            </p>
            <p>
              {filter
                ? 'Switch the filter to All to see every entry.'
                : 'Post a credit above to put money into this account.'}
            </p>
          </div>
        )}
      </div>

      {history && history.pagination.total_records > 0 && (
        <Pagination pagination={history.pagination} onPage={onPage} onLimit={onLimit} />
      )}
    </section>
  );
}
