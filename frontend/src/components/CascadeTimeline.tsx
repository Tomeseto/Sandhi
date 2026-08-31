import type { Booking, CascadeResult } from '../types';
import { StatusBadge } from './StatusBadge';
import { BOOKING_ICONS } from '../utils';

export function CascadeTimeline({ bookings, cascade }: { bookings: Booking[]; cascade: CascadeResult | null }) {
  if (!cascade) return null;

  const effectMap = new Map(cascade.effects.map(e => [e.booking_id, e]));

  return (
    <div className="space-y-1">
      {bookings.map((b, i) => {
        const effect = effectMap.get(b.id);
        const status = effect?.new_status || b.status;
        const isLast = i === bookings.length - 1;

        return (
          <div key={b.id} className="flex items-stretch gap-3">
            {/* Timeline line */}
            <div className="flex flex-col items-center w-6 shrink-0">
              <div className={`w-3 h-3 rounded-full border-2 mt-1 ${
                status === 'confirmed' ? 'bg-emerald-500 border-emerald-400' :
                status === 'delayed' ? 'bg-amber-500 border-amber-400 animate-pulse-glow' :
                status === 'at_risk' ? 'bg-orange-500 border-orange-400 animate-pulse-glow' :
                'bg-red-500 border-red-400'
              }`} />
              {!isLast && (
                <div className={`w-0.5 flex-1 min-h-8 ${
                  status === 'confirmed' ? 'bg-emerald-500/30' :
                  status === 'delayed' ? 'bg-amber-500/30' :
                  status === 'at_risk' ? 'bg-orange-500/30' :
                  'bg-red-500/30'
                }`} />
              )}
            </div>
            {/* Content */}
            <div className="flex-1 pb-2">
              <div className="flex items-center gap-2">
                <span className="text-lg">{BOOKING_ICONS[b.type]}</span>
                <span className="text-sm font-semibold text-white">{b.reference}</span>
                <StatusBadge status={status} />
              </div>
              {effect && (
                <p className="text-xs text-zinc-400 mt-1 ml-7 leading-relaxed">{effect.explanation}</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
