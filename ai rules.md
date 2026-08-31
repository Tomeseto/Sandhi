# SANDHI — AI Rules

## Foundational Principle

> **"The model explains. The code decides."**

AI output is **advisory and untrusted** until validated by deterministic code.

## Where AI Is ALLOWED

### 1. Policy Document Extraction (Offline Ingestion)
- Extracting structured fields from policy PDFs/documents during a preprocessing step
- Output must be reviewed and validated before entering the rule corpus
- Extracted rules must be stored as deterministic, machine-readable policy objects

### 2. Summarization
- Converting already-computed, deterministic results into natural language
- Summarizing cascade impact for display
- The underlying data must come from deterministic computation, not AI generation

### 3. Natural Language Explanation
- Explaining why a booking became infeasible (from deterministic graph data)
- Explaining a deadline in plain language (from deterministic deadline objects)
- Explaining an entitlement (from deterministic rule evaluation)

### 4. Draft Complaint/TDR Generation
- Generating a draft complaint letter from deterministic structured data
- All facts in the complaint must come from the deterministic engine
- The draft must be clearly marked as a draft requiring traveller review

## Where AI Is FORBIDDEN

### 1. Legal Decision Making
AI must **never** decide:
- Whether a traveller is legally entitled to compensation
- Which legal clause applies to a situation
- Whether a claim is valid under law

### 2. Entitlement Calculation
AI must **never** compute:
- Refund amounts
- Compensation amounts
- Penalty amounts
- Any monetary entitlement

### 3. Monetary Calculations
AI must **never**:
- Calculate prices
- Calculate costs
- Calculate savings
- Convert currencies
- Estimate financial impact

### 4. Deadline Calculations
AI must **never**:
- Determine when a deadline starts
- Determine when a deadline expires
- Calculate time remaining
- Determine deadline status

### 5. Graph Propagation
AI must **never**:
- Decide whether a disruption propagates to a downstream booking
- Determine booking feasibility
- Calculate slack time
- Determine connection viability

### 6. Feasibility Decisions
AI must **never**:
- Decide whether a recovery option is feasible
- Determine whether temporal constraints are satisfied
- Override deterministic feasibility checks

### 7. Fabrication (Absolute Prohibition)
AI must **never**:
- Fabricate legal clauses or rule references
- Fabricate source documents
- Fabricate prices, schedules, or statuses
- Fabricate API responses
- Fabricate entitlement amounts
- Convert estimates into facts
- Present AI-generated content as authoritative fact

## Validation Rule

When AI is used in any permitted capacity:

1. **Isolate**: AI logic must be behind an adapter/interface
2. **Timeout**: AI calls must have timeout and error handling
3. **Validate**: AI output must be validated before entering the decision engine
4. **Log**: AI usage must be logged with provenance
5. **Fallback**: A deterministic fallback must exist
6. **Override prevention**: AI output must never override deterministic rules

## Provenance Requirement

Any value derived from or influenced by AI must carry:

```
provenance_type: MODEL_PREDICTION or ESTIMATE
source: "<model identifier>"
confidence: <0.0 to 1.0>
validated: <true/false>
```

## No-AI Operation

The SANDHI application **must be fully functional without any AI/LLM API key**.

All core functionality — graph propagation, deadline computation, entitlement calculation, feasibility checking, recovery ranking — operates on deterministic code.

AI is an optional enhancement layer, not a dependency.

## Summary

| Function | AI Allowed? | Decision Maker |
|----------|-------------|----------------|
| Disruption detection | ❌ | Deterministic code |
| Graph propagation | ❌ | Deterministic code |
| Feasibility calculation | ❌ | Deterministic code |
| Deadline computation | ❌ | Deterministic code |
| Entitlement calculation | ❌ | Deterministic code |
| Recovery ranking | ❌ | Deterministic code |
| Monetary calculation | ❌ | Deterministic code |
| Policy extraction (offline) | ✅ | AI + human validation |
| Result summarization | ✅ | AI (from deterministic data) |
| Complaint drafting | ✅ | AI (from deterministic data) |
| Natural language explanation | ✅ | AI (from deterministic data) |
