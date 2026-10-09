# Distribution measurement contract

## ADDED Requirements

### Requirement: Discovery baseline is reproducible
The repository MUST define exactly 30 realistic task-language queries with target slug, UTC timestamp, method, visibility, rank when observable, competitors, and evidence URL fields.

#### Scenario: Unranked response
- **WHEN** a public search response has no ranked payload
- **THEN** rank is recorded as `not observable`
- **AND** the report does not infer a negative discovery result from missing rank

#### Scenario: Direct brand query
- **WHEN** `replynodes` is searched directly
- **THEN** the evidence records the returned canonical and legacy listings separately
- **AND** it does not convert aggregate install counts into user identity or retention

### Requirement: External and product metrics remain separate
Daily reporting MUST distinguish registry display counters from GitHub traffic, downstream callers, API-key conversion, sibling-skill adoption, and two-UTC-day retention.

#### Scenario: External counter readback
- **WHEN** Skills.sh or ClawHub exposes an install/download counter
- **THEN** the value is recorded with exact URL, UTC timestamp, and source surface
- **AND** it is labeled an external display signal, never a genuine-user or retained-caller count

#### Scenario: Attribution unavailable
- **WHEN** a registry does not expose source/referrer/identity or returns missing provenance
- **THEN** the field is recorded as `unavailable`
- **AND** the report does not invent causal attribution

### Requirement: Owner actions are separate from source delivery
The plan MUST list Skills.sh indexing correction and ClawHub owner-scoped reconciliation as external actions, not as completed repository work.

#### Scenario: Source merged but index stale
- **WHEN** the source PR is merged while a public registry still renders stale content
- **THEN** the status remains externally blocked until public readback changes
- **AND** no duplicate slug, forced version, or synthetic install is used as a workaround
