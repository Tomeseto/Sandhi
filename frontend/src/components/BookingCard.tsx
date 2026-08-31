import { useState } from 'react';
import type { Booking, CascadeEffect } from '../types';
import { StatusBadge } from './StatusBadge';
import { BOOKING_ICONS, formatCurrency, formatTime } from '../utils';

export function BookingCard({ booking, effect, onEvidenceClick }: {
  booking: Booking;
  effect?: CascadeEffect;
  onEvidenceClick: (id: string) => void;
}) {
  const [showBreakdown, setShowBreakdown] = useState(false);
  const hasDelay = booking.actual_arrival && booking.actual_arrival !== booking.scheduled_arrival;
  const isDisrupted = booking.status !== 'confirmed';

  return (
    <div className={`bg-[#111827] border rounded-xl p-4 transition-all duration-300 ${
      booking.status === 'confirmed' ? 'border-zinc-700/50' :
      booking.status === 'delayed' ? 'border-amber-500/40 shadow-amber-500/10 shadow-lg' :
      booking.status === 'at_risk' ? 'border-orange-500/40 shadow-orange-500/10 shadow-lg' :
      ['infeasible', 'missed', 'forfeited'].includes(booking.status) ? 'border-red-500/40 shadow-red-500/10 shadow-lg' :
      'border-zinc-700/50'
    }`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{BOOKING_ICONS[booking.type] || '📦'}</span>
          <div>
            <h3 className="text-white font-semibold text-sm">{booking.reference}</h3>
            <p className="text-zinc-500 text-xs">{booking.provider}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={booking.status} />
        </div>
      </div>

      <div className="flex items-center gap-3 text-sm mb-2">
        <div className="text-zinc-300">
          <span className="text-zinc-500 text-xs">From</span>
          <p className="font-medium">{booking.origin}</p>
        </div>
        <span className="text-zinc-600">→</span>
        <div className="text-zinc-300">
          <span className="text-zinc-500 text-xs">To</span>
          <p className="font-medium">{booking.destination}</p>
        </div>
      </div>

      <div className="flex items-center gap-4 text-xs">
        <div>
          <span className="text-zinc-500">Scheduled</span>
          <p className="text-zinc-300 font-mono">{formatTime(booking.scheduled_departure)} → {formatTime(booking.scheduled_arrival)}</p>
        </div>
        {hasDelay && (
          <div>
            <span className="text-amber-500">Updated</span>
            <p className="text-amber-400 font-mono font-semibold">{formatTime(booking.actual_departure!)} → {formatTime(booking.actual_arrival!)}</p>
          </div>
        )}
        <div className="ml-auto">
          <span className="text-zinc-500">Price (Fixture)</span>
          <p className="text-zinc-300 font-mono">{formatCurrency(booking.price)}</p>
        </div>
      </div>

      {effect && isDisrupted && (
        <div className="mt-3 pt-3 border-t border-zinc-700/50">
          <div className="flex items-start justify-between gap-2">
            <p className="text-xs text-zinc-300 leading-relaxed">{effect.explanation}</p>
            {effect.slack_minutes !== undefined && effect.slack_minutes !== null && (
              <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded shrink-0 ${
                effect.slack_minutes < 0 ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                effect.slack_minutes < 15 ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
              }`}>
                Slack: {effect.slack_minutes.toFixed(0)} min
              </span>
            )}
          </div>

          {/* Interactive "Why did this break?" deterministic calculation */}
          <div className="mt-2">
            <button
              onClick={() => setShowBreakdown(!showBreakdown)}
              className="text-xs text-amber-400/90 hover:text-amber-300 font-medium flex items-center gap-1 transition-colors"
            >
              {showBreakdown ? '▾ Hide deterministic calculation' : '▸ Why did this break? (Deterministic math)'}
            </button>

            {showBreakdown && (
              <div className="mt-2 p-3 bg-zinc-900/80 border border-zinc-700/60 rounded-lg text-xs space-y-1.5 animate-slide-up font-mono">
                <div className="text-zinc-400 font-semibold mb-1 border-b border-zinc-800 pb-1 text-[11px] uppercase tracking-wider text-amber-400">
                  ⚡ Temporal Dependency Math
                </div>

                {effect.breakdown ? (
                  <>
                    {effect.breakdown.predecessor_reference && (
                      <div className="flex justify-between text-zinc-300">
                        <span className="text-zinc-400">Preceding Service ({effect.breakdown.predecessor_reference}) Arrival:</span>
                        <span>{effect.breakdown.predecessor_arrival}</span>
                      </div>
                    )}
                    {effect.breakdown.required_transfer_minutes !== undefined && (
                      <div className="flex justify-between text-zinc-300">
                        <span className="text-zinc-400">+ Minimum Transfer Buffer:</span>
                        <span>{effect.breakdown.required_transfer_minutes} min</span>
                      </div>
                    )}
                    {effect.breakdown.earliest_arrival && (
                      <div className="flex justify-between text-zinc-300 border-t border-zinc-800 pt-1">
                        <span className="text-zinc-400">= Earliest Possible Departure:</span>
                        <span>{effect.breakdown.earliest_arrival}</span>
                      </div>
                    )}
                    {effect.breakdown.scheduled_departure && (
                      <div className="flex justify-between text-zinc-300">
                        <span className="text-zinc-400">Scheduled Departure of this booking:</span>
                        <span>{effect.breakdown.scheduled_departure}</span>
                      </div>
                    )}
                    {effect.breakdown.slack_minutes !== undefined && (
                      <div className="flex justify-between font-bold border-t border-zinc-800 pt-1">
                        <span className={effect.breakdown.slack_minutes < 0 ? 'text-red-400' : 'text-emerald-400'}>
                          Deterministic Slack (Scheduled - Earliest):
                        </span>
                        <span className={effect.breakdown.slack_minutes < 0 ? 'text-red-400' : 'text-emerald-400'}>
                          {effect.breakdown.slack_minutes.toFixed(0)} min
                        </span>
                      </div>
                    )}
                    {effect.breakdown.verdict && (
                      <div className="mt-1 pt-1 text-[11px] text-zinc-400 italic">
                        Verdict: <span className="text-amber-300 not-italic font-semibold">{effect.breakdown.verdict}</span>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-zinc-400">
                    Source delay: {hasDelay ? `${formatTime(booking.actual_departure!)} → ${formatTime(booking.actual_arrival!)}` : 'Disrupted connection'}.
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {booking.evidence_ids.length > 0 && (
        <div className="mt-2.5 flex gap-1.5 flex-wrap items-center">
          <span className="text-[10px] text-zinc-500 font-mono">Provenance:</span>
          {booking.evidence_ids.map(eid => (
            <button
              key={eid}
              onClick={() => onEvidenceClick(eid)}
              className="text-[10px] text-blue-400/80 hover:text-blue-300 font-mono px-1.5 py-0.5 rounded bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 transition-colors"
            >
              ◉ {eid.replace('ev_', '')}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
