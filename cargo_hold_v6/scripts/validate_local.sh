#!/usr/bin/env bash
set -euo pipefail
CARGO_PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export CARGO_PROJECT_ROOT
cmake -S "$CARGO_PROJECT_ROOT" -B "$CARGO_PROJECT_ROOT/build" -DCMAKE_BUILD_TYPE=Release
cmake --build "$CARGO_PROJECT_ROOT/build" -j2
ctest --test-dir "$CARGO_PROJECT_ROOT/build" --output-on-failure
gz sdf -k "$CARGO_PROJECT_ROOT/worlds/cargo_hold_cutaway.sdf"
gz sdf -k "$CARGO_PROJECT_ROOT/worlds/cargo_hold_full.sdf"
echo 'Core and SDF checks finished. These do not certify physics or aircraft compatibility.'
