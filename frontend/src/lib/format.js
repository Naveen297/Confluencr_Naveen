const money = new Intl.NumberFormat(undefined, {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export const formatMoney = (value) => money.format(value ?? 0);

const dateShort = new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
const time = new Intl.DateTimeFormat(undefined, { hour: '2-digit', minute: '2-digit' });
const full = new Intl.DateTimeFormat(undefined, { dateStyle: 'long', timeStyle: 'medium' });

export const formatDate = (iso) => (iso ? dateShort.format(new Date(iso)) : '');
export const formatTime = (iso) => (iso ? time.format(new Date(iso)) : '');
export const formatDateTime = (iso) => (iso ? full.format(new Date(iso)) : '');

export const shortId = (id = '') => id.slice(0, 8);

export function generateReference() {
  const d = new Date();
  const stamp = [d.getFullYear() % 100, d.getMonth() + 1, d.getDate()]
    .map((n) => String(n).padStart(2, '0'))
    .join('');
  const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  let tail = '';
  const bytes = crypto.getRandomValues(new Uint8Array(4));
  bytes.forEach((b) => (tail += alphabet[b % alphabet.length]));
  return `TXN-${stamp}-${tail}`;
}

export function parseAmount(raw) {
  const value = String(raw).trim();
  if (!value) return { error: 'Enter an amount.' };
  if (!/^\d+(\.\d{1,2})?$/.test(value)) {
    return { error: 'Use a positive number with up to two decimals.' };
  }
  const amount = Number(value);
  if (amount <= 0) return { error: 'Amount must be greater than zero.' };
  if (amount > 1_000_000_000) return { error: 'Amount is above the 1,000,000,000 limit.' };
  return { amount };
}
