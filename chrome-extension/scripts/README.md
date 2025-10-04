# Snapshot Utility

`snapshot_infobae.sh` mirrors [infobae.com](https://www.infobae.com/) for offline use while caching assets to avoid re-downloading unchanged files.

## Requirements

- `wget`
- `python3` (only needed when using the `-s` flag to serve the snapshot)
- `rsync` (optional; speeds up copying cached data into timestamped snapshots)

## Usage

```bash
./snapshot_infobae.sh [-o output_dir] [-p port] [-s] [-u url] [-d depth]
```

- `-o output_dir` sets the base directory where snapshots and cache are stored (default: `snapshots/infobae`).
- `-p port` chooses the port when serving locally (default: `8080`).
- `-s` serves the freshly created snapshot with `python3 -m http.server`.
- `-u url` allows overriding the source URL (defaults to `https://www.infobae.com/`).
- `-d depth` limits recursion depth (`wget --level`) so you can bound the crawl size.

Each run updates the persistent cache at `output_dir/cache/`, so subsequent runs only fetch new or changed files. After mirroring, a timestamped copy is created at `output_dir/<timestamp>/`, and the most recent snapshot path is recorded in `output_dir/latest_snapshot`.
