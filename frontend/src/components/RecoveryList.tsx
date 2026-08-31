import { useState } from 'react';
import type { RecoveryOption } from '../types';
import { formatCurrency, formatTime, PROVENANCE_COLORS } from '../utils';

export function RecoveryList({ options, onEvidenceClick }: {
  options: RecoveryOption[];
  onEvidenceClick: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState<string | null>(null);

  if (options.length === 0) return null;

  return (
    <div className="space-y-3">
      {options.map((opt, idx) => (
        <div key={opt.id} className={`bg-[#111827] border rounded-xl p-4 transition-all ${
          opt.feasible ? 'border-emerald-500/30 hover:border-emerald-500/50' :
          'border-red-500/30 opacity-90'
        }`}>
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <span className={`text-xs font-bold px-2 py-0.5 rounded border ${
                  idx === 0 && opt.feasible ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40' :
                  opt.feasible ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' :
                  'bg-red-500/20 text-red-400 border-red-500/30'
                }`}>
                  {idx === 0 && opt.feasible ? '★ RECOMMENDED OPTION' : opt.feasible ? '✓ FEASIBLE ALTERNATIVE' : '✗ REJECTED / INFEASIBLE'}
                </span>
                <span className="text-xs text-zinc-400 font-mono">Score: {opt.score.toFixed(3)}</span>
              </div>

              <div className="flex items-center gap-2.5">
                <span className="text-xl">{opt.mode === 'train' ? '🚂' : opt.mode === 'flight' ? '✈' : '🚌'}</span>
                <div>
                  <p className="text-sm font-semibold text-white">{opt.reference} — {opt.provider}</p>
                  <p className="text-xs text-zinc-400">{opt.origin} → {opt.destination}</p>
                </div>
              </div>

              <div className="flex items-center gap-4 mt-2 text-xs">
                <div>
                  <span className="text-zinc-500">Departure</span>
                  <p className="text-zinc-200 font-mono">{formatTime(opt.departure)}</p>
                </div>
                <div>
                  <span className="text-zinc-500">Arrival</span>
                  <p className="text-zinc-200 font-mono">{formatTime(opt.arrival)}</p>
                </div>
                {opt.price && (
                  <div>
                    <span className="text-zinc-500">Price</span>
                    <p className="text-zinc-200 font-mono">{formatCurrency(opt.price)}</p>
                  </div>
                )}
                <div>
                  <span className="text-zinc-500">Data Source</span>
                  <p className={`font-mono text-[11px] ${PROVENANCE_COLORS[opt.source_provenance] || 'text-zinc-400'}`}>
                    {opt.source_provenance}
                  </p>
                </div>
              </div>

              {!opt.feasible && opt.failure_reason && (
                <div className="mt-3 p-2.5 bg-red-950/40 border border-red-500/30 rounded-lg">
                  <div className="text-[11px] font-bold text-red-400 uppercase tracking-wider mb-1">
                    Constraint Infeasibility Reason
                  </div>
                  <p className="text-xs text-red-300 font-mono">{opt.failure_reason}</p>
                </div>
              )}
            </div>
          </div>

          <div className="mt-3 flex items-center gap-3">
            <button
              onClick={() => setExpanded(expanded === opt.id ? null : opt.id)}
              className="text-xs text-blue-400/90 hover:text-blue-300 font-medium transition-colors"
            >
              {expanded === opt.id ? '▾ Hide transparent scoring details' : '▸ Why this ranking? (Scoring breakdown)'}
            </button>

            {opt.evidence_ids.length > 0 && (
              <button
                onClick={() => onEvidenceClick(opt.evidence_ids[0])}
                className="text-[10px] text-zinc-400 hover:text-zinc-200 font-mono px-1.5 py-0.5 rounded bg-zinc-800 border border-zinc-700 transition-colors ml-auto"
              >
                ◉ Source Fixture
              </button>
            )}
          </div>

          {expanded === opt.id && (
            <div className="mt-2.5 p-3 bg-zinc-900/90 border border-zinc-800 rounded-lg animate-slide-up space-y-2">
              <p className="text-xs text-zinc-400 font-mono font-semibold border-b border-zinc-800 pb-1">
                Deterministic Multi-Factor Scoring (Lower score = Better alternative):
              </p>
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                {Object.entries(opt.scoring_breakdown).map(([key, val]) => (
                  <div key={key} className="flex justify-between bg-zinc-800/40 px-2 py-1 rounded">
                    <span className="text-zinc-400 capitalize">{key.replace(/_/g, ' ')}:</span>
                    <span className="text-zinc-200 font-bold">{typeof val === 'number' ? val.toFixed(3) : val}</span>
                  </div>
                ))}
              </div>
              {opt.downstream_effects.length > 0 && (
                <div className="mt-2 pt-2 border-t border-zinc-800 text-xs">
                  <p className="text-zinc-400 mb-1 font-semibold">Simulated Downstream Graph Effects:</p>
                  {opt.downstream_effects.map((de, i) => (
                    <p key={i} className="text-zinc-300 text-[11px] font-mono">• {de.explanation}</p>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
