#!/usr/bin/env bash
set -euo pipefail
CARGO_PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export CARGO_PROJECT_ROOT
export CARGO_REPLAY_SPEED=1
world=cargo_hold_cutaway.sdf
extra=()
while (($#)); do
 case "$1" in
  --full) world=cargo_hold_full.sdf; shift;;
  --speed) export CARGO_REPLAY_SPEED="$2"; shift 2;;
  --headless) extra+=(-s); shift;;
  --iterations) extra+=(--iterations "$2"); shift 2;;
  *) echo "Usage: ./run_gazebo.sh [--full] [--speed 1..1000] [--headless] [--iterations N]"; exit 2;;
 esac
done
command -v gz >/dev/null || { echo 'Gazebo Harmonic not installed. See README_ID.md.'; exit 1; }
cmake -S "$CARGO_PROJECT_ROOT" -B "$CARGO_PROJECT_ROOT/build" -DCMAKE_BUILD_TYPE=Release
cmake --build "$CARGO_PROJECT_ROOT/build" -j2
export GZ_SIM_SYSTEM_PLUGIN_PATH="$CARGO_PROJECT_ROOT/build${GZ_SIM_SYSTEM_PLUGIN_PATH:+:$GZ_SIM_SYSTEM_PLUGIN_PATH}"
export GZ_SIM_RESOURCE_PATH="$CARGO_PROJECT_ROOT/models${GZ_SIM_RESOURCE_PATH:+:$GZ_SIM_RESOURCE_PATH}"
exec gz sim -r -v 3 "${extra[@]}" "$CARGO_PROJECT_ROOT/worlds/$world"
