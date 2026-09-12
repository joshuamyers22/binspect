# Production-template alignment

Date: 2026-09-12. Applies to the [binspect project plan](../binspect-plan.md).
This records a direct comparison with the local production project template,
not retrospective evidence that the first plan rewrite used it.

## Scope and authority

Reviewed template checkout: `d59f3e661a1fa3456505cf36f91b51f4a1c873ac`.
Its README and source-material index had pre-existing local edits; those files
were read as context and left untouched. The normative standard, defaults,
blueprint, Python guide, checklists, and templates cited below were unchanged
relative to that revision. Converted books and generated examples are not policy.

binspect baseline: `59c6a39`, package 0.1.1. The existing plan rewrite and
adversarial-review document were already uncommitted on
`docs/production-roadmap-review`; this alignment builds on them.

Applicability: an existing Python statistical/visualization **library**. Apply the
repository standard, Python guide, relevant quantitative evidence requirements,
and review/release records. Do not run the project generator over the repository
or copy the data/quant archetype's application, dataset, service, or licensing
defaults wholesale.

Authority follows the template: explicit product constraints and reviewed ADRs
resolve default choices; executable checks establish conformance. This document
and the agent drafting it cannot certify security, statistical validity, or a
release. Proposed exceptions remain visible for G1 review.

## Source register

All links identify the reviewed template revision rather than a moving branch.

