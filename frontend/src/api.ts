// SANDHI API Client

import type {
  Trip, CascadeResult, Deadline, Entitlement,
  RecoveryOption, Evidence, GraphResponse,
} from './types';

const API_BASE = '/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  health: () => fetchJson<{ status: string; mode: string; version: string }>('/health'),

  getTrips: () => fetchJson<Trip[]>('/trips'),

  getTrip: (tripId: string) => fetchJson<Trip>(`/trips/${tripId}`),

  getGraph: (tripId: string) => fetchJson<GraphResponse>(`/trips/${tripId}/graph`),

  triggerDisruption: (tripId: string, bookingId: string, delayMinutes: number) =>
    fetchJson(`/trips/${tripId}/disruptions`, {
      method: 'POST',
      body: JSON.stringify({
        booking_id: bookingId,
        disruption_type: 'delay',
        delay_minutes: delayMinutes,
        source: 'user_input',
      }),
    }),

  getCascade: (tripId: string) => fetchJson<CascadeResult>(`/trips/${tripId}/cascade`),

  getDeadlines: (tripId: string) => fetchJson<Deadline[]>(`/trips/${tripId}/deadlines`),

  getEntitlements: (tripId: string) => fetchJson<Entitlement[]>(`/trips/${tripId}/entitlements`),

  getRecoveryOptions: (tripId: string) => fetchJson<RecoveryOption[]>(`/trips/${tripId}/recovery-options`),

  getEvidence: (evidenceId: string) => fetchJson<Evidence>(`/evidence/${evidenceId}`),

  resetTrip: (tripId: string) => fetchJson(`/trips/${tripId}/reset`, { method: 'POST' }),
};
