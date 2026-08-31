# SANDHI — Solution

## Problem → Insight → Solution

### Problem

When a traveller's itinerary is disrupted, the largest loss is often not the delayed booking itself. The real loss comes from downstream bookings becoming infeasible and refund/rebooking/cancellation deadlines silently expiring.

### Insight

A multi-segment itinerary is a **temporal dependency graph**. A disruption to one node propagates through the graph, creating cascading failures. Each failure activates policy-governed deadlines. These deadlines are the real cost — not the delay.

### Solution

SANDHI treats an itinerary as a dependency graph and, when disruption occurs:

1. **Propagates** the disruption through downstream dependencies
2. **Identifies** which bookings become infeasible and when
3. **Resolves** the policies governing affected bookings
4. **Creates** a live Deadline Ledger with countdowns
5. **Calculates** applicable Indian travel entitlements using deterministic rules
6. **Finds** recovery options that are physically feasible
7. **Ranks** recovery options transparently
8. **Shows** the source, timestamp, and provenance behind every important value

## Why Dependency Modelling Matters

Consider a simple itinerary: Mumbai → Delhi (flight) → Delhi → Agra (train) → Agra (hotel) → Taj Mahal (timed entry).

Without dependency modelling, a flight delay is just a flight delay.

With dependency modelling, a 2h50m flight delay reveals:

- The airport-to-station transfer is still feasible (barely) or at risk
- The train is **missed** because updated arrival + transfer time exceeds train departure
- The hotel check-in is **at risk** because the traveller has no confirmed transport to Agra
- The Taj Mahal timed entry is **forfeited** because arrival in Agra will be after the entry window

Each of these has different policy implications, different deadlines, and different financial consequences.

## Why Deadlines Matter

Every affected booking has associated deadlines:

- **Railway TDR filing**: Must be filed within a specific window to claim a refund for a missed train
- **Hotel free cancellation**: Many hotel bookings have a free cancellation window that may still be open — but closing
- **Airline compensation**: DGCA rules specify conditions under which passengers are entitled to compensation
- **Attraction refund**: Timed entry tickets may have a no-show/refund policy with its own deadline

These deadlines are the **actual financial risk**. A missed deadline converts a recoverable loss into a permanent one.

## Deadline Ledger

The Deadline Ledger is SANDHI's core differentiator. It presents:

| Countdown | Deadline | Booking | Value at Stake | Source |
|-----------|----------|---------|----------------|--------|
| 02:47 | TDR filing window | Train 12002 | ₹1,240 | Indian Railway Refund Rules |
| 05:15 | Free cancellation | Hotel Agra | ₹3,200 | Booking policy |
| — | Entry forfeited | Taj timed entry | ₹550 | No-show policy |

Each deadline is a **live countdown** — not a static notification. The traveller can see exactly how much time remains and how much money is at stake.

## Indian Entitlement Computation

SANDHI computes entitlements using deterministic rules derived from:

- DGCA Civil Aviation Requirements (CAR Section 3, Series M, Part IV)
- Indian Railway Passenger Fare Refund Rules
- Airline Conditions of Carriage
- Hotel/attraction cancellation policies

Every computed entitlement references its source document, clause, and effective date. If a rule cannot be verified from the available policy corpus, SANDHI explicitly marks it as **unavailable** rather than fabricating an answer.

## Feasibility-Verified Recovery

Recovery options are not just alternatives — they are **feasibility-verified alternatives**.

Before recommending a recovery option, SANDHI:

1. Inserts the candidate into the itinerary graph
2. Recomputes all downstream dependencies
3. Checks whether the remaining itinerary remains feasible
4. Rejects candidates that cause new downstream failures

This means a cheaper train that arrives after hotel check-in closes is flagged as **NOT FEASIBLE**, with a clear explanation.

## Provenance

Every important number in SANDHI carries provenance:

- **REAL_OBSERVATION**: Directly observed from a live source
- **PUBLISHED_RULE**: From a verified policy document
- **HISTORICAL**: From historical data
- **ESTIMATE**: Calculated estimate, clearly labelled
- **DEMO_FIXTURE**: Demo/seed data, not live
- **CACHE**: From cached data, with retrieval timestamp

No source → no display as authoritative fact.

## Example User Journey (MVP Demo)

1. **View itinerary**: Mumbai → Delhi → Agra with flight, transfer, train, hotel, Taj entry
2. **Disruption occurs**: Flight 6E 5312 delayed by 2h50m
3. **See cascade**: Visual timeline showing which connections break and why
4. **See Deadline Ledger**: Live countdowns for TDR filing, hotel cancellation, etc.
5. **Click an entitlement**: See the source rule, clause, and calculation
6. **See recovery options**: Ranked alternatives, each feasibility-checked
7. **Understand why**: Every recommendation shows its reasoning

## MVP Scope

The MVP implements:

- One complete demo scenario (Mumbai → Delhi → Agra)
- Dependency graph construction and disruption propagation
- Deadline Ledger with live countdowns
- Indian railway and aviation entitlement rules (verified subset)
- Recovery option generation with feasibility checking
- Provenance system for all critical values
- Offline/demo mode with fixture data

## Future Scope

Beyond MVP:

- Live API integration (flight tracking, railway status)
- Multi-trip management
- Automated TDR/complaint filing
- Push notifications for approaching deadlines
- Semantic policy search across a larger corpus
- ML-based delay prediction
- Mobile application
- Multi-language support
