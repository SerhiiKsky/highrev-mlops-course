# Source this file from Bash. Supports Linux/macOS and Git Bash on Windows.
venv_python() {
    local environment="$1"
    if [[ -x "$environment/bin/python" ]]; then
        printf '%s\n' "$environment/bin/python"
    elif [[ -f "$environment/Scripts/python.exe" ]]; then
        printf '%s\n' "$environment/Scripts/python.exe"
    else
        printf 'No Python interpreter in %s\n' "$environment" >&2
        return 1
    fi
}

native_path() {
    "${PYTHON_BIN:?Set PYTHON_BIN to your Python interpreter}" -c \
        'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve())' "$1"
}

json_get() {
    "${PYTHON_BIN:?Set PYTHON_BIN to your Python interpreter}" -c \
        'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8-sig"))[sys.argv[2]])' "$1" "$2"
}
