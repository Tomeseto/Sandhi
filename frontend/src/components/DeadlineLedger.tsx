import { useState, useEffect } from 'react';
import type { Booking, Deadline } from '../types';
import { BOOKING_ICONS, formatCountdown, formatCurrency, formatDate, formatTime } from '../utils';

export function DeadlineLedger({ deadlines, bookings, onEvidenceClick }: {
  deadlines: Deadline[];
  bookings: Booking[];
  onEvidenceClick: (id: string) => void;
}) {
  const [now, setNow] = useState(Date.now());
  const bookingMap = new Map(bookings.map(b => [b.id, b]));

  // Update countdown every second
  useEffect(() => {
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, []);

  if (deadlines.length === 0) return null;

  return (
    <div className="space-y-3">
      {deadlines.map(dl => {
        const booking = bookingMap.get(dl.booking_id);
        const expiresAt = new Date(dl.expires_at).getTime();
        const remaining = Math.max(0, (expiresAt - now) / 1000);
        const isExpired = remaining <= 0;
        const isUrgent = remaining > 0 && remaining < 3600; // < 1 hour

        return (
          <div key={dl.id} className={`bg-[#111827] border rounded-xl p-4 transition-all ${
            isExpired ? 'border-zinc-700/50 opacity-60' :
            isUrgent ? 'border-red-500/50 shadow-red-500/10 shadow-lg' :
            'border-amber-500/30'
          }`}>
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`font-mono text-2xl font-bold tabular-nums ${
                    isExpired ? 'text-zinc-500' : isUrgent ? 'text-red-400 animate-countdown' : 'text-amber-400'
                  }`}>
                    {formatCountdown(remaining)}
                  </span>
                  {isExpired && <span className="text-xs text-red-400 font-semibold">EXPIRED</span>}
                </div>
                <p className="text-sm text-zinc-200 font-medium">{dl.description.split('.')[0]}</p>
                <p className="text-xs text-zinc-500 mt-1">
                  {booking && <span>{BOOKING_ICONS[booking.type]} {booking.reference} · </span>}
                  Expires: {formatTime(dl.expires_at)} {formatDate(dl.expires_at)}
                </p>
              </div>
              <div className="text-right shrink-0">
                {dl.value_at_stake !== null && dl.value_at_stake !== undefined && (
                  <div>
                    <span className="text-xs text-zinc-500">At Stake</span>
                    <p className="text-lg font-bold text-white font-mono">{formatCurrency(dl.value_at_stake)}</p>
                  </div>
                )}
                {dl.evidence_id && (
                  <button onClick={() => onEvidenceClick(dl.evidence_id!)}
                    className="text-[10px] text-blue-400/70 hover:text-blue-300 font-mono mt-1 px-1.5 py-0.5 rounded bg-blue-500/10 hover:bg-blue-500/20 transition-colors">
                    ◉ source
                  </button>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
