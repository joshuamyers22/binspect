# A3 — compatibility policy

- Owner: Josh Myers; implementer: Codex; maintainer review pending.
- Date / baseline: 2026-09-12 / `9a6db9f`, stacked on A2 PR #17.
- Task: A3 in [the production plan](../binspect-plan.md).
- Status: documented and locally verified on `docs/compatibility-policy`;
  maintainer policy acceptance/integration pending.

## Contract before iteration

Inventory the actual public functions, result attributes, plot layers, defaults,
warnings and exceptions. Document supported option combinations and executable
migrations from 0.1.1. Allocate the pending changes to a proposed minor 0.2.0
release by compatibility impact, without changing the package version or publishing.
Preserve the user-directed Polars defaults and explicit pandas conversion.

Scope is documentation. Numerical methods, signatures, exports, dependency locks,
CI and runtime behavior remain the baseline. Existing plot tests protect caller
axes identity and scoped rcParams, including theme-context exceptions. Input,
ownership, inference and adapter tests provide the remaining behavioral evidence.
Required checks: runtime signature/attribute inventory comparison, executed migration
examples, focused existing contract/plot tests, local documentation links, formatting
and final diff review. A full software gate is required only if source/workflow
changes become necessary; prior A2 results do not count as an A3 rerun.

Blocking High findings: undocumented incompatible output/default behavior, invented
support or statistical acceptance, or an axes/theme regression. Missing migration
coverage or inaccurate signatures are Medium and must be resolved. Maximum three
evidence-changing passes / 60 minutes / local compute only. Stop when the contract
passes; at the ceiling report unresolved findings and the owner's next action.
Do not relax tests, run reserved assessment seeds, merge or release. Maintainer
policy acceptance and independent statistical review remain separate.

## Evidence ledger

| Pass | Changed evidence | Check / disposition |
|---|---|---|
| Baseline | Inspected runtime signatures, dataclass fields, public exports and existing plot regressions | Confirmed Polars result types, explicit pandas conversions, fixed draw order, axes identity and scoped-theme contracts; documentation inventory pending. |
| 1 | Proposed policy, actual API inventory, option matrix, four sequential migration examples and per-change release allocation | Covers all top-level/viz exports and public result fields/methods, including nested values. Records existing exported core primitives separately without granting them the public inference contract. Polars/pandas migration, positional alignment, array ownership, adjustment/DPI restrictions, grouped interval IDs, verdict/schema changes and function-target choice are explicit. |
| 2 | Executed examples and existing behavioral safety net | All four examples pass, including real binsreg DPI with `approximate_pointwise` status and no issues. 197 existing tests pass across plot/layer, Polars, ownership, evidence, adjusted/grouped inference, diagnostic policy and adapter boundary suites. One expected adjusted-inference warning remains visible in a grouped failure test. |
| 3 | Runtime inventory equality, supplementary rendering checks, source/doc consistency and final diff review | Inventory matches inspected exports, signatures/defaults, dataclass fields, properties and constants. All nine standalone layers return the supplied Axes; caller figure size is preserved; a rendering exception restores rcParams. Changed Markdown local link targets, code fences, whitespace/newlines and `git diff --check` pass. Corrected stale README cluster/SD/deviation statements and removed unqualified accessibility claims pending D2. |

Commands used the existing locked `.venv` on macOS arm64/Python 3.12.14. The
inventory was produced and checked with `inspect.signature`, `dataclasses.fields`,
class properties/methods and module `__all__` values, rather than inferred signatures.
Disposable inspection code lives in ignored `.work/a3_inventory.py`; the committed
[inventory](API_INVENTORY.md) identifies its source modules and baseline. D1 will
add the generated API site and executable documentation gate.

The focused test command was:

```sh
.venv/bin/pytest -q tests/test_plot.py tests/test_layer_policy.py \
  tests/test_polars_contract.py tests/test_result_ownership.py \
  tests/test_evidence_export.py tests/test_adjusted_inference_boundary.py \
  tests/test_grouped_intervals.py tests/test_diagnostic_policy.py \
  tests/test_binsreg_boundary.py
```

The four Python blocks in [the migration guide](COMPATIBILITY.md) were executed
sequentially with `MPLBACKEND=Agg`, using the installed pandas and DPI extras.
No source, workflow, test expectations, lock or package-version changes were made.
Full `make check`, coverage simulations, builds and other-platform tests were not
rerun for this documentation-only slice; prior A2 evidence remains historical.
No new statistical assessment or dependency qualification is claimed.

## Review disposition

Local documentation/behavior checks have no unresolved blocking finding. The
proposed [policy](COMPATIBILITY.md) allocates pending incompatible changes to 0.2.0
and describes patch eligibility without bumping or releasing 0.1.1. Maintainer
policy acceptance/integration remains open. The branch is stacked on A2/A1, so it
must be reviewed against A2 rather than treated as a standalone main-branch change.

M2 acceptance, C3 qualified statistical review/final assessment, P2 dependency
qualification and release gates remain open. No merge, release, independent
approval or reserved-seed execution occurred. Next implementation is D1 executable
user guide and API reference; local A3 examples do not complete its site/CI criteria.