- [Repository standard](https://github.com/joshuamyers22/production-project-template/blob/d59f3e661a1fa3456505cf36f91b51f4a1c873ac/standards/PRODUCTION_REPOSITORY_STANDARD.md): requirements, applicability, acceptance, and definition of done.
- [Engineering defaults](https://github.com/joshuamyers22/production-project-template/blob/d59f3e661a1fa3456505cf36f91b51f4a1c873ac/PERSONAL_ENGINEERING_DEFAULTS.md): overridable engine, runtime, tooling, and workflow preferences.
- [Production blueprint](https://github.com/joshuamyers22/production-project-template/blob/d59f3e661a1fa3456505cf36f91b51f4a1c873ac/docs/PRODUCTION_BLUEPRINT.md) and [Python guide](https://github.com/joshuamyers22/production-project-template/blob/d59f3e661a1fa3456505cf36f91b51f4a1c873ac/docs/PYTHON_ENGINEERING_GUIDE.md): scoped boundaries, ownership, numerical contracts, evidence, and side effects.
- [Project brief](https://github.com/joshuamyers22/production-project-template/blob/d59f3e661a1fa3456505cf36f91b51f4a1c873ac/templates/PROJECT_BRIEF.md) and [ADR](https://github.com/joshuamyers22/production-project-template/blob/d59f3e661a1fa3456505cf36f91b51f4a1c873ac/templates/ADR.md): outcomes, decisions, ownership, and verification.
- [Statistical analysis plan](https://github.com/joshuamyers22/production-project-template/blob/d59f3e661a1fa3456505cf36f91b51f4a1c873ac/templates/STATISTICAL_ANALYSIS_PLAN.md): model/sample/uncertainty design and attributable evidence.
- [Threat model](https://github.com/joshuamyers22/production-project-template/blob/d59f3e661a1fa3456505cf36f91b51f4a1c873ac/templates/THREAT_MODEL.md) and [release checklist](https://github.com/joshuamyers22/production-project-template/blob/d59f3e661a1fa3456505cf36f91b51f4a1c873ac/checklists/RELEASE_READINESS.md): controls, residual risks, evidence and approval.
- [Adversarial review](https://github.com/joshuamyers22/production-project-template/blob/d59f3e661a1fa3456505cf36f91b51f4a1c873ac/templates/ADVERSARIAL_CODE_ARCHITECTURE_REVIEW.md), [improvement plan](https://github.com/joshuamyers22/production-project-template/blob/d59f3e661a1fa3456505cf36f91b51f4a1c873ac/templates/IMPROVEMENT_PLAN.md), and [verification loop](https://github.com/joshuamyers22/production-project-template/blob/d59f3e661a1fa3456505cf36f91b51f4a1c873ac/templates/AGENTIC_VERIFICATION_LOOP.md): bounded review, acceptance, owners, stop conditions.
- [Performance experiment](https://github.com/joshuamyers22/production-project-template/blob/d59f3e661a1fa3456505cf36f91b51f4a1c873ac/templates/PERFORMANCE_EXPERIMENT.md): repeatable measurement and evidence for optimization.
- [Agent agreement](https://github.com/joshuamyers22/production-project-template/blob/d59f3e661a1fa3456505cf36f91b51f4a1c873ac/AGENTS.md): retrieve/verify, bounded memory, evidence-changing passes, and accountable review.
- [Shared release workflow](https://github.com/joshuamyers22/production-project-template/blob/d59f3e661a1fa3456505cf36f91b51f4a1c873ac/archetypes/_shared/.github/workflows/release.yml): an executable example of frozen tools, audits, and SBOM production; its event trigger is not a requirement to replace binspect's existing release route.

## Requirement-to-evidence mapping

“Partial” records existing repository evidence, not full certification. “Planned”
means acceptance criteria now exist and implementation remains open. Each open
item is accountable to the maintainer, with a specific implementer/reviewer
assigned before work and completion due at the named milestone gate.

| Template requirement | Current binspect evidence / gap | Plan coverage and due gate |
|---|---|---|
| Standard §1: location, origin, generated-state hygiene | Correct project location/origin; .gitignore covers caches/builds. No new runtime code/artifacts added by alignment. | G1/P3 verify tracked-file and secret hygiene before qualification. |
| §2: project agreement, memory, bounded notes, review records | No tracked AGENTS, project memory, or adapted release checklist at baseline. | G1 before broader architecture/contract decisions; populate from evidence rather than copy blank files. |
| §3: manifest, resolver lock, frozen dependency updates | Metadata/uv.lock/frozen CI present; released build tools are installed unpinned. | P2/R1 lock runtime, installer/build tools and isolated build resolution; P3 reviews upgrades. |
| §3 + quantitative defaults: engines and method plan | pandas/NumPy/SciPy differ from Polars/Statsmodels defaults; no method analysis-plan artifact. | Proposed ADR reviewed in G1; C3 method specification and independent references; A2 evidence export. |
| §4: secrets/configuration | No configured service; ignoring caches alone does not establish secret hygiene. | G2/P3 prevent sensitive data in errors, source/history, logs and artifacts; service environment configuration N/A. |
| §5: C++/latency systems | No C++ source or real-time deployment. | N/A for toolchains/sanitizers/queue deadlines; applicable bounded arrays and reproducible measurement retained in P1. |
| §6: Docker | In-process library, no deployed app/CLI. | Intentional omission in brief/ADR; revisit if deployment model changes. |
| §7: honest local commands | Makefile supplies sync/lint/type/test/build/check. No audit gate. | G1/D1 document existing interface; P3 adds a real supply-chain gate and integrates it into qualification. |
| §8: deterministic unit, integration, artifact tests | Existing 160-test baseline; no pinned external reference gate or clean artifact install qualification. | C1/C3 references, A1–A3 contracts, R1 artifact tests. Unit tests stay network-independent. |
| §9: CI triggers, least privilege, immutable actions | PR/main CI and scoped permissions present. PyPI publish action uses mutable `release/v1`. | P3 pins every action and adds secret/dependency/license checks; R1 verifies actual governance configuration. |
| §10: traceable CI releases | Trusted Publishing route configured in YAML; no SBOM/provenance/checksum evidence in workflow. | P3/R1/R2 locked builds and identity/evidence bundle; R3 recovery. Verify deployed settings separately. |
| §11: README, reproducibility, security, ownership, license | Core documents exist but contain stale/overbroad statements; MIT already established. | D1/G1/G2 update them and preserve license. Brief and proposed ADR now populated. |
| §12: observability and improvement | User-facing warnings/errors and CI exist; no owned trend-review record. | R3 monthly/release triage and evidence-based improvement loop. Service telemetry/health/backup N/A. |
| §§13–14: acceptance and final definition of done | Existing CI cannot close new correctness/readiness gaps. | R2 evidence checklist with exact revision, audit/artifact results, approver/date, and owned residual risks; no unchecked gate is reported passed. |
| Statistical plan: design, dependence, uncertainty, selection/final assessment | Mathematical contracts improved in first rewrite; coverage assessment still unperformed. | C3 predeclares method/Monte Carlo tolerances and locks final-assessment cases; A2 binds results to plan/data/software identity. |
| Blueprint/Python guide: architecture and ownership | Core/result/viz boundaries present; mutable arrays and grouped-coordinate defect reproduced. | C2/A1–A3, explicit named pandas boundaries in ADR, import-time side-effect checks in G2. |
| Verification/review/improvement templates | Review has findings/reproductions but did not declare original iteration limits. Do not backdate them. | Plan §5 requires bounded contracts for future material work and milestone adversarial review; final document verification below is scoped separately. |
| Performance-experiment template | No measured production workload envelope. | P1 repeated distributions, warm/cold boundaries, baseline variance, correctness evidence, and rollback triggers. |

## Applicability and exceptions

The [project brief](../PROJECT_BRIEF.md) and
[proposed ADR](decisions/0001-existing-library-baseline.md) record these choices:

- **Documented departures requiring G1 disposition:** existing pandas
  input/control/table boundaries; conditional retention of NumPy/SciPy
  estimators with locked Statsmodels validation; strict mypy; current tested
  runtime range. These are compatibility choices, not waivers of correctness.
- **Preserved owner decision:** existing MIT licensing. Template generation's
  proprietary default does not supersede it.
- **N/A for this library:** Docker/runtime dependency exports for deployment,
  service authentication/tenancy/health checks, service-level uptime/RPO/RTO,
  queues, retries across hosted boundaries, telemetry shipping/storage, and
  database/dataset publication migrations. Input/privacy/capacity checks and
  export-schema compatibility still apply.
- **N/A to current statistical scope:** Bayesian priors/posterior samplers,
  financial utility/trading controls, point-in-time prediction folds, and a
  hosted immutable dataset platform. Specify dependence, selection, estimator
  uncertainty, units, missingness and reference evidence for supported methods.
  If future scope activates these requirements, update the brief/ADR first.

These omissions are scoped product decisions. There is no requirement here to add
an unused telemetry schema or switch dataframe engines solely to resemble the
generator's directory tree.

## Final document-verification contract

Defined for the final alignment checks, without claiming it governed the earlier
adversarial investigation.

- Objective: every applicable template requirement maps to an owned acceptance
  gate; exceptions are explicit; known binspect findings remain open.
- Invariants: no runtime, license, remote configuration, or unrelated template
  changes; no invented approval, passing check, benchmark, or capacity guarantee.
- Scope/ceiling: at most two final correction/check passes and 15 minutes;
  local documentation validation only, no simulation or network audit spend.
- Pass: local document links and Python example syntax valid, no whitespace
  errors, no broken task references, and all applicable standard sections mapped.
- Stop: pass once; otherwise correct identified failures and rerun affected
  checks. Stop at the ceiling and report any unresolved issue. Domain validity
  and policy acceptance stay with the named future gates.
- Independence: same assistant authored and checked these documents. No independent
  review or release approval is claimed.

## Verification result

Final local checks passed on 2026-09-12: all five changed/added documents have
valid relative links, balanced code fences, parseable Python examples, portable
paths, and clean whitespace. All 23 implementation/deferred task IDs are unique;
the mapping covers standard sections 1–14. Review also made recovery/runbook
readiness an explicit prerequisite to publication and included M0 in the release
dependencies.

Earlier numerical test results remain historical evidence in the
[adversarial review](project-plan-review.md); they are not a new conformance run.
Full software/supply-chain/release gates were not rerun for this documentation-only
alignment. Stop condition: document rubric passed; repository implementation,
statistical validation, and accountable policy/release decisions remain open.
