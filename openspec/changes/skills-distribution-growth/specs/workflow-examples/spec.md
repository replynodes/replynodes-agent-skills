# Workflow examples contract

## ADDED Requirements

### Requirement: Examples are copyable and read-only
The repository MUST provide five GitHub Actions examples covering company research, URL-to-Markdown, App Store research, umbrella routing, and scheduled public research. Each example MUST use bounded public inputs and document expected failure/rate-limit behavior.

#### Scenario: Example discovery
- **WHEN** a developer opens an example
- **THEN** it names the canonical skill and links to the source repository and focused acquisition page
- **AND** it does not require a private credential merely to understand the install path

#### Scenario: Safe execution
- **WHEN** an example executes a provider request
- **THEN** it uses a harmless public target, read-only GET path, and bounded timeout/retry behavior
- **AND** it does not claim private access, publishing, mutation, or unrestricted crawling

#### Scenario: Secret safety
- **WHEN** a workflow needs optional authenticated enrichment
- **THEN** it references a GitHub secret by name without printing it
- **AND** logs and committed files contain no key, cookie, session, or bearer value

### Requirement: Examples do not manufacture acquisition telemetry
The examples MUST NOT install a skill on every repository event, loop installs, star repositories, call marketplace mutation endpoints, or submit artificial discovery traffic.

#### Scenario: Manual or scheduled use
- **WHEN** a workflow is triggered
- **THEN** it is manual or explicitly scheduled and bounded
- **AND** the workflow does not present execution as an install/download conversion
