import { useCallback, useEffect, useState } from 'react';
import { api } from './api/client';
import { AccountSidebar } from './components/AccountSidebar';
import { AccountView } from './components/AccountView';
import { Icon } from './components/Icon';
import { NewAccountDialog } from './components/NewAccountDialog';
import { TopBar } from './components/TopBar';
import { useToast } from './components/Toasts';
import { useSelectedAccount } from './hooks/useSelectedAccount';
import { useTheme } from './hooks/useTheme';

export default function App() {
  const { theme, toggle } = useTheme();
  const toast = useToast();
  const [selectedId, select] = useSelectedAccount();

  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [creating, setCreating] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const loadAccounts = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.listAccounts();
      setAccounts(data);
      setError('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAccounts();
  }, [loadAccounts]);

  useEffect(() => {
    if (loading || error) return;
    const exists = accounts.some((a) => a.id === selectedId);
    if (!exists && accounts.length) select(accounts[0].id, { replace: true });
    if (!exists && !accounts.length && selectedId) select(null, { replace: true });
  }, [accounts, loading, error, selectedId, select]);

  const handleSelect = (id) => {
    if (id !== selectedId) select(id);
    setDrawerOpen(false);
  };

  const handleCreated = (account) => {
    setAccounts((list) => [account, ...list]);
    setCreating(false);
    setDrawerOpen(false);
    select(account.id);
    toast.push({ tone: 'success', title: 'Account opened', message: `${account.name} starts at 0.00.` });
  };

  const handleBalanceChange = useCallback((id, balance) => {
    setAccounts((list) => list.map((a) => (a.id === id ? { ...a, balance } : a)));
  }, []);

  const handleMissing = useCallback(
    (id) => {
      setAccounts((list) => list.filter((a) => a.id !== id));
    },
    [],
  );

  const hasSelection = selectedId && accounts.some((a) => a.id === selectedId);

  return (
    <div className="app">
      <TopBar theme={theme} onToggleTheme={toggle} onOpenMenu={() => setDrawerOpen(true)} />

      <div className="layout">
        <AccountSidebar
          accounts={accounts}
          loading={loading}
          error={error}
          selectedId={selectedId}
          onSelect={handleSelect}
          onCreate={() => setCreating(true)}
          onRetry={loadAccounts}
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
        />

        <main className="main" id="main">
          {hasSelection ? (
            <AccountView
              key={selectedId}
              accountId={selectedId}
              onBalanceChange={handleBalanceChange}
              onMissing={handleMissing}
            />
          ) : (
            !loading && (
              <div className="state state--welcome">
                <div className="state__art" aria-hidden="true">
                  <span />
                  <span />
                  <span />
                </div>
                <p className="state__title">
                  {error ? 'The ledger is not reachable' : 'Open your first account'}
                </p>
                <p className="state__text">
                  {error
                    ? error
                    : 'Accounts start at 0.00. From there you can post credits and debits, and every entry is kept as a permanent record.'}
                </p>
                {error ? (
                  <button className="btn btn--ghost" onClick={loadAccounts}>
                    <Icon name="refresh" size={15} /> Try again
                  </button>
                ) : (
                  <button className="btn btn--primary" onClick={() => setCreating(true)}>
                    <Icon name="plus" size={15} strokeWidth={2.2} /> New account
                  </button>
                )}
              </div>
            )
          )}
        </main>
      </div>

      <NewAccountDialog open={creating} onClose={() => setCreating(false)} onCreated={handleCreated} />
    </div>
  );
}
