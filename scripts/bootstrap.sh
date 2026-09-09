#!/usr/bin/env bash
set -euo pipefail
python "$(dirname "$0")/baseline.py" bootstrap "$@"
