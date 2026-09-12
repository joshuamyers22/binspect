# Bounded verification: <task>

- Owner / implementer / reviewer:
- Date / baseline commit:
- Linked plan task or improvement:
- Status: proposed / in progress / ready for review / accepted / blocked

## Contract before iteration

- Objective and observable success:
- Scope and non-goals:
- Invariants and existing safety net:
- Required checks and evidence locations:
- Blocking severities (correctness, security, compatibility, unsupported claims):
- Maximum evidence-changing passes / elapsed time / compute or monetary ceiling:
- Stop, rollback and escalation conditions:
- Acceptance authority and any independent-review requirement:

## Evidence ledger

| Pass / baseline | Changed evidence or hypothesis | Check and actual result | Disposition / next action |
|---|---|---|---|
| | | | |

Every pass must change evidence. Stop when the contract passes; at the ceiling,
report remaining failures and the next owner/action. Do not relax tolerances,
repeat self-review as independent evidence, or call unexecuted checks passed.

## Review disposition

Link the diff, actual checks, limitations and reviewer decision. Keep proposed
policy/risk acceptance separate from implementation readiness. Update durable
records and remove disposable scratch; do not retain raw sensitive evidence.
