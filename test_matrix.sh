#!/usr/bin/env bash
# Matrix compatibility test: pandera × pandas versions
# Usage: bash test_matrix.sh

set -uo pipefail

PANDERA_VERSIONS=("0.24.0" "0.25.0" "0.27.1" "0.31.1")
PANDAS_VERSIONS=("2.0.3" "2.1.4" "2.2.3" "2.3.3")

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENVS_DIR="/tmp/pandera_ui_matrix"
RESULTS=()

mkdir -p "$ENVS_DIR"

run_combo() {
    local pandera_ver="$1"
    local pandas_ver="$2"
    local label="pandera==${pandera_ver}  pandas==${pandas_ver}"
    local env_dir="${ENVS_DIR}/pa${pandera_ver}_pd${pandas_ver}"

    printf "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    printf "  Testing: %s\n" "$label"
    printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

    rm -rf "$env_dir"
    if ! uv venv "$env_dir" --python 3.11 -q 2>&1; then
        RESULTS+=("⚠️  ENV_FAIL  ${label}")
        return
    fi

    local python="${env_dir}/bin/python"

    # Install everything using uv pip with this specific venv as target
    local install_exit=0
    uv pip install -q \
        --python "$python" \
        --no-deps \
        -e "${PROJECT_DIR}" \
        2>&1 || install_exit=$?

    local install_exit2=0
    uv pip install -q \
        --python "$python" \
        "pandas==${pandas_ver}" \
        "pandera[pandas]==${pandera_ver}" \
        "fastapi>=0.111" \
        "uvicorn[standard]>=0.30" \
        "typer>=0.12" \
        "pydantic>=2.0" \
        "httpx>=0.27" \
        "pytest>=8" \
        2>&1 | tail -5 || install_exit2=$?

    if [[ $install_exit2 -ne 0 ]]; then
        RESULTS+=("⚠️  INSTALL_FAIL  ${label}")
        return
    fi

    local output=""
    local exit_code=0
    output=$("$python" -m pytest "${PROJECT_DIR}/tests/" \
        --tb=line -q \
        --ignore="${PROJECT_DIR}/tests/test_ui.py" \
        2>&1) || exit_code=$?

    local passed
    passed=$(echo "$output" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' | head -1 || echo "0")

    echo "$output" | tail -8

    if [[ $exit_code -eq 0 ]]; then
        RESULTS+=("✅ PASS  ${label}  (${passed} passed)")
    else
        RESULTS+=("❌ FAIL  ${label}  (${passed} passed, exit=${exit_code})")
    fi
}

for pandera_ver in "${PANDERA_VERSIONS[@]}"; do
    for pandas_ver in "${PANDAS_VERSIONS[@]}"; do
        run_combo "$pandera_ver" "$pandas_ver"
    done
done

printf "\n════════════════════════════════════════════════\n"
printf "  RESULTS SUMMARY\n"
printf "════════════════════════════════════════════════\n"
for r in "${RESULTS[@]}"; do
    printf "  %s\n" "$r"
done
printf "\n"
