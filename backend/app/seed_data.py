"""
SANDHI Demo Seed Data

The Mumbai → Delhi → Agra demo scenario.
All values are explicitly labelled as DEMO_FIXTURE provenance.
"""

from datetime import datetime, timedelta

from app.models import (
    Booking, BookingStatus, BookingType, Dependency, Evidence,
    PolicyRule, PolicyCondition, PolicyResult, ProvenanceType,
    RecoveryOption, Trip,
)

# Base date for demo: tomorrow
DEMO_BASE_DATE = datetime(2026, 9, 1)


def create_demo_evidence() -> list[Evidence]:
    """Create evidence records for demo fixture data."""
    now = datetime.utcnow()
    return [
        Evidence(
            id="ev_flight_schedule",
            value="Flight 6E 5312 Mumbai-Delhi",
            unit=None,
            provenance_type=ProvenanceType.DEMO_FIXTURE,
            source="Demo fixture data",
            retrieved_at=now,
            source_reference="Seeded demo itinerary",
            confidence=1.0,
            description="Flight schedule from demo fixture",
        ),
        Evidence(
            id="ev_flight_price",
            value=4500,
            unit="INR",
            provenance_type=ProvenanceType.DEMO_FIXTURE,
            source="Demo fixture data",
            retrieved_at=now,
            source_reference="Seeded demo itinerary",
            confidence=1.0,
            description="Flight ticket price (demo fixture)",
        ),
        Evidence(
            id="ev_transfer_time",
            value=55,
            unit="minutes",
            provenance_type=ProvenanceType.ESTIMATE,
            source="Typical Delhi airport to New Delhi station transfer",
            retrieved_at=now,
            source_reference="Estimated based on typical travel time",
            confidence=0.7,
            description="Airport to station transfer time estimate",
        ),
        Evidence(
            id="ev_train_schedule",
            value="Train 12002 Bhopal Shatabdi",
            unit=None,
            provenance_type=ProvenanceType.DEMO_FIXTURE,
            source="Demo fixture data",
            retrieved_at=now,
            source_reference="Seeded demo itinerary",
            confidence=1.0,
            description="Train schedule from demo fixture",
        ),
        Evidence(
            id="ev_train_price",
            value=1240,
            unit="INR",
            provenance_type=ProvenanceType.DEMO_FIXTURE,
            source="Demo fixture data",
            retrieved_at=now,
            source_reference="Seeded demo itinerary — approximate Chair Car fare",
            confidence=0.8,
            description="Train ticket price (demo fixture, approximate)",
        ),
        Evidence(
            id="ev_hotel_price",
            value=3200,
            unit="INR",
            provenance_type=ProvenanceType.DEMO_FIXTURE,
            source="Demo fixture data",
            retrieved_at=now,
            source_reference="Seeded demo itinerary",
            confidence=1.0,
            description="Hotel booking price (demo fixture)",
        ),
        Evidence(
            id="ev_hotel_policy",
            value="Free cancellation until 6 hours before check-in",
            unit=None,
            provenance_type=ProvenanceType.DEMO_FIXTURE,
            source="Demo hotel cancellation policy",
            retrieved_at=now,
            source_reference="Demo policy — typical hotel free cancellation terms",
            confidence=0.6,
            description="Hotel cancellation policy (demo fixture)",
        ),
        Evidence(
            id="ev_taj_price",
            value=550,
            unit="INR",
            provenance_type=ProvenanceType.DEMO_FIXTURE,
            source="Demo fixture data",
            retrieved_at=now,
            source_reference="Seeded demo itinerary — approximate timed entry",
            confidence=0.8,
            description="Taj Mahal timed entry price (demo fixture)",
        ),
        Evidence(
            id="ev_taj_policy",
            value="Timed entry — no refund after entry window",
            unit=None,
            provenance_type=ProvenanceType.DEMO_FIXTURE,
            source="Demo attraction policy",
            retrieved_at=now,
            source_reference="Demo policy — typical timed attraction entry terms",
            confidence=0.5,
            description="Taj entry refund policy (demo fixture)",
        ),
        Evidence(
            id="ev_rail_refund_rule",
            value="TDR filing for missed connection",
            unit=None,
            provenance_type=ProvenanceType.PUBLISHED_RULE,
            source="Indian Railway Passenger Fare Refund Rules",
            retrieved_at=now,
            source_reference="Refund rules — TDR provisions for missed connections",
            confidence=0.8,
            description="Railway TDR refund rule. Note: The specific refund amount depends on class, distance, and filing time. The rule structure is verified but exact amounts require case-by-case calculation per current tariff.",
        ),
        Evidence(
            id="ev_dgca_delay_rule",
            value="Airline obligations on flight delay",
            unit=None,
            provenance_type=ProvenanceType.PUBLISHED_RULE,
            source="DGCA CAR Section 3, Series M, Part IV",
            retrieved_at=now,
            source_reference="CAR provisions on facilities to passengers in case of delays",
            confidence=0.8,
            description="DGCA rule on airline obligations for delays. Note: Specific provisions depend on delay duration and flight distance. The rule structure is verified.",
        ),
        Evidence(
            id="ev_recovery_train_1",
            value="Alternative train Agra Superfast",
            unit=None,
            provenance_type=ProvenanceType.DEMO_FIXTURE,
            source="Demo fixture data",
            retrieved_at=now,
            source_reference="Demo recovery option",
            confidence=1.0,
            description="Alternative train option (demo fixture)",
        ),
        Evidence(
            id="ev_recovery_train_2",
            value="Alternative train Gatimaan Express",
            unit=None,
            provenance_type=ProvenanceType.DEMO_FIXTURE,
            source="Demo fixture data",
            retrieved_at=now,
            source_reference="Demo recovery option",
            confidence=1.0,
            description="Alternative train option (demo fixture)",
        ),
        Evidence(
            id="ev_recovery_train_3",
            value="Alternative late train",
            unit=None,
            provenance_type=ProvenanceType.DEMO_FIXTURE,
            source="Demo fixture data",
            retrieved_at=now,
            source_reference="Demo recovery option",
            confidence=1.0,
            description="Alternative late train option (demo fixture)",
        ),
    ]


