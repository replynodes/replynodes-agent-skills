# Release checklist

This branch prepares package version `v2.0.1` from `VERSION`.

## v2.0.1 release notes

- Adds the focused `url-to-markdown` OpenClaw skill.
- Documents the free read-only endpoint at `https://md.replynodes.com`.
- Links the canonical implementation repository at
  `https://github.com/replynodes/replynodes-markdown`.

## v2.0.0 release notes

- Replaces the old provider-specific publishing workflow with one ReplyNodes
  research umbrella skill.
- Routes agents across the live 51-tool production MCP surface.
- Adds progressive-disclosure capability and multi-source workflow references.
- Adds the skills.sh install command and official badge.
- Documents Bearer API-key storage and read-only public-data boundaries.

Before publishing a new version, a maintainer must:

1. Update `VERSION` to a SemVer value and update release notes.
2. Review `SKILL.md`, `README.md`, `PROVENANCE.md`, `LICENSE`, and `SECURITY.md`.
3. Run `bash scripts/validate-package.sh` and `bash tests/test-package.sh`.
4. Run the current Agent Skills validator against a directory named `replynodes`.
5. Confirm the live MCP `initialize` and `tools/list` contract before changing
   capability references.
6. Confirm the tree contains no credentials, provider tokens, generated archives,
   or unrelated files.
7. Commit and push the reviewed release, then create a matching annotated tag
   only after the branch is merged.

The skill has no runtime dependency manifest. If one is introduced, commit its
lockfile and require a successful high-severity vulnerability audit before
release.
