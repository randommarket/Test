# QA Engineer Brief

## Key Decisions
- Unit tests for finance calculations.
- Golden-file checks for Excel exports.

## Risks
- Drift in Excel format → mitigated via sheet-name assertions.

## Deliverables
- MVP: pytest suite for core engine and exports.

## Acceptance Criteria
- CI passes with coverage on calc engine.
