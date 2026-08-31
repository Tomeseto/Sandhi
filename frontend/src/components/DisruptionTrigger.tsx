import { useState } from 'react';
import type { Trip } from '../types';

export function DisruptionTrigger({ trip, onTrigger, onReset, hasDisruption }: {
  trip: Trip;
  onTrigger: (bookingId: string, delayMinutes: number) => void;
  onReset: () => void;
  hasDisruption: boolean;
}) {
  const [delay, setDelay] = useState(170); // 2h50m default
  const [triggering, setTriggering] = useState(false);

  const flightBooking = trip.bookings.find(b => b.type === 'flight');

  if (!flightBooking) return null;

  const handleTrigger = async () => {
    setTriggering(true);
    await onTrigger(flightBooking.id, delay);
    setTriggering(false);
  };

  return (
    <div className="bg-gradient-to-br from-amber-500/10 to-red-500/10 border border-amber-500/30 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xl">⚡</span>
        <h3 className="text-white font-semibold">Disruption Simulator</h3>
      </div>

      {!hasDisruption ? (
        <>
          <p className="text-sm text-zinc-400 mb-4">
            Simulate a flight delay to see how disruptions cascade through your itinerary.
          </p>
          <div className="flex items-end gap-3">
            <div className="flex-1">
              <label className="text-xs text-zinc-500 mb-1 block">Flight {flightBooking.reference} Delay</label>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min={30}
                  max={300}
                  step={10}
                  value={delay}
                  onChange={e => setDelay(Number(e.target.value))}
                  className="flex-1 accent-amber-500"
                />
                <span className="text-amber-400 font-mono font-bold text-lg w-24 text-right">
                  {Math.floor(delay / 60)}h {delay % 60}m
                </span>
              </div>
            </div>
            <button
              onClick={handleTrigger}
              disabled={triggering}
              className="px-5 py-2.5 bg-amber-500 hover:bg-amber-600 disabled:bg-amber-500/50 text-black font-bold rounded-lg transition-colors text-sm shrink-0"
            >
              {triggering ? 'Propagating...' : 'Trigger Delay ⚡'}
            </button>
          </div>
        </>
      ) : (
        <div className="flex items-center justify-between">
          <p className="text-sm text-amber-400">
            ✓ Disruption active — flight delayed by {Math.floor(delay / 60)}h {delay % 60}m
          </p>
          <button
            onClick={onReset}
            className="px-4 py-2 bg-zinc-700 hover:bg-zinc-600 text-white rounded-lg transition-colors text-sm"
          >
            Reset Scenario
          </button>
        </div>
      )}
    </div>
  );
}
