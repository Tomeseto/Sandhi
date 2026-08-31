// SANDHI Domain Types — mirrors backend Pydantic models

export type BookingType = 'flight' | 'train' | 'transfer' | 'hotel' | 'attraction';
export type BookingStatus = 'confirmed' | 'delayed' | 'at_risk' | 'infeasible' | 'missed' | 'forfeited' | 'cancelled' | 'unknown';
export type ProvenanceType = 'REAL_OBSERVATION' | 'HISTORICAL' | 'CACHE' | 'PUBLISHED_RULE' | 'MODEL_PREDICTION' | 'ESTIMATE' | 'DEMO_FIXTURE';
export type DeadlineStatus = 'active' | 'expired' | 'acted_upon' | 'not_applicable';
export type EntitlementStatus = 'supported' | 'not_supported' | 'estimate' | 'not_applicable';

export interface Booking {
  id: string;
  type: BookingType;
  provider: string;
  reference: string;
  origin: string;
  destination: string;
  scheduled_departure: string;
  scheduled_arrival: string;
  actual_departure?: string;
  actual_arrival?: string;
  price: number;
  currency: string;
  status: BookingStatus;
  metadata: Record<string, unknown>;
  evidence_ids: string[];
}

export interface Dependency {
  id: string;
  from_booking_id: string;
  to_booking_id: string;
  min_transfer_minutes: number;
  transfer_location: string;
  calculation_source: string;
}

export interface Trip {
  id: string;
  name: string;
  description: string;
  bookings: Booking[];
  dependencies: Dependency[];
}

export interface CascadeEffect {
  booking_id: string;
  original_status: BookingStatus;
  new_status: BookingStatus;
  slack_minutes?: number;
  explanation: string;
  affected_by?: string;
  breakdown?: {
    predecessor_reference?: string;
    predecessor_arrival?: string;
    required_transfer_minutes?: number;
    earliest_arrival?: string;
    scheduled_departure?: string;
    scheduled_arrival?: string;
    updated_departure?: string;
    updated_arrival?: string;
    delay_minutes?: number;
    slack_minutes?: number;
    verdict?: string;
  };
}

export interface CascadeResult {
  trip_id: string;
  disruption_id: string;
  effects: CascadeEffect[];
  timestamp: string;
}

export interface Deadline {
  id: string;
  booking_id: string;
  deadline_type: string;
  description: string;
  starts_at: string;
  expires_at: string;
  value_at_stake?: number;
  currency: string;
  status: DeadlineStatus;
  governing_rule_id?: string;
  evidence_id?: string;
  time_remaining_seconds?: number;
}

export interface Entitlement {
  id: string;
  booking_id: string;
  rule_id: string;
  entitlement_type: string;
  description: string;
  amount?: number;
  currency: string;
  status: EntitlementStatus;
  evidence_id?: string;
  conditions_met: string[];
  conditions_not_met: string[];
}

export interface RecoveryOption {
  id: string;
  mode: string;
  provider: string;
  reference: string;
  origin: string;
  destination: string;
  departure: string;
  arrival: string;
  price?: number;
  currency: string;
  source: string;
  source_provenance: ProvenanceType;
  feasible: boolean;
  failure_reason?: string;
  score: number;
  scoring_breakdown: Record<string, number>;
  downstream_effects: CascadeEffect[];
  evidence_ids: string[];
}

export interface Evidence {
  id: string;
  value: unknown;
  unit?: string;
  provenance_type: ProvenanceType;
  source: string;
  retrieved_at: string;
  source_reference?: string;
  confidence: number;
  description?: string;
}

export interface GraphNode {
  id: string;
  booking: Booking;
  status: BookingStatus;
}

export interface GraphEdge {
  from_id: string;
  to_id: string;
  min_transfer_minutes: number;
  transfer_location: string;
  slack_minutes?: number;
}

export interface GraphResponse {
  trip_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}
