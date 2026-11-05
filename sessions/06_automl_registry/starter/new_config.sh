#!/usr/bin/env bash
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if [[ $# -ne 4 ]]; then
    printf 'Usage: bash new_config.sh PROJECT RUN_DIRECTORY GIT_COMMIT DATA_HASH\n' >&2
    exit 2
fi
"${PYTHON_BIN:-python3}" "$script_dir/new_config.py" "$@"
