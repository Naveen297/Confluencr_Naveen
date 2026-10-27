import { useCallback, useEffect, useState } from 'react';

export function useSelectedAccount() {
  const read = () => new URLSearchParams(window.location.search).get('account');
  const [selectedId, setSelectedId] = useState(read);

  useEffect(() => {
    const onPop = () => setSelectedId(read());
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);

  const select = useCallback((id, { replace = false } = {}) => {
    const url = new URL(window.location.href);
    if (id) url.searchParams.set('account', id);
    else url.searchParams.delete('account');
    window.history[replace ? 'replaceState' : 'pushState'](null, '', url);
    setSelectedId(id);
  }, []);

  return [selectedId, select];
}
