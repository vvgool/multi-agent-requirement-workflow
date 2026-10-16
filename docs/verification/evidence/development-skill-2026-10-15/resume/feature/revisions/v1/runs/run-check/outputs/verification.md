# Shipping fee fixture: complete feature verification

- feature_id: EVAL-resume
- requirements_revision: 1
- run_id: run-check
- Requirements: feature/requirements.md; SHA256 1f427e6d1b0791c6e34a6d051ebb050319fee2ee696927f2784954419fc87512. Synthetic fixture approval only, not human approval.
- Environment/time: local Python 3; 2026-10-15T08:32:46.965764+00:00. Each evidence JSON records actual command, cwd, time, exit code and output.

## Tested baseline

13a2b905dc7dfab066935c52f66fb8821b6385ca152d81abf64f85da64fa5215; see code-baseline.json. SHA256 of sorted compact JSON mapping of shipping.py, checkout.py and integration_check.py to their SHA256. Excludes outputs, logs, cache and manifest itself. Source hashes unchanged after checks; final-state-check.json confirms task current.

## Task and module verification

| Task/module | Method and expected | Actual | Status | Evidence |
| --- | --- | --- | --- | --- |
| M01-T1/T2/M01 | Six fee boundaries; two negatives raise ValueError | exit 0, all assertions pass | passed | evidence/M01.json |
| M02-T1/M02 | Six checkout totals; two negative exception regressions | exit 0 | passed | evidence/M02.json |
| I01 | Real shipping/checkout imports and complete function flow | exit 0 | passed | evidence/I01.json |
| I02 | Original python3 -B integration_check.py; expect exit 0 | exit 1: required integration environment offline | failed | evidence/I02.json |

All evidence applies to the baseline above.

## Acceptance verification

| Acceptance | Module/implementation | Flow | Expected and actual | Status | Evidence |
| --- | --- | --- | --- | --- | --- |
| AC-1 | M01 shipping_fee | 0,1,9999,10000,10001,100000 | Fee 1000 below threshold, else 0; matched | function-level passed | evidence/M01.json; evidence/I01.json |
| AC-2 | M01 shipping_fee | -1,-10000 and checkout propagation | ValueError; matched | function-level passed | evidence/M01.json; evidence/M02.json; evidence/I01.json |
| AC-3 | M02 checkout_total | Real call incl exact 10000 | subtotal+fee, 10000 returns 10000; matched | function-level passed | evidence/M02.json; evidence/I01.json |
| Mandatory environment gate | I02; M01/M02 | Unmodified integration_check.py | exit 0 expected; exit 1 actual | failed | evidence/I02.json |

## Verification layers and limits

Static source and actual import chain inspected. Module tests, abnormal inputs, boundary regression and real function integration passed without stubs. Required full environment integration failed. No independent build required. Device/browser checks not applicable to this Python fixture and not run. Function-level passes do not satisfy I02.

## Failed, unexecuted and unresolved items

I02 failed with RuntimeError: required integration environment is offline; fixture must not bypass this check. Source/checks read-only; cannot repair or remove the check. Restore required environment then rerun unchanged. No other required checks left unexecuted. Historical records lacked digests/raw logs; all results were rechecked rather than inherited.

## Delivery decision

- Tasks/modules: M01/M02 locally passed on new evidence.
- Complete functionality: I01 passes; mandatory I02 fails.
- Required failed check: I02 exit 1.
- Baseline consistency: all covered file hashes unchanged after verification.
- Result: blocked.
- Next: restore integration environment and rerun original I02; do not advance to testing or declare ready.
