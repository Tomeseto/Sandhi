"""
SANDHI Deadline Engine

Deterministic computation of policy-derived deadlines.
Produces the Deadline Ledger — countdown timers for refund/cancellation/claim windows.
No AI/ML involved.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
import uuid

from app.models import (
    Booking, BookingStatus, BookingType, CascadeEffect,
    Deadline, DeadlineStatus, Evidence, PolicyRule, ProvenanceType,
)


def compute_deadlines(
    bookings: list[Booking],
    effects: list[CascadeEffect],
    policy_rules: list[PolicyRule],
    disruption_time: datetime,
    now: Optional[datetime] = None,
) -> tuple[list[Deadline], list[Evidence]]:
    """
    Compute the Deadline Ledger from cascade effects and policy rules.

    For each affected booking:
    1. Find applicable policy rules
    2. Calculate deadline timestamps
    3. Determine value at stake
    4. Create Deadline objects with evidence

    All calculations are deterministic.
    """
    if now is None:
        now = datetime.utcnow()

    deadlines: list[Deadline] = []
    evidence_list: list[Evidence] = []
    booking_map = {b.id: b for b in bookings}
    effect_map = {e.booking_id: e for e in effects}

    for effect in effects:
        booking = booking_map.get(effect.booking_id)
        if booking is None:
            continue

        # Find applicable rules
        for rule in policy_rules:
            deadline = _try_create_deadline(
                booking, effect, rule, disruption_time, now,
            )
            if deadline is not None:
                dl, ev = deadline
                deadlines.append(dl)
                evidence_list.append(ev)

    # Sort by urgency (expires_at ascending)
    deadlines.sort(key=lambda d: d.expires_at)

    # Update time_remaining_seconds
    for dl in deadlines:
        remaining = (dl.expires_at - now).total_seconds()
        dl.time_remaining_seconds = max(0, remaining)
        if remaining <= 0:
            dl.status = DeadlineStatus.EXPIRED

    return deadlines, evidence_list


def _try_create_deadline(
    booking: Booking,
    effect: CascadeEffect,
    rule: PolicyRule,
    disruption_time: datetime,
    now: datetime,
) -> tuple[Deadline, Evidence] | None:
    """
    Try to create a deadline from a booking + effect + rule combination.
    Returns None if the rule doesn't apply.
    """
    # Check if rule applies to this booking type
    if not _check_conditions(rule, booking, effect):
        return None

    # Calculate deadline based on rule type
    dl_id = f"dl_{booking.id}_{rule.rule_id}_{uuid.uuid4().hex[:6]}"
    ev_id = f"ev_{dl_id}"

    starts_at = disruption_time
    expires_at = _calculate_expiry(rule, booking, disruption_time)
    value_at_stake = _calculate_value_at_stake(rule, booking)

    # Determine description
    description = rule.result.description

    # Determine deadline type based on entitlement type
    deadline_type = rule.result.entitlement_type

    # Create evidence
    evidence = Evidence(
        id=ev_id,
        value=value_at_stake,
        unit="INR" if value_at_stake else None,
        provenance_type=(
            ProvenanceType.PUBLISHED_RULE
            if rule.status == "VERIFIED_STRUCTURE"
            else ProvenanceType.DEMO_FIXTURE
        ),
        source=rule.source_document,
        retrieved_at=now,
        source_reference=rule.clause_reference,
        confidence=0.8 if rule.status == "VERIFIED_STRUCTURE" else 0.5,
        description=f"Deadline evidence: {description}",
    )

    deadline = Deadline(
        id=dl_id,
        booking_id=booking.id,
        deadline_type=deadline_type,
        description=description,
        starts_at=starts_at,
        expires_at=expires_at,
        value_at_stake=value_at_stake,
        currency=booking.currency,
        status=DeadlineStatus.ACTIVE,
        governing_rule_id=rule.rule_id,
        evidence_id=ev_id,
    )

    return deadline, evidence


def _check_conditions(
    rule: PolicyRule,
    booking: Booking,
    effect: CascadeEffect,
) -> bool:
    """Check whether a policy rule's conditions are met for this booking/effect."""
    for condition in rule.conditions:
        field = condition.field
        op = condition.operator
        expected = condition.value

        # Get the actual value
        actual = _get_field_value(field, booking, effect)
        if actual is None:
            return False

        # Evaluate condition
        if op == "eq" and actual != expected:
            return False
        if op == "ne" and actual == expected:
            return False
        if op == "gt" and not (actual > expected):
            return False
        if op == "lt" and not (actual < expected):
            return False
        if op == "gte" and not (actual >= expected):
            return False
        if op == "lte" and not (actual <= expected):
            return False
        if op == "in" and actual not in expected:
            return False

    return True


def _get_field_value(field: str, booking: Booking, effect: CascadeEffect):
    """Extract a field value from booking or effect for condition evaluation."""
    if field == "booking_type":
        return booking.type.value
    if field == "booking_status":
        return effect.new_status.value
    if field == "delay_minutes":
        # For the disrupted booking, this would come from the disruption object
        # For now, extract from slack if available
        if effect.slack_minutes is not None:
            return abs(effect.slack_minutes)
        return None
    return None


def _calculate_expiry(
    rule: PolicyRule,
    booking: Booking,
    disruption_time: datetime,
) -> datetime:
    """
    Calculate the deadline expiry time.

    This uses deterministic rules based on the rule type.
    No AI/ML involved.
    """
    if rule.rule_id == "RAIL_TDR_MISSED":
        # TDR filing: use a conservative demo window of 3 hours from disruption detection
        # NOTE: Actual TDR filing windows depend on specific Railway rules.
        # This is a conservative demo estimate.
        return disruption_time + timedelta(hours=3)

    if rule.rule_id == "RAIL_TDR_WINDOW":
        # TDR filing window — same as above
        return disruption_time + timedelta(hours=3)

    if rule.rule_id == "DGCA_DELAY_2HR":
        # DGCA delay facilities — available during the delay period
        return booking.actual_departure or booking.scheduled_departure

    if rule.rule_id == "DGCA_DELAY_COMPENSATION":
        # Compensation claim — typically can be filed within a reasonable period
        # Using 30 days as a conservative demo estimate
        return disruption_time + timedelta(days=30)

    if rule.rule_id == "HOTEL_FREE_CANCEL":
        # Free cancellation window from booking metadata
        hours_before = booking.metadata.get("free_cancellation_hours_before", 6)
        check_in_time = booking.scheduled_departure  # check-in time
        return check_in_time - timedelta(hours=hours_before)

    if rule.rule_id == "ATTRACTION_NOSHOW":
        # Entry window end
        return booking.scheduled_arrival  # entry window end

    # Default: 24 hours from disruption
    return disruption_time + timedelta(hours=24)


def _calculate_value_at_stake(
    rule: PolicyRule,
    booking: Booking,
) -> float | None:
    """
    Calculate the monetary value at stake for this deadline.

    Only returns a value when it can be deterministically calculated.
    Returns None for amounts that depend on unverified rules.
    """
    if rule.rule_id in ("RAIL_TDR_MISSED", "RAIL_TDR_WINDOW"):
        # The booking price is the maximum at stake
        return booking.price

    if rule.rule_id == "HOTEL_FREE_CANCEL":
        return booking.price

    if rule.rule_id == "ATTRACTION_NOSHOW":
        return booking.price

    if rule.rule_id in ("DGCA_DELAY_2HR", "DGCA_DELAY_COMPENSATION"):
        # Compensation amount depends on specific DGCA norms
        # We don't fabricate an amount
        return None

    return None
