import { useState, useEffect } from 'react';
import { api } from '../api';
import type { Evidence } from '../types';
import { PROVENANCE_COLORS } from '../utils';

export function EvidenceDrawer({ evidenceId, onClose }: { evidenceId: string; onClose: () => void }) {
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getEvidence(evidenceId)
      .then(setEvidence)
      .catch(() => setEvidence(null))
      .finally(() => setLoading(false));
  }, [evidenceId]);

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-[#111827] border border-zinc-700/50 rounded-2xl max-w-lg w-full p-6 shadow-2xl animate-slide-up" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <span className="text-blue-400">◉</span> Evidence / Provenance
          </h3>
          <button onClick={onClose} className="text-zinc-400 hover:text-white transition-colors text-xl">✕</button>
        </div>

        {loading ? (
          <div className="text-zinc-400 text-center py-8">Loading evidence...</div>
        ) : evidence ? (
          <div className="space-y-4">
            <div className="bg-zinc-800/50 rounded-xl p-4 space-y-3">
              {evidence.value !== null && evidence.value !== undefined && (
                <div>
                  <span className="text-xs text-zinc-500 uppercase tracking-wider">Value</span>
                  <p className="text-white font-mono text-lg">
                    {evidence.unit === 'INR' ? `₹${evidence.value}` : `${evidence.value}`}
                    {evidence.unit && evidence.unit !== 'INR' && <span className="text-zinc-400 text-sm ml-1">{evidence.unit}</span>}
                  </p>
                </div>
              )}
              <div>
                <span className="text-xs text-zinc-500 uppercase tracking-wider">Provenance Type</span>
                <p className={`font-mono font-semibold ${PROVENANCE_COLORS[evidence.provenance_type] || 'text-zinc-400'}`}>
                  {evidence.provenance_type}
                </p>
              </div>
              <div>
                <span className="text-xs text-zinc-500 uppercase tracking-wider">Source</span>
                <p className="text-zinc-200">{evidence.source}</p>
              </div>
              {evidence.source_reference && (
                <div>
                  <span className="text-xs text-zinc-500 uppercase tracking-wider">Reference</span>
                  <p className="text-zinc-300 text-sm">{evidence.source_reference}</p>
                </div>
              )}
              <div>
                <span className="text-xs text-zinc-500 uppercase tracking-wider">Retrieved At</span>
                <p className="text-zinc-400 font-mono text-sm">{new Date(evidence.retrieved_at).toLocaleString('en-IN')}</p>
              </div>
              <div>
                <span className="text-xs text-zinc-500 uppercase tracking-wider">Confidence</span>
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex-1 h-2 bg-zinc-700 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500 rounded-full" style={{ width: `${evidence.confidence * 100}%` }} />
                  </div>
                  <span className="text-zinc-400 font-mono text-sm">{(evidence.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
              {evidence.description && (
                <div>
                  <span className="text-xs text-zinc-500 uppercase tracking-wider">Description</span>
                  <p className="text-zinc-300 text-sm">{evidence.description}</p>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="text-zinc-500 text-center py-8">Evidence not found</div>
        )}
      </div>
    </div>
  );
}
