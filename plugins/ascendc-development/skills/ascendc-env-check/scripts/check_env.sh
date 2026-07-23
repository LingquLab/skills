#!/usr/bin/env bash
# Read-only CANN environment inspection.

set -u

if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    NC=''
fi

errors=0
warnings=0

ok() {
    printf '%b[ok]%b %s\n' "$GREEN" "$NC" "$1"
}

warn() {
    printf '%b[warn]%b %s\n' "$YELLOW" "$NC" "$1"
    warnings=$((warnings + 1))
}

fail() {
    printf '%b[error]%b %s\n' "$RED" "$NC" "$1"
    errors=$((errors + 1))
}

read_version_field() {
    local file=$1
    local key=$2
    awk -F= -v key="$key" '$1 == key {value=$2; gsub(/^"|"$/, "", value); print value; exit}' "$file"
}

printf '%s\n' 'Ascend C environment check'
printf '%s\n' '--------------------------'

ascend_home=${ASCEND_HOME_PATH:-}
if [[ -z "$ascend_home" ]]; then
    fail 'ASCEND_HOME_PATH is not set'
elif [[ ! -d "$ascend_home" ]]; then
    fail "ASCEND_HOME_PATH does not exist: $ascend_home"
else
    ok "ASCEND_HOME_PATH=$ascend_home"
fi

version=''
runtime_requirement=''
version_source=''
if [[ -n "$ascend_home" ]]; then
    version_candidates=(
        "$ascend_home/compiler/version.info"
        "$ascend_home/version.info"
        "$ascend_home/version.cfg"
    )
    for candidate in "${version_candidates[@]}"; do
        [[ -f "$candidate" ]] || continue
        version_source=$candidate
        if [[ "$candidate" == *.info ]]; then
            version=$(read_version_field "$candidate" 'Version')
            runtime_requirement=$(read_version_field "$candidate" 'required_package_runtime_version')
        else
            version=$(awk 'NF {print; exit}' "$candidate")
        fi
        [[ -n "$version" ]] && break
    done
fi

if [[ -n "$version" ]]; then
    ok "CANN version=$version (source: $version_source)"
    if [[ -n "$runtime_requirement" ]]; then
        printf '      required runtime=%s\n' "$runtime_requirement"
    fi
else
    warn 'CANN version metadata was not found under ASCEND_HOME_PATH'
fi

opp_path=${ASCEND_OPP_PATH:-}
if [[ -z "$opp_path" ]]; then
    warn 'ASCEND_OPP_PATH is not set; runtime operator packages may be unavailable'
elif [[ ! -d "$opp_path" ]]; then
    fail "ASCEND_OPP_PATH does not exist: $opp_path"
else
    ok "ASCEND_OPP_PATH=$opp_path"
    if [[ -d "$opp_path/vendors" ]]; then
        vendor_count=$(find "$opp_path/vendors" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
        printf '      vendor directories=%s\n' "$vendor_count"
    fi
fi

for tool in bisheng npu-smi msprof; do
    if command -v "$tool" >/dev/null 2>&1; then
        ok "$tool=$(command -v "$tool")"
    else
        warn "$tool is not available on PATH"
    fi
done

if [[ -n "$ascend_home" && -d "$ascend_home" ]]; then
    set_env=''
    for candidate in "$ascend_home/set_env.sh" "$(dirname "$ascend_home")/set_env.sh"; do
        if [[ -f "$candidate" ]]; then
            set_env=$candidate
            break
        fi
    done
    if [[ -n "$set_env" ]]; then
        ok "environment script=$set_env"
    else
        warn 'set_env.sh was not found at the common locations near ASCEND_HOME_PATH'
    fi
fi

printf '\nsummary: errors=%d warnings=%d\n' "$errors" "$warnings"
if (( errors > 0 )); then
    exit 1
fi
