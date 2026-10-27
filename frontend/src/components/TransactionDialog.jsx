import { formatDateTime, formatMoney } from '../lib/format';
import { CopyButton } from './CopyButton';
import { Dialog } from './Dialog';
import { Icon } from './Icon';

export function TransactionDialog({ transaction: tx, onClose }) {
  return (
    <Dialog open={Boolean(tx)} onClose={onClose} title="Entry details" size="sm">
      {tx && (
        <>
          <div className="dialog__body">
            <div className={`entry-amount entry-amount--${tx.type}`}>
              <span className="entry-amount__type">
                <Icon name={tx.type === 'credit' ? 'arrowIn' : 'arrowOut'} size={15} strokeWidth={2} />
                {tx.type === 'credit' ? 'Credit' : 'Debit'}
              </span>
              <span className="entry-amount__value num">
                {tx.type === 'credit' ? '+' : '−'}
                {formatMoney(tx.amount)}
              </span>
            </div>

            <dl className="details">
              <Row label="Description">{tx.description}</Row>
              <Row label="Reference ID" copy={tx.reference_id}>
                <code>{tx.reference_id}</code>
              </Row>
              <Row label="Balance after">
                <span className="num">{formatMoney(tx.balance_after)}</span>
              </Row>
              <Row label="Posted">{formatDateTime(tx.created_at)}</Row>
              <Row label="Transaction ID" copy={tx.id}>
                <code className="details__long">{tx.id}</code>
              </Row>
              <Row label="Account ID" copy={tx.account_id}>
                <code className="details__long">{tx.account_id}</code>
              </Row>
            </dl>
          </div>
          <footer className="dialog__footer dialog__footer--note">
            <Icon name="lock" size={15} />
            <span>Posted entries are permanent. They cannot be edited or deleted.</span>
          </footer>
        </>
      )}
    </Dialog>
  );
}

function Row({ label, copy, children }) {
  return (
    <div className="details__row">
      <dt>{label}</dt>
      <dd>
        {children}
        {copy && <CopyButton value={copy} label={`Copy ${label.toLowerCase()}`} />}
      </dd>
    </div>
  );
}
