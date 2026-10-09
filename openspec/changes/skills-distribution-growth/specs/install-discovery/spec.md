# Install and discovery contract

## ADDED Requirements

### Requirement: Canonical acquisition commands are explicit
The repository MUST document exactly one umbrella acquisition command and a direct focused-directory acquisition command for each priority skill. The documentation MUST identify the canonical GitHub source, the focused Skills.sh page when present, and the fact that external indexes may lag.

#### Scenario: Umbrella install
- **WHEN** a user runs `npx --yes skills add replynodes/replynodes-agent-skills` in an isolated project
- **THEN** the documentation says the umbrella is the canonical all-skills path
- **AND** the user is not directed to a duplicate marketplace repository

#### Scenario: Focused install
- **WHEN** a user wants `company-research`, `url-to-markdown`, or `app-store-api`
- **THEN** the documentation provides the direct `tree/main/skills/<slug>` command
- **AND** the command preserves the literal canonical slug and source repository

#### Scenario: Nested-discovery compatibility
- **WHEN** the CLI is probed with a repository-plus-`--skill` form
- **THEN** the result is recorded as compatibility evidence only
- **AND** the primary CTA is not changed to a command that the current CLI cannot prove

### Requirement: Clean-install evidence is honest
A clean-install record MUST include CLI version, isolated HOME/workdir, command, source SHA, installed path/content hash on success, or the exact failure and host blocker on failure.

#### Scenario: Installation blocked by host
- **WHEN** installation fails with `ENOSPC`, network failure, or an upstream index error
- **THEN** the report records the literal error and marks the gate blocked
- **AND** it does not claim installation succeeded

### Requirement: Metadata is task-oriented and bounded
Priority skill metadata MUST use truthful task language, bounded keywords, canonical slugs, and read-only/keyless-first claims only where supported by live evidence.

#### Scenario: Legacy external slug
- **WHEN** Skills.sh or ClawHub renders a legacy alias
- **THEN** repository docs point to the canonical source/slug and classify the alias as external drift
- **AND** no duplicate listing or invented version is created