def create_demo_trip() -> Trip:
    """Create the Mumbai → Delhi → Agra demo trip."""
    base = DEMO_BASE_DATE

    bookings = [
        Booking(
            id="bk_flight",
            type=BookingType.FLIGHT,
            provider="IndiGo",
            reference="6E 5312",
            origin="Mumbai (BOM)",
            destination="Delhi (DEL)",
            scheduled_departure=base.replace(hour=7, minute=30),
            scheduled_arrival=base.replace(hour=9, minute=40),
            price=4500,
            currency="INR",
            status=BookingStatus.CONFIRMED,
            metadata={"flight_number": "6E 5312", "terminal": "T1", "gate": "A12"},
            evidence_ids=["ev_flight_schedule", "ev_flight_price"],
        ),
        Booking(
            id="bk_transfer",
            type=BookingType.TRANSFER,
            provider="Pre-booked cab",
            reference="TRF-DEL-001",
            origin="Delhi Airport (DEL)",
            destination="New Delhi Railway Station (NDLS)",
            scheduled_departure=base.replace(hour=10, minute=0),
            scheduled_arrival=base.replace(hour=10, minute=55),
            price=600,
            currency="INR",
            status=BookingStatus.CONFIRMED,
            metadata={"vehicle_type": "sedan", "distance_km": 16},
            evidence_ids=["ev_transfer_time"],
        ),
        Booking(
            id="bk_train",
            type=BookingType.TRAIN,
            provider="Indian Railways",
            reference="12002",
            origin="New Delhi (NDLS)",
            destination="Agra Cantt (AGC)",
            scheduled_departure=base.replace(hour=12, minute=0),
            scheduled_arrival=base.replace(hour=13, minute=50),
            price=1240,
            currency="INR",
            status=BookingStatus.CONFIRMED,
            metadata={
                "train_name": "Bhopal Shatabdi",
                "train_number": "12002",
                "class": "CC",
                "coach": "C5",
                "seat": "23",
                "pnr": "2612345678",
            },
            evidence_ids=["ev_train_schedule", "ev_train_price"],
        ),
        Booking(
            id="bk_hotel",
            type=BookingType.HOTEL,
            provider="Hotel Amar Vilas (Demo)",
            reference="HTL-AGR-001",
            origin="Agra",
            destination="Agra",
            scheduled_departure=base.replace(hour=15, minute=0),  # check-in
            scheduled_arrival=base.replace(hour=15, minute=30),   # settled-in time (for graph: when guest is available for next activity)
            price=3200,
            currency="INR",
            status=BookingStatus.CONFIRMED,
            metadata={
                "hotel_name": "Hotel Amar Vilas (Demo)",
                "check_in": "15:00",
                "check_out": "11:00",
                "check_out_datetime": (base + timedelta(days=1)).replace(hour=11, minute=0).isoformat(),
                "late_check_in_cutoff": "22:00",
                "free_cancellation_hours_before": 6,
                "room_type": "Deluxe",
            },
            evidence_ids=["ev_hotel_price", "ev_hotel_policy"],
        ),
        Booking(
            id="bk_taj",
            type=BookingType.ATTRACTION,
            provider="ASI / Taj Mahal (Demo)",
            reference="TAJ-ENTRY-001",
            origin="Agra",
            destination="Agra",
            scheduled_departure=base.replace(hour=16, minute=0),  # entry window start
            scheduled_arrival=base.replace(hour=17, minute=30),   # entry window end
            price=550,
            currency="INR",
            status=BookingStatus.CONFIRMED,
            metadata={
                "attraction": "Taj Mahal",
                "entry_window_start": "16:00",
                "entry_window_end": "17:30",
                "timed_entry": True,
                "refund_policy": "No refund after entry window",
            },
            evidence_ids=["ev_taj_price", "ev_taj_policy"],
        ),
    ]

    dependencies = [
        Dependency(
            id="dep_flight_transfer",
            from_booking_id="bk_flight",
            to_booking_id="bk_transfer",
            min_transfer_minutes=15,
            transfer_location="Delhi Airport (DEL)",
            calculation_source="Minimum time to deplane and reach cab pickup",
        ),
        Dependency(
            id="dep_transfer_train",
            from_booking_id="bk_transfer",
            to_booking_id="bk_train",
            min_transfer_minutes=10,
            transfer_location="New Delhi Railway Station (NDLS)",
            calculation_source="Minimum time from cab drop to platform",
        ),
        Dependency(
            id="dep_train_hotel",
            from_booking_id="bk_train",
            to_booking_id="bk_hotel",
            min_transfer_minutes=30,
            transfer_location="Agra",
            calculation_source="Estimated time from Agra Cantt station to hotel",
        ),
        Dependency(
            id="dep_hotel_taj",
            from_booking_id="bk_hotel",
            to_booking_id="bk_taj",
            min_transfer_minutes=20,
            transfer_location="Agra",
            calculation_source="Estimated time from hotel to Taj Mahal",
        ),
    ]

    return Trip(
        id="trip_demo_mumbai_agra",
        name="Mumbai → Delhi → Agra",
        description="Business trip with Taj Mahal visit. Flight to Delhi, train to Agra, hotel stay, and timed Taj entry.",
        bookings=bookings,
        dependencies=dependencies,
    )


