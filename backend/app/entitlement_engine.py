"""
SANDHI Entitlement Engine

Deterministic computation of Indian travel entitlements from verified policy rules.
Never fabricates legal content. Unsupported rules return NOT_SUPPORTED status.
No AI/ML involved.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
import uuid

from app.models import (
    Booking, BookingStatus, BookingType, CascadeEffect,
    Disruption, Entitlement, EntitlementStatus, Evidence,
    PolicyRule, ProvenanceType,
)


def compute_entitlements(
    bookings: list[Booking],
    effects: list[CascadeEffect],
    policy_rules: list[PolicyRule],
    disruption: Disruption,
    now: Optional[datetime] = None,
) -> tuple[list[Entitlement], list[Evidence]]:
    """
    Compute entitlements for all affected bookings.

    For each affected booking:
    1. Find applicable policy rules
    2. Evaluate conditions
    3. Compute entitlement if rule is verified
    4. Mark as NOT_SUPPORTED if rule cannot be verified

    All calculations are deterministic.
    """
    if now is None:
        now = datetime.utcnow()

    entitlements: list[Entitlement] = []
    evidence_list: list[Evidence] = []
    booking_map = {b.id: b for b in bookings}
    effect_map = {e.booking_id: e for e in effects}

    for effect in effects:
        booking = booking_map.get(effect.booking_id)
        if booking is None:
            continue

        for rule in policy_rules:
            ent = _try_compute_entitlement(
                booking, effect, rule, disruption, now,
            )
            if ent is not None:
                e, ev = ent
                entitlements.append(e)
                evidence_list.append(ev)

    return entitlements, evidence_list


def _try_compute_entitlement(
    booking: Booking,
    effect: CascadeEffect,
    rule: PolicyRule,
    disruption: Disruption,
    now: datetime,
) -> tuple[Entitlement, Evidence] | None:
    """
    Try to compute an entitlement from a booking + effect + rule combination.
    Returns None if the rule doesn't apply.
    """
    # Check conditions
    conditions_met: list[str] = []
    conditions_not_met: list[str] = []

    for condition in rule.conditions:
        actual = _get_field_value(condition.field, booking, effect, disruption)
        met = _evaluate_condition(actual, condition.operator, condition.value)

        desc = f"{condition.field} {condition.operator} {condition.value}"
        if met:
            conditions_met.append(desc)
        else:
            conditions_not_met.append(desc)

    # If any condition is not met, rule doesn't apply
    if conditions_not_met:
        return None

    # Rule applies — compute entitlement
    ent_id = f"ent_{booking.id}_{rule.rule_id}_{uuid.uuid4().hex[:6]}"
    ev_id = f"ev_{ent_id}"

    # Determine amount
    amount = _compute_amount(rule, booking)

    # Determine status based on rule verification level
    if rule.status == "VERIFIED_STRUCTURE":
        status = EntitlementStatus.SUPPORTED
    elif rule.status == "DEMO":
        status = EntitlementStatus.ESTIMATE
    else:
        status = EntitlementStatus.NOT_SUPPORTED

    # Create evidence
    evidence = Evidence(
        id=ev_id,
        value=amount,
        unit="INR" if amount else None,
        provenance_type=(
            ProvenanceType.PUBLISHED_RULE
            if rule.status == "VERIFIED_STRUCTURE"
            else ProvenanceType.DEMO_FIXTURE
        ),
        source=rule.source_document,
        retrieved_at=now,
        source_reference=rule.clause_reference,
        confidence=0.8 if rule.status == "VERIFIED_STRUCTURE" else 0.5,
        description=f"Entitlement: {rule.result.description}",
    )

    entitlement = Entitlement(
        id=ent_id,
        booking_id=booking.id,
        rule_id=rule.rule_id,
        entitlement_type=rule.result.entitlement_type,
        description=rule.result.description,
        amount=amount,
        currency=booking.currency,
        status=status,
        evidence_id=ev_id,
        conditions_met=conditions_met,
        conditions_not_met=conditions_not_met,
    )

    return entitlement, evidence


def _get_field_value(field: str, booking: Booking, effect: CascadeEffect, disruption: Disruption):
    """Extract a field value for condition evaluation."""
    if field == "booking_type":
        return booking.type.value
    if field == "booking_status":
        return effect.new_status.value
    if field == "delay_minutes":
        # For the disrupted booking, use the disruption's delay
        if effect.booking_id == disruption.booking_id:
            return disruption.delay_minutes
        # For downstream bookings, use slack
        if effect.slack_minutes is not None:
            return abs(effect.slack_minutes)
        return 0
    return None


def _evaluate_condition(actual, operator: str, expected) -> bool:
    """Evaluate a single condition."""
    if actual is None:
        return False
    if operator == "eq":
        return actual == expected
    if operator == "ne":
        return actual != expected
    if operator == "gt":
        return actual > expected
    if operator == "lt":
        return actual < expected
    if operator == "gte":
        return actual >= expected
    if operator == "lte":
        return actual <= expected
    if operator == "in":
        return actual in expected
    return False


def _compute_amount(rule: PolicyRule, booking: Booking) -> float | None:
    """
    Compute the entitlement amount.

    Only returns an amount when it can be deterministically calculated
    from verified rules. Returns None for amounts that depend on
    unverified or complex rules.
    """
    result = rule.result

    # Fixed amount if specified
    if result.fixed_amount is not None:
        return result.fixed_amount

    # Rule-specific calculations
    if rule.rule_id == "RAIL_TDR_MISSED":
        # TDR refund: booking price is the maximum refundable
        # Actual refund depends on class, distance, and filing time
        # Return booking price as the "at stake" value
        return booking.price

    if rule.rule_id == "HOTEL_FREE_CANCEL":
        # Full refund if cancelled within window
        return booking.price

    if rule.rule_id == "ATTRACTION_NOSHOW":
        # Forfeited ticket value
        return booking.price

    # For rules where amount depends on unverified formulas (e.g., DGCA compensation),
    # return None rather than fabricating
    if rule.rule_id in ("DGCA_DELAY_2HR", "DGCA_DELAY_COMPENSATION"):
        return None

    return None
