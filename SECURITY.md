# Security reporting

Report suspected credentials or security problems privately to the repository
maintainer. Once the public repository exists, use GitHub's private vulnerability
reporting if enabled. Do not post credentials, database dumps or private account
screenshots in issues, pull requests or chat.

Keep local state/secrets under ignored `.local/`. Runtime credentials will be
generated locally; no production credentials belong in GitHub or Terraform state.
The public gateway will expose application routes only. Database, metrics and
administrative tools remain private. Do not use intentionally vulnerable releases
to demonstrate a security gate; use clearly fake isolated fixtures.

Required release security gates are specified in docs/IMPLEMENTATION_PLAN.md.
Their implementation/verification is recorded by phase, not assumed from this file.
