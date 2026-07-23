#!/usr/bin/env bash
# Read-only NPU status query with bounded raw output and an asys fallback.

set -u

MAX_LINES=${ASCEND_NPU_MAX_LINES:-400}
MAX_BYTES=${ASCEND_NPU_MAX_BYTES:-65536}

is_positive_integer() {
    [[ "$1" =~ ^[1-9][0-9]*$ ]]
}

if ! is_positive_integer "$MAX_LINES" || ! is_positive_integer "$MAX_BYTES"; then
    printf '%s\n' 'ASCEND_NPU_MAX_LINES and ASCEND_NPU_MAX_BYTES must be positive integers.' >&2
    exit 2
fi

run_bounded_time() {
    if command -v timeout >/dev/null 2>&1; then
        timeout 20 "$@"
    elif command -v gtimeout >/dev/null 2>&1; then
        gtimeout 20 "$@"
    elif command -v python3 >/dev/null 2>&1; then
        python3 -c '
import subprocess
import sys

try:
    result = subprocess.run(sys.argv[1:], timeout=20)
except subprocess.TimeoutExpired:
    raise SystemExit(124)
raise SystemExit(result.returncode)
' "$@"
    else
        printf '%s\n' 'No timeout utility or Python 3 is available; refusing an unbounded device query.' >&2
        return 125
    fi
}

CAPTURE_STATUS=0
CAPTURE_BYTES=0
CAPTURE_BYTE_TRUNCATED=0

capture_query() {
    local output_file=$1
    shift
    local statuses=()
    local capture_limit=$((MAX_BYTES + 1))

    : > "$output_file"
    run_bounded_time "$@" 2>&1 | {
        head -c "$capture_limit" > "$output_file"
        # Keep draining the pipe so the producer retains its real exit status
        # instead of receiving SIGPIPE when the display prefix is full.
        cat > /dev/null
    }
    statuses=("${PIPESTATUS[@]}")
    CAPTURE_STATUS=${statuses[0]}
    CAPTURE_BYTES=$(wc -c < "$output_file" | tr -d ' ')
    CAPTURE_BYTE_TRUNCATED=0
    if (( CAPTURE_BYTES > MAX_BYTES )); then
        CAPTURE_BYTE_TRUNCATED=1
    fi
}

print_bounded_file() {
    local output_file=$1
    head -c "$MAX_BYTES" "$output_file" | awk -v limit="$MAX_LINES" '
        NR <= limit { print }
        NR == limit + 1 {
            print "[output truncated after " limit " lines]"
            exit
        }
    '
    if (( CAPTURE_BYTE_TRUNCATED == 1 )); then
        printf '[output truncated after %d bytes]\n' "$MAX_BYTES"
    fi
}

looks_like_toolkit() {
    local root=$1
    [[ -d "$root" ]] || return 1
    [[ -f "$root/set_env.sh" || -d "$root/compiler" || ( -d "$root/runtime" && -d "$root/opp" ) ]]
}

find_asys() {
    local candidate=''
    local roots=${ASCEND_ENV_CHECK_ROOTS:-}
    local root_items=()

    if command -v asys >/dev/null 2>&1; then
        command -v asys
        return 0
    fi

    for candidate in \
        "${ASCEND_HOME_PATH:-}" \
        "${ASCEND_TOOLKIT_HOME:-}" \
        "${CANN_HOME:-}" \
        "${ASCEND_HOME:-}"; do
        [[ -n "$candidate" ]] || continue
        if [[ -x "$candidate/tools/ascend_system_advisor/asys/asys" ]]; then
            printf '%s\n' "$candidate/tools/ascend_system_advisor/asys/asys"
            return 0
        fi
    done

    if [[ -n "$roots" ]]; then
        IFS=: read -r -a root_items <<< "$roots"
        for candidate in "${root_items[@]}"; do
            looks_like_toolkit "$candidate" || continue
            if [[ -x "$candidate/tools/ascend_system_advisor/asys/asys" ]]; then
                printf '%s\n' "$candidate/tools/ascend_system_advisor/asys/asys"
                return 0
            fi
        done
    fi

    for candidate in \
        "$HOME/Ascend/ascend-toolkit/latest" \
        "$HOME/Ascend/cann" \
        /usr/local/Ascend/ascend-toolkit/latest \
        /usr/local/Ascend/cann/latest \
        /usr/local/Ascend/cann; do
        looks_like_toolkit "$candidate" || continue
        if [[ -x "$candidate/tools/ascend_system_advisor/asys/asys" ]]; then
            printf '%s\n' "$candidate/tools/ascend_system_advisor/asys/asys"
            return 0
        fi
    done

    return 1
}

printf '%s\n' 'Ascend NPU status'
printf '%s\n' '-----------------'

capture_file=$(mktemp "${TMPDIR:-/tmp}/ascend-npu-info.XXXXXX") || {
    printf '%s\n' 'Unable to create a bounded diagnostic capture file.' >&2
    exit 2
}
trap 'rm -f -- "$capture_file"' EXIT HUP INT TERM

if command -v npu-smi >/dev/null 2>&1; then
    capture_query "$capture_file" npu-smi info
    status=$CAPTURE_STATUS
    if (( status == 0 )) && [[ -s "$capture_file" ]]; then
        printf 'source: npu-smi (%s)\n\n' "$(command -v npu-smi)"
        print_bounded_file "$capture_file"
        exit 0
    fi
    printf 'npu-smi failed with status %d\n' "$status" >&2
    [[ ! -s "$capture_file" ]] || print_bounded_file "$capture_file" >&2
fi

asys_cmd=$(find_asys || true)
if [[ -n "$asys_cmd" ]]; then
    capture_query "$capture_file" "$asys_cmd" health
    status=$CAPTURE_STATUS
    if (( status == 0 )) && [[ -s "$capture_file" ]]; then
        printf 'source: asys (%s)\n\n' "$asys_cmd"
        print_bounded_file "$capture_file"
        exit 0
    fi
    printf 'asys health failed with status %d\n' "$status" >&2
    [[ ! -s "$capture_file" ]] || print_bounded_file "$capture_file" >&2
fi

printf '%s\n' 'No working npu-smi or asys status query was found.' >&2
exit 1
