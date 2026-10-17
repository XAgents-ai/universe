#!/usr/bin/env bash
set -euo pipefail
python v0_regression.py
python test_f6_resolution.py
python test_oracle_bounded_negative.py
python v0_acceptance.py
python v0_memory_witness.py
python v0_oracle.py
python v0_responder.py
UNIVERSE_STATE_DIR="$(mktemp -d)" python test_viewer_api.py
UNIVERSE_STATE_DIR="$(mktemp -d)" python test_live_world.py
python test_journal_integrity.py
if [ "${WITH_BROWSER:-0}" = '1' ]; then
  UNIVERSE_STATE_DIR="$(mktemp -d)" python test_viewer_ui.py
  python test_live_ui.py
fi