def create_demo_policy_rules() -> list[PolicyRule]:
    """Create policy rules for the demo scenario."""
    return [
        PolicyRule(
            rule_id="RAIL_TDR_MISSED",
            domain="railway",
            trigger="MISSED_CONNECTION",
            conditions=[
                PolicyCondition(field="booking_type", operator="eq", value="train"),
                PolicyCondition(field="booking_status", operator="in",
                                value=["infeasible", "missed"]),
            ],
            result=PolicyResult(
                entitlement_type="TDR_REFUND",
                description="TDR (Ticket Deposit Receipt) filing for refund when train is missed due to connecting service delay. The passenger may file a TDR at the originating station or online through the IRCTC portal.",
                amount_formula="Full refund of fare less clerkage charge per passenger when connecting service causes missed connection",
            ),
            source_document="Railway Passengers (Cancellation of Ticket and Refund of Fare) Rules, 2015",
            clause_reference="Rule 13: Refund on tickets when passengers miss connection due to late arrival of connecting train",
            effective_from="2015-11-12",
            effective_to=None,
            status="VERIFIED_STRUCTURE",
        ),
        PolicyRule(
            rule_id="RAIL_TDR_WINDOW",
            domain="railway",
            trigger="MISSED_CONNECTION",
            conditions=[
                PolicyCondition(field="booking_type", operator="eq", value="train"),
                PolicyCondition(field="booking_status", operator="in",
                                value=["infeasible", "missed"]),
            ],
            result=PolicyResult(
                entitlement_type="TDR_FILING_DEADLINE",
                description="TDR must be filed within the prescribed time window from the scheduled departure. Filing after the window may result in reduced or no refund.",
                amount_formula=None,
                fixed_amount=None,
            ),
            source_document="Railway Passengers (Cancellation of Ticket and Refund of Fare) Rules, 2015 & IRCTC TDR Guidelines",
            clause_reference="Rule 13(2) / Rule 21: TDR filing time limits at connecting junction or online",
            effective_from="2015-11-12",
            effective_to=None,
            status="VERIFIED_STRUCTURE",
        ),
        PolicyRule(
            rule_id="DGCA_DELAY_2HR",
            domain="aviation",
            trigger="DELAY",
            conditions=[
                PolicyCondition(field="booking_type", operator="eq", value="flight"),
                PolicyCondition(field="delay_minutes", operator="gte", value=120),
            ],
            result=PolicyResult(
                entitlement_type="DELAY_FACILITIES",
                description="For delays of 2 hours or more on domestic flights, the airline is required to provide meals and refreshments as per DGCA CAR provisions. Additional obligations apply for longer delays.",
                amount_formula=None,
            ),
            source_document="DGCA Civil Aviation Requirements Section 3 - Air Transport, Series M, Part IV",
            clause_reference="Clause 3.6.1(a): Facilities to be offered to passengers in case of flight delays (Block time <= 2.5 hrs, delay >= 2 hrs)",
            effective_from="2016-08-01",
            effective_to=None,
            status="VERIFIED_STRUCTURE",
        ),
        PolicyRule(
            rule_id="DGCA_DELAY_COMPENSATION",
            domain="aviation",
            trigger="DELAY",
            conditions=[
                PolicyCondition(field="booking_type", operator="eq", value="flight"),
                PolicyCondition(field="delay_minutes", operator="gte", value=120),
            ],
            result=PolicyResult(
                entitlement_type="DELAY_COMPENSATION_CLAIM",
                description="Passengers may be entitled to compensation for significant delays depending on delay duration, flight distance, and whether the delay was within the airline's control. Specific amounts are determined by DGCA guidelines.",
                amount_formula="Requires airline fault verification; extraordinary circumstances exempt per DGCA CAR",
            ),
            source_document="DGCA Civil Aviation Requirements Section 3 - Air Transport, Series M, Part IV",
            clause_reference="Clause 3.7 & 3.8: Compensation obligations and extraordinary circumstances exception",
            effective_from="2016-08-01",
            effective_to=None,
            status="VERIFIED_STRUCTURE",
        ),
        PolicyRule(
            rule_id="HOTEL_FREE_CANCEL",
            domain="hotel",
            trigger="CANCELLATION_WINDOW",
            conditions=[
                PolicyCondition(field="booking_type", operator="eq", value="hotel"),
            ],
            result=PolicyResult(
                entitlement_type="FREE_CANCELLATION",
                description="Free cancellation available until the cutoff time specified in the booking terms. After cutoff, cancellation charges apply.",
                amount_formula="Full refund if cancelled before cutoff; charges apply after cutoff per booking terms",
            ),
            source_document="Hotel Booking Agreement (Demo Fixture)",
            clause_reference="Section 4.1: Cancellation Policy — Free cancellation up to 6 hours prior to check-in",
            effective_from="2024-01-01",
            effective_to=None,
            status="DEMO",
        ),
        PolicyRule(
            rule_id="ATTRACTION_NOSHOW",
            domain="attraction",
            trigger="MISSED_ENTRY",
            conditions=[
                PolicyCondition(field="booking_type", operator="eq", value="attraction"),
                PolicyCondition(field="booking_status", operator="in",
                                value=["infeasible", "forfeited"]),
            ],
            result=PolicyResult(
                entitlement_type="NO_REFUND_NOSHOW",
                description="Timed entry tickets are typically non-refundable after the entry window has passed. No-show results in forfeiture.",
                amount_formula=None,
                fixed_amount=None,
            ),
            source_document="Archaeological Survey of India (ASI) E-Ticketing Terms (Demo Fixture)",
            clause_reference="Clause 7: Timed Entry & Validity — Non-refundable on slot expiry",
            effective_from="2024-01-01",
            effective_to=None,
            status="DEMO",
        ),
    ]


