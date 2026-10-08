# Company research distribution and measurement

This record separates canonical-repository work from marketplace actions that
require an external index, publisher account, or marketplace owner.

## Source of truth

- Canonical repository: `https://github.com/replynodes/replynodes-agent-skills`
- Canonical skill path: `skills/company-research/SKILL.md`
- Canonical taxonomy: `skills.sh.json` (`company-research` is in the Research
  grouping)
- Owned attribution entry:
  `https://replynodes.com/?skill=company-research&campaign=company-research`
- Discovery baseline: `references/phase-1-discovery-baseline-2026-10-04.md`,
  re-run 2026-10-08 in `references/phase-1-discovery-baseline-2026-10-08.md`.
- No marketplace-specific copy or fork is part of this repository.

The source repository, the checked-in skill, and the taxonomy above are the
only canonical distribution artifacts. Marketplace pages must be read back
before they are described as current.

## Install readback

Verified 2026-10-08 UTC with the current official `skills` CLI (`1.7.0`) in a
clean temporary `HOME` and working directory:

| Command | Result | Disposition |
| --- | --- | --- |
| `npx skills add https://github.com/replynodes/replynodes-agent-skills/tree/main/skills/company-research` | Exit 0: installs the focused `company-research` skill from the canonical repository. | **Primary CTA.** |
| `npx skills add replynodes/replynodes-agent-skills` | Exit 0: installs the `replynodes` umbrella (root skill plus nested focused skills). | **Umbrella install.** |
| `npx skills add https://github.com/replynodes/replynodes-agent-skills --skill company-research` | Exit 1: the clone exposes only the root `replynodes` skill and reports no matching `company-research` skill. | **Compatibility limitation, not the CTA.** |

The focused directory command is the documented install in `README.md` and
`skills/company-research/SKILL.md`; the same `.../tree/main/skills/<slug>` form
was verified for `url-to-markdown` and `brand-kit`. Removing the root umbrella
skill or copying `company-research` into a second top-level location would
create a fork or break the canonical `replynodes` install, so this repository
does not do that. The repository-plus-`--skill` form remains a documented
compatibility limitation until upstream CLI behavior changes; it is not the
primary CTA.

## Public marketplace readback

These observations are external state, not repository changes:

- `https://www.skills.sh/replynodes/replynodes-agent-skills/company-research`
  returned HTTP 200 and rendered the `company-research` name and company brief
  workflow. The page is a generated index view; it does not expose a canonical
  source commit or a byte-identity hash. Reindex timing and any stale rendered
  copy are owned by skills.sh.
- `https://clawhub.ai/replynodes-ai/skills/company-research` returned HTTP 200
  and reports latest version `1.0.1`. The public API readback at
  `https://clawhub.ai/api/v1/skills/company-research?owner=replynodes-ai`
  reports no source commit in its metadata.
- On the same readback, the UTF-8 SHA-256 of the public API's `skill.description`
  was
  `6153bbb305c3301d231d37aa397bab997e72d092650dbb8ff4986369aef88aa5`.
  The canonical `skills/company-research/SKILL.md` at the audited source head
  had SHA-256
  `756037b6aec7855120fce64114fba07f1a2b064319d14eb7f5f3c611e981150f`.
  These are different artifacts; this repository does not claim the ClawHub
  listing is canonical.

No ClawHub upload, marketplace fork, credential use, or source-commit claim is
made by this change. Updating ClawHub requires the authenticated owner path and
must be followed by a fresh public version, content, and moderation/readback.

## Measurement plan

Status: **PENDING** until a real two-day window exists.

Use the existing attribution and PostHog contracts from the related measurement
work; do not add an event, data store, dashboard, backend endpoint, or new
analytics channel for this skill.

- **Primary metric:** distinct company-research callers active on at least two
  separate UTC calendar days.
- **Report with the primary metric:** first callers, total callers, requests per
  caller, cross-capability usage, API-key creation after usage, and later use of
  sibling skills such as `competitor-research`.
- **Attribution:** preserve `skill=company-research` and
  `campaign=company-research` from the owned entry. Marketplace install/listing
  counters are external discovery signals, not retention or genuine-user
  measurements.
- **Exclusion:** owner-IP and internal validation traffic are excluded. Local
  install checks must set `DISABLE_TELEMETRY=1` where telemetry could otherwise
  be emitted.
- **Window:** report UTC dates and keep the metric `PENDING` until the second
  eligible calendar day has completed; do not infer retention from a one-day
  count.

## Maintainer readback after merge

Run all checks against the exact merged commit, then record the resulting commit
SHA alongside the outputs:

```sh
bash scripts/validate-package.sh
bash tests/test-package.sh
bash tests/test-distribution.sh

# Internal/local discovery only; suppress CLI telemetry.
INSTALL_INTERNAL_SKILLS=1 DISABLE_TELEMETRY=1 \
  npx --yes skills@1.7.0 add . --list --full-depth

# Public focused install (primary CTA); clean HOME.
HOME="$(mktemp -d)" npx --yes skills@1.7.0 add \
  https://github.com/replynodes/replynodes-agent-skills/tree/main/skills/company-research

# Public umbrella install.
HOME="$(mktemp -d)" npx --yes skills@1.7.0 add \
  replynodes/replynodes-agent-skills
```

Then read back the canonical GitHub file, the skills.sh page, and the ClawHub
page/API. A successful push or upload without public readback is not completion.
