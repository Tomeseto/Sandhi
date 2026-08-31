export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false });
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' });
}

export function formatCountdown(seconds: number): string {
  if (seconds <= 0) return 'EXPIRED';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 24) return `${Math.floor(h / 24)}d ${h % 24}h`;
  if (h > 0) return `${h}h ${m.toString().padStart(2, '0')}m`;
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

export function formatCurrency(amount: number | undefined | null, currency = 'INR'): string {
  if (amount === undefined || amount === null) return '—';
  return `₹${amount.toLocaleString('en-IN')}`;
}

export const STATUS_COLORS: Record<string, string> = {
  confirmed: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  delayed: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  at_risk: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  infeasible: 'bg-red-500/20 text-red-400 border-red-500/30',
  missed: 'bg-red-500/20 text-red-400 border-red-500/30',
  forfeited: 'bg-red-500/20 text-red-400 border-red-500/30',
  cancelled: 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30',
  unknown: 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30',
};

export const STATUS_LABELS: Record<string, string> = {
  confirmed: '✓ Confirmed',
  delayed: '⏳ Delayed',
  at_risk: '⚠ At Risk',
  infeasible: '✗ Infeasible',
  missed: '✗ Missed',
  forfeited: '✗ Forfeited',
  cancelled: '— Cancelled',
  unknown: '? Unknown',
};

export const BOOKING_ICONS: Record<string, string> = {
  flight: '✈',
  train: '🚂',
  transfer: '🚕',
  hotel: '🏨',
  attraction: '🏛',
};

export const PROVENANCE_COLORS: Record<string, string> = {
  REAL_OBSERVATION: 'text-emerald-400',
  PUBLISHED_RULE: 'text-blue-400',
  HISTORICAL: 'text-cyan-400',
  ESTIMATE: 'text-amber-400',
  DEMO_FIXTURE: 'text-zinc-400',
  CACHE: 'text-purple-400',
  MODEL_PREDICTION: 'text-orange-400',
};
