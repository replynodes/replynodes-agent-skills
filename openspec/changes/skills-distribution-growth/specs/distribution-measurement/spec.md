# Distribution measurement

## ADDED Requirements

### Requirement: Discovery baseline is reproducible
The repository MUST define a 30-query discovery baseline with exact query text, UTC timestamp, target slug, visibility/rank when observable, competitors, and evidence URL.

#### Scenario: Unranked public search
- **WHEN** the search response does not expose a ranked payload
- **THEN** the result is recorded as `not observable`
- **AND** no rank or negative discovery claim is inferred

### Requirement: External and product metrics are separated
Daily reporting MUST keep registry install/download counters separate from GitHub traffic, downstream API callers, API-key conversion, and two-day retention.

#### Scenario: External counter readback
- **WHEN** a registry page exposes an install count
- **THEN** it is recorded as an external display signal with timestamp and URL
- **AND** it is not labeled as a genuine user or retained caller
