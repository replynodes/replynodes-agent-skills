# Install and discovery reliability

## ADDED Requirements

### Requirement: Canonical install paths are explicit
The repository MUST document one canonical umbrella install and one focused install for each priority skill, including the required nested-discovery flag and a truthful explanation of bare-command limitations.

#### Scenario: Clean focused install
- **WHEN** a user runs the documented focused command in a fresh HOME and empty repository
- **THEN** the requested skill is installed from the canonical GitHub repository without credentials
- **AND** the documentation identifies the installed path and source repository

#### Scenario: Clean umbrella install
- **WHEN** a user runs the documented umbrella command in a fresh HOME
- **THEN** the root `replynodes` skill is discovered and installed
- **AND** the command does not depend on a registry duplicate

### Requirement: Canonical metadata is task-oriented
Priority skill metadata MUST use truthful user-task language, bounded keywords, canonical slugs, and a read-only/keyless-first claim where live evidence supports it.

#### Scenario: Legacy slug
- **WHEN** a registry still renders a legacy slug
- **THEN** repository documentation points to the canonical slug and records the registry discrepancy
- **AND** no duplicate listing is created to bypass the discrepancy
