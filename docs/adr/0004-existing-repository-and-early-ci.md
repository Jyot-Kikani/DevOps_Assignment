# ADR 0004: Existing repository and early CI

Accepted by explicit user instructions on 2026-10-20.

Use only `Jyot-Kikani/DevOps_Assignment`, preserving its existing origin, contents
and history. Do not create a separate `stellar-atlas` repository. Stellar Atlas
remains the application name; namespaces, cluster and image prefixes keep that name.
Release source repository, signer identity, data-release URLs and Argo Git source
must use `DevOps_Assignment`.

The repository was initially private during early CI. Later on 2026-10-20 the
user explicitly made this same repository public; live API verification confirmed
that change. Public source access is now enabled. Standard hosted runners are
free for public repositories; retain reviewed zero-paid-usage hard stops and
bounded artifact/cache use. Never purchase credits or change budgets for a run.

Main protection was then applied and read back: PR required, branch up to date,
`ci / quality` and `ci / security` required from the observed GitHub Actions app,
admins included, force pushes/deletion disabled, conversations resolved. Required
human approval count is zero; code-owner and last-push approvals are not mandatory
for this solo project. Normal development must use branches/PRs. Data/image
publication and full P15 enforcement demonstrations remain later gates.

Bring basic GitHub CI forward to after P03/before P04: existing tests, schema/type
drift, frontend lint/type/build and secret/exclusion checks on pushes and PRs.
Use pinned actions, frozen dependencies, read-only permissions, standard Ubuntu,
bounded runs and no artifact/cache upload initially. Prove a real GitHub run.
P10/P15 expand these checks; deployment/GitOps/public access keep their later phases.

The sealed P03 dataset lock contains the original planned `stellar-atlas` URL
template. Preserve that historical metadata and all archive/notice bytes.
The publisher now accepts only `<owner>/DevOps_Assignment` and writes a separate
resolved lock from the actual verified URL in P15. A repository rename is not a
scientific transformation and does not justify silently rewriting a frozen snapshot.

This amendment supersedes older P00/P01 reports and examples about creating a new
repository; those reports remain historical evidence. It does not complete P04–P07,
P10/P15 security gates, deployment, image signing, data publication or public access.
