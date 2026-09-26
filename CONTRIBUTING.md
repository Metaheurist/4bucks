# Contributing

4Bucks is an offline Windows tool that edits GTA IV Complete Edition `SGTA4xx` saves. In-scope: **PlayerInfo** (money, weapons, vitality) and **Block 4 Garages** (StoredCar parking). Do not resize blocks or rewrite Scripts, Stats, Radar, or End.

## Prerequisites

1. [docs/SECURITY.md](docs/SECURITY.md) - no live memory, injection, ASI trainers, or live-cheat offset dumps.
2. [docs/versioning.md](docs/versioning.md) and [docs/save-format.md](docs/save-format.md) before changing write logic.
3. Open an Issue before large features or new savegame version support.

## Development setup (Windows)

```powershell
cd path\to\4bucks
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest tests/unit -q
python -m src
```

Dual-arch EXE: [docs/setup-and-usage.md](docs/setup-and-usage.md), `build.ps1`.

## Pull requests

- Target `main`. Keep each PR focused.
- Run pytest and pip-audit locally ([docs/testing-and-configuration.md](docs/testing-and-configuration.md)).
- CI must pass: unit tests, Gitleaks, pip-audit, Windows EXE matrix.
- Use ASCII hyphens (`-`) in docs; do not commit secrets, real saves, `.venv`, `dist`, or `backups`.
- New PlayerInfo fields: extend `src/playerinfo.py`, fixtures in `tests/unit/fixtures.py`, document in `docs/save-format.md`.
- Garage changes: extend `src/save_garage.py` / `src/safehouse_parking.py` with tests; keep block size fixed.

## Code map

| Area | Path |
|------|------|
| Flet UI | `src/app.py` |
| Write gate / technique | `src/versioning.py` |
| Money / weapons / vitality | `src/save_*.py`, `src/playerinfo.py` |
| Garages / vehicles | `src/save_garage.py`, `src/safehouse_parking.py`, `src/vehicles_catalog.py` |
| CI | `.github/workflows/ci.yml`, `scripts/ci/` |
