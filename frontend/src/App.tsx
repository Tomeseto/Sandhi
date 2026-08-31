import { useState, useEffect, useCallback } from 'react';
import { api } from './api';
import type {
  Trip, CascadeResult, Deadline, Entitlement,
  RecoveryOption,
} from './types';
import { formatCurrency } from './utils';
import { Section } from './components/Section';
import { BookingCard } from './components/BookingCard';
import { CascadeTimeline } from './components/CascadeTimeline';
import { DeadlineLedger } from './components/DeadlineLedger';
import { EntitlementsList } from './components/EntitlementsList';
import { RecoveryList } from './components/RecoveryList';
import { DisruptionTrigger } from './components/DisruptionTrigger';
import { EvidenceDrawer } from './components/EvidenceDrawer';

export default function App() {
  const [trip, setTrip] = useState<Trip | null>(null);
  const [cascade, setCascade] = useState<CascadeResult | null>(null);
  const [deadlines, setDeadlines] = useState<Deadline[]>([]);
  const [entitlements, setEntitlements] = useState<Entitlement[]>([]);
  const [recovery, setRecovery] = useState<RecoveryOption[]>([]);
  const [hasDisruption, setHasDisruption] = useState(false);
  const [evidenceDrawerId, setEvidenceDrawerId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const TRIP_ID = 'trip_demo_mumbai_agra';

  const loadTrip = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const tripData = await api.getTrip(TRIP_ID);
      setTrip(tripData);

      // Check if disruption already exists
      const cascadeData = await api.getCascade(TRIP_ID);
      if (cascadeData && 'effects' in cascadeData && (cascadeData as CascadeResult).effects?.length > 0) {
        setCascade(cascadeData as CascadeResult);
        setHasDisruption(true);
        const [dl, ent, rec] = await Promise.all([
          api.getDeadlines(TRIP_ID),
          api.getEntitlements(TRIP_ID),
          api.getRecoveryOptions(TRIP_ID),
        ]);
        setDeadlines(dl);
        setEntitlements(ent);
        setRecovery(rec);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load trip data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTrip();
  }, [loadTrip]);

  const handleTriggerDisruption = async (bookingId: string, delayMinutes: number) => {
    try {
      setError(null);
      await api.triggerDisruption(TRIP_ID, bookingId, delayMinutes);

      // Reload all data
      const [tripData, cascadeData, dl, ent, rec] = await Promise.all([
        api.getTrip(TRIP_ID),
        api.getCascade(TRIP_ID),
        api.getDeadlines(TRIP_ID),
        api.getEntitlements(TRIP_ID),
        api.getRecoveryOptions(TRIP_ID),
      ]);

      setTrip(tripData);
      setCascade(cascadeData as CascadeResult);
      setDeadlines(dl);
      setEntitlements(ent);
      setRecovery(rec);
      setHasDisruption(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to trigger disruption');
    }
  };

  const handleReset = async () => {
    try {
      await api.resetTrip(TRIP_ID);
      setCascade(null);
      setDeadlines([]);
      setEntitlements([]);
      setRecovery([]);
      setHasDisruption(false);
      await loadTrip();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4 animate-pulse">⟡</div>
          <p className="text-zinc-400">Loading SANDHI...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 max-w-md text-center">
          <p className="text-red-400 font-semibold mb-2">Connection Error</p>
          <p className="text-zinc-400 text-sm mb-4">{error}</p>
          <p className="text-zinc-500 text-xs">Make sure the backend is running on port 8000</p>
          <button onClick={loadTrip} className="mt-4 px-4 py-2 bg-zinc-700 hover:bg-zinc-600 text-white rounded-lg text-sm transition-colors">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!trip) return null;

  const effectMap = cascade ? new Map(cascade.effects.map(e => [e.booking_id, e])) : new Map();
  const totalAtStake = deadlines.reduce((sum, d) => sum + (d.value_at_stake || 0), 0);

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-zinc-800 bg-[#0a0e1a]/90 backdrop-blur-xl sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">⟡</span>
            <div>
              <h1 className="text-white font-bold text-lg tracking-tight">SANDHI</h1>
              <p className="text-zinc-500 text-xs">Travel Disruption Cascade Intelligence</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {hasDisruption && totalAtStake > 0 && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-1.5">
                <span className="text-xs text-red-400">Total at stake: </span>
                <span className="text-sm font-bold text-red-400 font-mono">{formatCurrency(totalAtStake)}</span>
              </div>
            )}
            <span className="text-xs bg-amber-500/10 text-amber-300 border border-amber-500/30 px-2.5 py-1 rounded-full font-mono font-medium">
              ⚡ DEMO MODE · Cached/Fixture Data
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 py-6 space-y-8">
        {/* Trip Header */}
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">{trip.name}</h2>
          <p className="text-zinc-400 text-sm">{trip.description}</p>
          <p className="text-zinc-600 text-xs mt-1 font-mono">Trip ID: {trip.id}</p>
        </div>

        {/* Disruption Trigger */}
        <DisruptionTrigger
          trip={trip}
          onTrigger={handleTriggerDisruption}
          onReset={handleReset}
          hasDisruption={hasDisruption}
        />

        {/* Cascade Timeline (visible after disruption) */}
        {hasDisruption && cascade && (
          <Section title="Cascade Analysis" subtitle="How the disruption propagates through your itinerary" icon="⛓" count={cascade.effects.length}>
            <CascadeTimeline bookings={trip.bookings} cascade={cascade} />
          </Section>
        )}

        {/* Deadline Ledger */}
        {hasDisruption && deadlines.length > 0 && (
          <Section title="Deadline Ledger" subtitle="Policy-derived countdowns — act before these expire" icon="⏱" count={deadlines.length}>
            <DeadlineLedger deadlines={deadlines} bookings={trip.bookings} onEvidenceClick={setEvidenceDrawerId} />
          </Section>
        )}

        {/* Entitlements */}
        {hasDisruption && entitlements.length > 0 && (
          <Section title="Entitlements" subtitle="Computed from Indian travel regulations — click source to verify" icon="⚖" count={entitlements.length}>
            <EntitlementsList entitlements={entitlements} bookings={trip.bookings} onEvidenceClick={setEvidenceDrawerId} />
          </Section>
        )}

        {/* Recovery Options */}
        {hasDisruption && recovery.length > 0 && (
          <Section title="Recovery Options" subtitle="Feasibility-checked alternatives ranked by time, cost, and downstream impact" icon="🔄" count={recovery.length}>
            <RecoveryList options={recovery} onEvidenceClick={setEvidenceDrawerId} />
          </Section>
        )}

        {/* Itinerary Bookings */}
        <Section title="Itinerary" subtitle={hasDisruption ? 'Updated booking statuses after disruption' : 'All bookings in this trip'} icon="📋" count={trip.bookings.length}>
          <div className="grid gap-3">
            {trip.bookings.map(b => (
              <BookingCard
                key={b.id}
                booking={b}
                effect={effectMap.get(b.id)}
                onEvidenceClick={setEvidenceDrawerId}
              />
            ))}
          </div>
        </Section>

        {/* Footer */}
        <footer className="border-t border-zinc-800 pt-6 pb-8 text-center">
          <p className="text-zinc-600 text-xs">
            SANDHI MVP · A delay is not an event — it is a set of countdowns nobody told you had started.
          </p>
          <p className="text-zinc-700 text-xs mt-1">
            All computations are deterministic. No AI/LLM in the decision path. Provenance tracked for all values.
          </p>
        </footer>
      </main>

      {/* Evidence Drawer */}
      {evidenceDrawerId && (
        <EvidenceDrawer evidenceId={evidenceDrawerId} onClose={() => setEvidenceDrawerId(null)} />
      )}
    </div>
  );
}
