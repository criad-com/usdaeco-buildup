#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
TOOLCHAIN_DIR="${TOOLCHAIN_DIR:-$HERE/../usdaeco-toolchain}"
CORE_DIR="${AECO_CORE_ROOT:-${CORE_DIR:-$HERE/../usdaeco-core}}"
bash "$TOOLCHAIN_DIR/build.sh" usdAecoBuildUp "$HERE" \
    --dep "${CORE_PLUGIN_DIR:-$CORE_DIR/out/plugins/usdAeco/resources}" "$@"

# Install the source companion beside the Python validator module.
while (( $# )); do
    if [[ "$1" == "--install-root" ]]; then
        mkdir -p "$2/python"
        cp -RL "$HERE/tools/usdaeco_buildup" "$2/python/"
        break
    fi
    shift
done
