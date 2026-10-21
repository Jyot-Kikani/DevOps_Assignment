# Stellar Atlas planning handoff

1. Read [PRD.md](PRD.md) for the product and assessment acceptance requirements.
2. Execute [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) in phase order. Its contracts and decisions are authoritative unless the user changes them.
3. Preserve `validation/` and `design/mockups/`. The existing files are feasibility evidence and visual references, not an implemented application.

The planning documents were created on 18 October 2026. No application, cluster, repository publication, account configuration, or deployment was created as part of writing them. External account values and prerequisite actions are explicitly listed in the implementation plan; they are not unspecified architecture choices.

Implementation status is tracked separately: [Batch 1 report](BATCH1_REPORT.md)
covers P01–P03, completed on 19 October 2026. It records foundation checks and
local dataset sealing; feature implementation, database and deployment phases follow.

The user authorized [early GitHub CI](EARLY_CI.md) before Batch 2 and selected the
existing `Jyot-Kikani/DevOps_Assignment` repository exclusively. Read
[ADR 0004](adr/0004-existing-repository-and-early-ci.md) before remote operations.

The [Batch 2 report](BATCH2_REPORT.md) records P04–P07 database/import/API work
and exact validation. Read its phase guides for reproducible database and HTTP
checks. The early-CI and Batch 1 documents remain historical checkpoints.
Batch 3 now implements P08–P11 local application work; read [its report](BATCH3_REPORT.md)
for exact results, local image metadata and the failed Grype threshold. Batch 4 adds
local kind Kubernetes, Terraform, deployment, monitoring and isolated restore.
Read [its report](BATCH4_REPORT.md) for actual results. Publication, GitOps and public
access are implemented in Batch 5; see the P15–P18 guides and actual Batch 5 report.

Read [ADR 0005](adr/0005-course-assignment-scope.md) before future work. It narrows checks to a practical course demonstration and supersedes older mandatory hardening language. The revised PRD and implementation plan agree with it; historical completion reports remain unchanged.

Current guides: [P08 web](P08_WEB.md), [P09 Compose](P09_COMPOSE.md), [P10 checks](P10_CHECKS.md), [P11 images](P11_RELEASE_IMAGES.md).

Batch 4 guides: [P12 platform](P12_KUBERNETES.md), [P13 deployment](P13_LOCAL_DEPLOYMENT.md),
[P14 monitoring/recovery](P14_MONITORING_RECOVERY.md).

Batch 5 guides: [P15 publication](P15_PUBLICATION.md), [P16 public access](P16_PUBLIC_DEMO.md),
[P17 GitOps](P17_GITOPS.md), [P18 update/rollback](P18_UPDATE_ROLLBACK.md).
P19 remains unstarted.
