#!/usr/bin/env bash
# Serve the Berean reader from the repo root, so web/ and library/ are BOTH reachable.
# Run from anywhere:   bash /path/to/berean/serve.sh [port]
set -euo pipefail
cd "$(dirname "$0")"
PORT="${1:-8000}"
echo "Berean → open http://localhost:$PORT/   (serving $(pwd))"
exec python3 -m http.server "$PORT"
