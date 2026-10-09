# Workflow examples

## ADDED Requirements

### Requirement: Examples are useful and safe
The repository MUST provide five copyable GitHub Action examples covering the priority skills and umbrella routing, using bounded read-only calls and secret-safe placeholders.

#### Scenario: Example install CTA
- **WHEN** a developer opens a workflow example
- **THEN** it names the relevant canonical skill and links to its canonical install page
- **AND** it does not run an install on every repository event or emit credentials

#### Scenario: Public route example
- **WHEN** an example uses a keyless route
- **THEN** it uses a harmless public input and documents the expected bounded response/failure behavior
- **AND** it does not imply private access or write capability
