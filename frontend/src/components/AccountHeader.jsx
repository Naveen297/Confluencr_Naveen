import { formatDate, formatMoney } from '../lib/format';
import { CopyButton } from './CopyButton';

export function AccountHeader({ account }) {
  const { summary } = account;
  const volume = summary.total_credits + summary.total_debits;
  const creditShare = volume ? (summary.total_credits / volume) * 100 : 50;

  return (
    <section className="account-header" aria-labelledby="account-title">
      <div className="account-header__identity">
        <h1 id="account-title" className="account-header__name">
          {account.name}
        </h1>
        <div className="account-header__meta">
          <span className="id-chip" title={account.id}>
            <span className="id-chip__value">{account.id}</span>
            <CopyButton value={account.id} label="Copy account ID" />
          </span>
          <span className="account-header__opened">Opened {formatDate(account.created_at)}</span>
        </div>
      </div>

      <div className="account-header__balance">
        <span className="account-header__balance-label">Current balance</span>
        <span className="account-header__balance-value num" aria-live="polite">
          {formatMoney(account.balance)}
        </span>
      </div>

      <dl className="totals">
        <div className="totals__item totals__item--credit">
          <dt>Total credits</dt>
          <dd className="num">{formatMoney(summary.total_credits)}</dd>
        </div>
        <div className="totals__item totals__item--debit">
          <dt>Total debits</dt>
          <dd className="num">{formatMoney(summary.total_debits)}</dd>
        </div>
        <div className="totals__item">
          <dt>Entries</dt>
          <dd className="num">{summary.transaction_count}</dd>
        </div>
        <div
          className="totals__bar"
          role="img"
          aria-label={
            volume
              ? `Credits are ${Math.round(creditShare)}% of all money moved`
              : 'No money has moved yet'
          }
        >
          <span className={`totals__bar-credit ${volume ? '' : 'is-empty'}`} style={{ width: `${creditShare}%` }} />
          <span className={`totals__bar-debit ${volume ? '' : 'is-empty'}`} />
        </div>
      </dl>
    </section>
  );
}
