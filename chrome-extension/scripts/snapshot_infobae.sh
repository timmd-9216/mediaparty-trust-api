#!/usr/bin/env bash
set -Eeuo pipefail

# Mirrors infobae.com locally and optionally serves the snapshot via Python's http.server.
# Usage: snapshot_infobae.sh [-o output_dir] [-p port] [-s] [-u url] [-d depth]
#   -o output_dir  Directory to store snapshots (default: snapshots/infobae)
#   -p port        Port used when serving the snapshot (default: 8080)
#   -s             Serve the most recent snapshot after mirroring completes
#   -u url         Override the source URL (default: https://www.infobae.com/)
#   -d depth       Limit crawl depth (passed to wget --level)

DEFAULT_URL="https://www.infobae.com/"
OUTPUT_BASE="snapshots/infobae"
PORT="8080"
SERVE=false
URL="$DEFAULT_URL"
DEPTH=""

usage() {
  echo "Usage: $(basename "$0") [-o output_dir] [-p port] [-s] [-u url] [-d depth]" >&2
  exit 1
}

while getopts ":o:p:su:d:" opt; do
  case "$opt" in
    o) OUTPUT_BASE="$OPTARG" ;;
    p) PORT="$OPTARG" ;;
    s) SERVE=true ;;
    u) URL="$OPTARG" ;;
    d)
      if [[ "$OPTARG" =~ ^[0-9]+$ ]]; then
        DEPTH="$OPTARG"
      else
        echo "Error: depth must be a non-negative integer." >&2
        exit 1
      fi
      ;;
    *) usage ;;
  esac
done

if ! command -v wget >/dev/null 2>&1; then
  echo "Error: wget is required but not installed." >&2
  exit 1
fi

CACHE_DIR="$OUTPUT_BASE/cache"
SNAPSHOT_TIME=$(date +"%Y%m%d-%H%M%S")
SNAPSHOT_DIR="$OUTPUT_BASE/$SNAPSHOT_TIME"

mkdir -p "$CACHE_DIR" "$SNAPSHOT_DIR"

# Respectful mirroring options to avoid hammering the origin.
WGET_COMMON_ARGS=(
  --mirror
  --page-requisites
  --convert-links
  --adjust-extension
  --no-parent
  --compression=auto
  --restrict-file-names=windows
  --timeout=30
  --tries=3
  --wait=1
  --random-wait
  --directory-prefix="$CACHE_DIR"
  --timestamping
)

if [[ -n "$DEPTH" ]]; then
  WGET_COMMON_ARGS+=("--level=$DEPTH")
fi

echo "[info] Mirroring $URL into $CACHE_DIR (snapshot copy will be $SNAPSHOT_DIR)" >&2
if ! wget "${WGET_COMMON_ARGS[@]}" "$URL"; then
  echo "Error: wget failed. Check the output above for details." >&2
  exit 1
fi

echo "[info] Mirror updated. Creating timestamped snapshot." >&2
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete "$CACHE_DIR/" "$SNAPSHOT_DIR/"
else
  # Fallback to cp -a; may leave stale files if source no longer provides them.
  cp -a "$CACHE_DIR/." "$SNAPSHOT_DIR/"
fi

domain_dir=$(find "$SNAPSHOT_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)
if [[ -z "$domain_dir" ]]; then
  echo "Error: Unable to locate mirrored domain directory in $SNAPSHOT_DIR" >&2
  exit 1
fi

echo "[info] Local root: $domain_dir" >&2

echo "$SNAPSHOT_DIR" > "$OUTPUT_BASE/latest_snapshot"

echo "[info] Snapshot complete." >&2

if [[ "$SERVE" == true ]]; then
  if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 is required to serve the snapshot." >&2
    exit 1
  fi
  echo "[info] Serving snapshot on http://localhost:$PORT (press Ctrl+C to stop)" >&2
  (cd "$domain_dir" && python3 -m http.server "$PORT")
fi

