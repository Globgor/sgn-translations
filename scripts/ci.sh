#!/bin/sh
# All checks that CI runs, in one script. Run it from the repository root.
#   Needs: Python 3, GNU gettext, Perl+PPI, Node+npm, R 4.5.0 + jsonlite 2.0.0
#   (scripts/install-ci-deps.sh installs them on Ubuntu 24.04).
# Optional: SGN_CHECKOUT=/path/to/sgn runs the tests that read SGN files
# (manual chapters, marked source files, runtime fixtures); they skip without it.
set -u
cd "$(dirname "$0")/.."
export PYTHONDONTWRITEBYTECODE=1
status=0
step() { echo; echo "=== $*"; }

step "Install the pinned JavaScript parser (tools/package-lock.json)"
npm ci --prefix tools --ignore-scripts --no-audit --no-fund || exit 1

step "Catalog structure: python3 tools/check_catalogs.py"
python3 -B tools/check_catalogs.py \
    --count '\bлокаці(я|ї|ю|єю|й|ям|ями|ях)\b' \
    --count '\bмісц(е|я|ю|ем|і|ь|ям|ями|ях)\b' || status=1

step "Tool tests: tools/test_*.py (SGN_CHECKOUT=${SGN_CHECKOUT:-not set})"
for test in tools/test_*.py; do
    echo "--- $test"
    python3 -B "$test" || status=1
done

echo
if [ "$status" -eq 0 ]; then echo "ALL CHECKS PASSED"; else echo "SOME CHECKS FAILED"; fi
exit "$status"
