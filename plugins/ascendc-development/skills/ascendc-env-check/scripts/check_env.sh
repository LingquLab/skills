#!/usr/bin/env bash
# Read-only CANN environment inspection.

set -u

script_dir=$(cd -P "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)

if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

errors=0
warnings=0
infos=0

ok() {
    printf '%b[ok]%b %s\n' "$GREEN" "$NC" "$1"
}

info() {
    printf '%b[info]%b %s\n' "$BLUE" "$NC" "$1"
    infos=$((infos + 1))
}

warn() {
    printf '%b[warn]%b %s\n' "$YELLOW" "$NC" "$1"
    warnings=$((warnings + 1))
}

fail() {
    printf '%b[error]%b %s\n' "$RED" "$NC" "$1"
    errors=$((errors + 1))
}

canonical_dir() {
    (cd -P "$1" 2>/dev/null && pwd)
}

looks_like_toolkit() {
    local root=$1
    [[ -d "$root" ]] || return 1
    [[ -f "$root/set_env.sh" || -d "$root/compiler" || ( -d "$root/runtime" && -d "$root/opp" ) ]]
}

first_discovered_toolkit() {
    local candidate=''
    local tool=''
    local probe=''
    local depth=0
    local roots=${ASCEND_ENV_CHECK_ROOTS:-}
    local root_items=()

    if [[ -n "$roots" ]]; then
        IFS=: read -r -a root_items <<< "$roots"
        for candidate in "${root_items[@]}"; do
            if looks_like_toolkit "$candidate"; then
                canonical_dir "$candidate"
                return 0
            fi
        done
    fi

    for candidate in "${ASCEND_TOOLKIT_HOME:-}" "${CANN_HOME:-}" "${ASCEND_HOME:-}"; do
        [[ -n "$candidate" ]] || continue
        if looks_like_toolkit "$candidate"; then
            canonical_dir "$candidate"
            return 0
        fi
    done

    for tool in ccec bisheng msprof; do
        tool=$(command -v "$tool" 2>/dev/null || true)
        [[ -n "$tool" && "$tool" == */* ]] || continue
        probe=$(canonical_dir "$(dirname "$tool")") || continue
        depth=0
        while [[ "$probe" != / && $depth -lt 7 ]]; do
            if looks_like_toolkit "$probe"; then
                printf '%s\n' "$probe"
                return 0
            fi
            probe=$(dirname "$probe")
            depth=$((depth + 1))
        done
    done

    for candidate in \
        "$HOME/Ascend/ascend-toolkit/latest" \
        "$HOME/Ascend/cann" \
        /usr/local/Ascend/ascend-toolkit/latest \
        /usr/local/Ascend/cann/latest \
        /usr/local/Ascend/cann; do
        if looks_like_toolkit "$candidate"; then
            canonical_dir "$candidate"
            return 0
        fi
    done

    return 1
}

read_version_field() {
    local file=$1
    local key=$2
    awk -F= -v key="$key" '
        {
            field=$1
            gsub(/^[[:space:]]+|[[:space:]]+$/, "", field)
        }
        field == key {
            value=substr($0, index($0, "=") + 1)
            gsub(/^[[:space:]"]+|[[:space:]"]+$/, "", value)
            print value
            exit
        }
    ' "$file"
}

printf '%s\n' 'Ascend C environment check'
printf '%s\n' '--------------------------'

ascend_home=${ASCEND_HOME_PATH:-}
toolkit_root=''
toolkit_source=''

if [[ -n "$ascend_home" ]]; then
    if [[ ! -d "$ascend_home" ]]; then
        fail "ASCEND_HOME_PATH does not exist: $ascend_home"
    elif ! looks_like_toolkit "$ascend_home"; then
        fail "ASCEND_HOME_PATH is not recognizable as a CANN toolkit root: $ascend_home"
    else
        toolkit_root=$(canonical_dir "$ascend_home")
        toolkit_source='ASCEND_HOME_PATH'
        ok "active toolkit root=$toolkit_root (source: ASCEND_HOME_PATH)"
    fi
else
    info 'ASCEND_HOME_PATH is not set; probing read-only installation evidence'
fi

if [[ -z "$toolkit_root" ]]; then
    toolkit_root=$(first_discovered_toolkit || true)
    if [[ -n "$toolkit_root" ]]; then
        toolkit_source='discovery'
        ok "toolkit root=$toolkit_root (source: discovery)"
        if [[ -n "$ascend_home" ]]; then
            info 'A separate toolkit installation was found, but it does not repair the invalid active ASCEND_HOME_PATH'
        else
            info 'Toolkit files are installed, but the current shell may not have loaded the vendor environment'
        fi
    else
        warn 'No CANN toolkit root was found from environment variables, tool paths, overrides, or common locations'
    fi
fi

version=''
runtime_requirement=''
version_source=''
state_release_status=''
if [[ -n "$toolkit_root" ]]; then
    version_candidates=(
        "$toolkit_root/compiler/version.info"
        "$toolkit_root/version.info"
        "$toolkit_root/version.cfg"
    )
    for candidate in "${version_candidates[@]}"; do
        [[ -f "$candidate" ]] || continue
        version_source=$candidate
        version=$(read_version_field "$candidate" 'Version')
        runtime_requirement=$(read_version_field "$candidate" 'required_package_runtime_version')
        if [[ -z "$version" && "$candidate" == *.cfg ]]; then
            version=$(awk 'NF {print; exit}' "$candidate")
        fi
        [[ -n "$version" ]] && break
    done
fi

if [[ -n "$toolkit_root" ]]; then
    state_inspector="$script_dir/inspect_cann_state.py"
    if [[ -f "$state_inspector" ]] && command -v python3 >/dev/null 2>&1; then
        info 'bounded component metadata inventory follows'
        state_output=''
        if state_output=$(python3 "$state_inspector" --toolkit-root "$toolkit_root" 2>&1); then
            printf '%s\n' "$state_output"
            state_release_status=$(printf '%s\n' "$state_output" | awk '/^toolkit release:/ { sub(/^.*\(/, ""); sub(/\).*$/, ""); print; exit }')
            state_warning_count=$(printf '%s\n' "$state_output" | awk '/^\[warn\]/ { count++ } END { print count + 0 }')
            warnings=$((warnings + state_warning_count))
        else
            printf '%s\n' "$state_output"
            warn 'component metadata inventory failed; inspect the helper error separately'
        fi
    elif [[ ! -f "$state_inspector" ]]; then
        warn "component metadata inspector is missing: $state_inspector"
    else
        warn 'python3 is unavailable; component metadata inventory was skipped'
    fi
fi

if [[ -n "$state_release_status" && "$state_release_status" != 'resolved' ]]; then
    warn "CANN version metadata is not resolved below the selected toolkit root: $toolkit_root (status: $state_release_status)"
    version=''
    runtime_requirement=''
elif [[ -n "$version" ]]; then
    ok "CANN version=$version (source: $version_source)"
    if [[ -n "$runtime_requirement" ]]; then
        printf '      required runtime=%s\n' "$runtime_requirement"
    fi
elif [[ -n "$toolkit_root" ]]; then
    warn "CANN version metadata was not found below the selected toolkit root: $toolkit_root"
else
    info 'CANN version check is unavailable without a discovered toolkit root'
fi

opp_path=${ASCEND_OPP_PATH:-}
resolved_opp=''
if [[ -n "$opp_path" ]]; then
    if [[ -d "$opp_path" ]]; then
        resolved_opp=$(canonical_dir "$opp_path")
        ok "operator repository=$resolved_opp (source: ASCEND_OPP_PATH)"
    else
        fail "ASCEND_OPP_PATH does not exist: $opp_path"
    fi
elif [[ -n "$toolkit_root" && -d "$toolkit_root/opp" ]]; then
    resolved_opp=$(canonical_dir "$toolkit_root/opp")
    info "ASCEND_OPP_PATH is not set; discovered operator repository=$resolved_opp"
else
    warn 'ASCEND_OPP_PATH is not set and no operator repository was found below the selected toolkit root'
fi

if [[ -n "$resolved_opp" ]]; then
    opp_version_file="$resolved_opp/version.info"
    if [[ -f "$opp_version_file" ]]; then
        opp_version=$(read_version_field "$opp_version_file" 'Version')
        if [[ -n "$opp_version" ]]; then
            ok "OPP version=$opp_version (source: $opp_version_file)"
            if [[ -n "$version" && "$opp_version" != "$version" ]]; then
                warn "Toolkit version $version and OPP version $opp_version differ; verify the release compatibility matrix"
            fi
        else
            warn "OPP version metadata has no Version field: $opp_version_file"
        fi
    else
        info "OPP version metadata was not found: $opp_version_file"
    fi

    if [[ -d "$resolved_opp/vendors" ]]; then
        vendor_count=$(find "$resolved_opp/vendors" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
        info "vendor directories=$vendor_count (this does not prove each package is loadable)"
    else
        info 'No vendors directory was found; this alone does not prove that built-in operator content is missing'
    fi
fi

compiler_found=0
for tool in ccec bisheng; do
    if command -v "$tool" >/dev/null 2>&1; then
        ok "$tool=$(command -v "$tool")"
        compiler_found=1
    fi
done
if (( compiler_found == 0 )); then
    warn 'Neither ccec nor bisheng is available on PATH for a compile check'
fi

for tool in npu-smi msprof; do
    if command -v "$tool" >/dev/null 2>&1; then
        ok "$tool=$(command -v "$tool")"
    else
        info "$tool is not available on PATH"
    fi
done

if [[ -n "$toolkit_root" ]]; then
    set_env=''
    for candidate in "$toolkit_root/set_env.sh" "$(dirname "$toolkit_root")/set_env.sh"; do
        if [[ -f "$candidate" ]]; then
            set_env=$candidate
            break
        fi
    done
    if [[ -n "$set_env" ]]; then
        ok "environment script=$set_env"
    else
        warn "set_env.sh was not found at the selected toolkit root or its parent: $toolkit_root"
    fi
fi

printf '\nsummary: errors=%d warnings=%d info=%d\n' "$errors" "$warnings" "$infos"
if (( errors > 0 )); then
    exit 1
fi
exit 0
