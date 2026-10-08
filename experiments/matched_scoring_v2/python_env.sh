#!/bin/sh
# Portable Python 3.11+ launcher for Windows Git Bash and POSIX shells.
# Source this file, then use: run_python <args...>

find_python() {
    for p in \
        "${MATCHED_ROOT:-.}/.venv/Scripts/python.exe" \
        "${MATCHED_ROOT:-.}/../.venv/Scripts/python.exe" \
        "${MATCHED_ROOT:-.}/.venv/bin/python" \
        "${MATCHED_ROOT:-.}/../.venv/bin/python"
    do
        if [ -x "$p" ] && "$p" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
            MATCHED_PY_KIND=exe
            MATCHED_PY_EXE=$p
            export MATCHED_PY_KIND MATCHED_PY_EXE
            return 0
        fi
    done
    if command -v py >/dev/null 2>&1 && py -3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
        MATCHED_PY_KIND=py3
        MATCHED_PY_EXE=py
        export MATCHED_PY_KIND MATCHED_PY_EXE
        return 0
    fi
    if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
        MATCHED_PY_KIND=exe
        MATCHED_PY_EXE=$(command -v python3)
        export MATCHED_PY_KIND MATCHED_PY_EXE
        return 0
    fi
    if command -v python >/dev/null 2>&1 && python -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
        MATCHED_PY_KIND=exe
        MATCHED_PY_EXE=$(command -v python)
        export MATCHED_PY_KIND MATCHED_PY_EXE
        return 0
    fi
    echo "ERROR: Python 3.11+ was not found." >&2
    echo "Tried project .venv, Windows 'py -3', python3, and python." >&2
    return 1
}

run_python() {
    case "${MATCHED_PY_KIND:-}" in
        py3) py -3 "$@" ;;
        exe) "$MATCHED_PY_EXE" "$@" ;;
        *) find_python || return 127; run_python "$@" ;;
    esac
}

find_python
