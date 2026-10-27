import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../api/client';
import { formatMoney } from '../lib/format';
import { AccountHeader } from './AccountHeader';
import { EntryForm } from './EntryForm';
import { LedgerTable } from './LedgerTable';
import { TransactionDialog } from './TransactionDialog';
import { useToast } from './Toasts';

export function AccountView({ accountId, onBalanceChange, onMissing }) {
  const toast = useToast();
  const [account, setAccount] = useState(null);
  const [accountError, setAccountError] = useState('');

  const [query, setQuery] = useState({ type: null, page: 1, limit: 10 });
  const [history, setHistory] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState('');

  const [openTx, setOpenTx] = useState(null);
  const [highlightId, setHighlightId] = useState(null);
  const historyAbort = useRef(null);

  const loadAccount = useCallback(
    async (signal) => {
      try {
        const data = await api.getAccount(accountId, { signal });
        setAccount(data);
        setAccountError('');
        return data;
      } catch (err) {
        if (err.name === 'AbortError') return null;
        if (err.code === 'ACCOUNT_NOT_FOUND') onMissing(accountId);
        setAccountError(err.message);
        return null;
      }
    },
    [accountId, onMissing],
  );

  const loadHistory = useCallback(
    async (q) => {
      historyAbort.current?.abort();
      const controller = new AbortController();
      historyAbort.current = controller;
      setHistoryLoading(true);
      try {
        const data = await api.listTransactions(accountId, q, { signal: controller.signal });
        if (data.pagination.total_pages > 0 && q.page > data.pagination.total_pages) {
          setQuery((cur) => ({ ...cur, page: data.pagination.total_pages }));
          return;
        }
        setHistory(data);
        setHistoryError('');
      } catch (err) {
        if (err.name !== 'AbortError') setHistoryError(err.message);
      } finally {
        if (historyAbort.current === controller) setHistoryLoading(false);
      }
    },
    [accountId],
  );

  useEffect(() => {
    const controller = new AbortController();
    loadAccount(controller.signal);
    return () => controller.abort();
  }, [accountId, loadAccount]);

  useEffect(() => {
    loadHistory(query);
  }, [query, loadHistory]);

  useEffect(() => () => historyAbort.current?.abort(), []);

  const handlePosted = async (tx) => {
    toast.push({
      tone: 'success',
      title: `${tx.type === 'credit' ? 'Credit' : 'Debit'} of ${formatMoney(tx.amount)} posted`,
      message: `Balance is now ${formatMoney(tx.balance_after)}.`,
    });
    setHighlightId(tx.id);
    window.setTimeout(() => setHighlightId((id) => (id === tx.id ? null : id)), 2400);

    const fresh = await loadAccount();
    if (fresh) onBalanceChange(fresh.id, fresh.balance);
    setQuery((q) => ({ ...q, page: 1 }));
  };

  if (accountError && !account) {
    return (
      <div className="state">
        <p className="state__title">This account could not be loaded</p>
        <p className="state__text">{accountError}</p>
      </div>
    );
  }

  if (!account) {
    return (
      <div className="account-view" aria-busy="true">
        <div className="skeleton skeleton--title" />
        <div className="skeleton skeleton--block" />
        <div className="skeleton skeleton--sheet" />
      </div>
    );
  }

  return (
    <div className="account-view">
      <AccountHeader account={account} />
      <div className="sheet">
        <EntryForm account={account} onPosted={handlePosted} onShowEntry={setOpenTx} />
        <LedgerTable
          summary={account.summary}
          history={history}
          loading={historyLoading}
          error={historyError}
          filter={query.type}
          onFilter={(type) => setQuery((q) => ({ ...q, type, page: 1 }))}
          onPage={(page) => setQuery((q) => ({ ...q, page }))}
          onLimit={(limit) => setQuery((q) => ({ ...q, limit, page: 1 }))}
          onOpen={setOpenTx}
          onRetry={() => loadHistory(query)}
          highlightId={highlightId}
        />
      </div>
      <TransactionDialog transaction={openTx} onClose={() => setOpenTx(null)} />
    </div>
  );
}
