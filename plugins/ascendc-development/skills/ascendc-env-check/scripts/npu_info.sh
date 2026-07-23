#!/usr/bin/env bash
# Read-only NPU status query with an asys fallback.

set -u

run_bounded() {
    if command -v timeout >/dev/null 2>&1; then
        timeout 20 "$@"
    else
        "$@"
    fi
}

find_asys() {
    local ascend_home=${ASCEND_HOME_PATH:-}
    local bundled=''
    if [[ -n "$ascend_home" ]]; then
        bundled="$ascend_home/tools/ascend_system_advisor/asys/asys"
    fi

    if [[ -n "$bundled" && -x "$bundled" ]]; then
        printf '%s\n' "$bundled"
    elif command -v asys >/dev/null 2>&1; then
        command -v asys
    fi
}

printf '%s\n' 'Ascend NPU status'
printf '%s\n' '-----------------'

if command -v npu-smi >/dev/null 2>&1; then
    output=$(run_bounded npu-smi info 2>&1)
    status=$?
    if (( status == 0 )) && [[ -n "$output" ]]; then
        printf 'source: npu-smi (%s)\n\n' "$(command -v npu-smi)"
        printf '%s\n' "$output"
        exit 0
    fi
    printf 'npu-smi failed with status %d\n' "$status" >&2
    [[ -z "$output" ]] || printf '%s\n' "$output" >&2
fi

asys_cmd=$(find_asys)
if [[ -n "$asys_cmd" ]]; then
    output=$(run_bounded "$asys_cmd" health 2>&1)
    status=$?
    if (( status == 0 )) && [[ -n "$output" ]]; then
        printf 'source: asys (%s)\n\n' "$asys_cmd"
        printf '%s\n' "$output"
        exit 0
    fi
    printf 'asys health failed with status %d\n' "$status" >&2
    [[ -z "$output" ]] || printf '%s\n' "$output" >&2
fi

printf '%s\n' 'No working npu-smi or asys device query was found.' >&2
exit 1
