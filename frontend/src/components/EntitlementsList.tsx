import type { Booking, Entitlement } from '../types';
import { BOOKING_ICONS, formatCurrency } from '../utils';

export function EntitlementsList({ entitlements, bookings, onEvidenceClick }: {
  entitlements: Entitlement[];
  bookings: Booking[];
  onEvidenceClick: (id: string) => void;
}) {
  const bookingMap = new Map(bookings.map(b => [b.id, b]));

  if (entitlements.length === 0) return null;

  return (
    <div className="space-y-3">
      {entitlements.map(ent => {
        const booking = bookingMap.get(ent.booking_id);
        const isSupported = ent.status === 'supported';
        const isEstimate = ent.status === 'estimate';

        const statusColor = isSupported ? 'border-emerald-500/30 bg-emerald-500/5' :
          isEstimate ? 'border-amber-500/30 bg-amber-500/5' :
          'border-zinc-700/50';

        return (
          <div key={ent.id} className={`bg-[#111827] border rounded-xl p-4 ${statusColor}`}>
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1.5">
                  <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded border ${
                    isSupported ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' :
                    isEstimate ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' :
                    'bg-zinc-700/50 text-zinc-400 border-zinc-700'
                  }`}>
                    {isSupported ? '✓ SUPPORTED LEGAL RULE' : isEstimate ? '⚡ DEMO / ESTIMATE RULE' : '✗ NOT SUPPORTED'}
                  </span>
                  <span className="text-xs text-zinc-400 font-mono">{ent.rule_id}</span>
                </div>

                <p className="text-sm text-zinc-200 font-medium leading-relaxed">{ent.description}</p>

                {booking && (
                  <p className="text-xs text-zinc-400 mt-1">
                    Applicable to: <span className="text-zinc-300 font-semibold">{BOOKING_ICONS[booking.type]} {booking.reference}</span> · {booking.provider} ({booking.origin} → {booking.destination})
                  </p>
                )}

                {ent.conditions_met.length > 0 && (
                  <div className="mt-2.5 flex flex-wrap gap-1.5 items-center">
                    <span className="text-[11px] text-zinc-500 font-mono">Validated Conditions:</span>
                    {ent.conditions_met.map((c, i) => (
                      <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 font-mono border border-emerald-500/20">
                        ✓ {c}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="text-right shrink-0">
                {ent.amount !== null && ent.amount !== undefined ? (
                  <div>
                    <span className="text-[11px] text-zinc-500 block">Entitled Value</span>
                    <p className="text-lg font-bold text-emerald-400 font-mono">{formatCurrency(ent.amount)}</p>
                  </div>
                ) : (
                  <div>
                    <span className="text-[11px] text-zinc-500 block">Amount Status</span>
                    <p className="text-xs font-mono text-zinc-400 bg-zinc-800/80 px-2 py-1 rounded mt-0.5">
                      Statutory entitlement / Carrier-determined
                    </p>
                  </div>
                )}

                {ent.evidence_id && (
                  <button
                    onClick={() => onEvidenceClick(ent.evidence_id!)}
                    className="text-[10px] text-blue-400 hover:text-blue-300 font-mono mt-2 px-2 py-1 rounded bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 transition-colors block ml-auto"
                  >
                    ◉ Inspect Statutory Clause
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
