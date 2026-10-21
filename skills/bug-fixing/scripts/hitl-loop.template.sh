#!/usr/bin/env bash
# Copy to the task-authorized debug directory, then customize the exact symptom.
# Human actions are structured; never claim unattended execution of human steps.
set -euo pipefail
printf '%s\n' 'Perform the documented trigger; do not paste credentials.'
read -r -p 'Does the exact original symptom occur? [red/green/unknown] ' verdict
case "$verdict" in
  red) printf '%s\n' 'FAIL: original symptom reproduced'; exit 1 ;;
  green) printf '%s\n' 'PASS: original symptom absent under documented check'; exit 0 ;;
  *) printf '%s\n' 'BLOCKED: verdict unavailable'; exit 2 ;;
esac