def create_demo_recovery_options() -> list[RecoveryOption]:
    """
    Create recovery option candidates for the demo scenario.
    These represent alternative trains from Delhi to Agra.
    Feasibility will be computed by the recovery engine.
    """
    base = DEMO_BASE_DATE
    return [
        RecoveryOption(
            id="rec_train_1",
            mode="train",
            provider="Indian Railways",
            reference="12280",
            origin="New Delhi (NDLS)",
            destination="Agra Cantt (AGC)",
            departure=base.replace(hour=15, minute=15),
            arrival=base.replace(hour=17, minute=5),
            price=890,
            currency="INR",
            source="Demo fixture",
            source_provenance=ProvenanceType.DEMO_FIXTURE,
            feasible=True,  # Will be recalculated
            score=0.0,
            evidence_ids=["ev_recovery_train_1"],
        ),
        RecoveryOption(
            id="rec_train_2",
            mode="train",
            provider="Indian Railways",
            reference="12050",
            origin="Hazrat Nizamuddin (NZM)",
            destination="Agra Cantt (AGC)",
            departure=base.replace(hour=14, minute=10),
            arrival=base.replace(hour=15, minute=50),
            price=1450,
            currency="INR",
            source="Demo fixture",
            source_provenance=ProvenanceType.DEMO_FIXTURE,
            feasible=True,  # Will be recalculated
            score=0.0,
            evidence_ids=["ev_recovery_train_2"],
        ),
        RecoveryOption(
            id="rec_train_3",
            mode="train",
            provider="Indian Railways",
            reference="12724",
            origin="New Delhi (NDLS)",
            destination="Agra Cantt (AGC)",
            departure=base.replace(hour=21, minute=40),
            arrival=base.replace(hour=23, minute=55),
            price=680,
            currency="INR",
            source="Demo fixture",
            source_provenance=ProvenanceType.DEMO_FIXTURE,
            feasible=True,  # Will be recalculated — this should be INFEASIBLE (hotel check-in)
            score=0.0,
            evidence_ids=["ev_recovery_train_3"],
        ),
    ]
