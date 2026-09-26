# Next phase development plan

Active roadmap for Save 4Bucks (post **v1.2.0**). Shipped work lives in [CHANGELOG.md](CHANGELOG.md).

## Near term

- Optional in-app link to latest GitHub Release / version check (still offline-first; no forced updates).
- Expand synthetic fixtures if additional CE patches publish new `SAVEGAME_VERSION_NUMBER` values.
- README CI build stamp automation (populate the `SAVE4BUCKS_BUILD_INFO` channel table from Actions).
- Confirm or drop **x86** release artifacts if Flet desktop remains x64-only in practice.

## Later

- Signed EXE / SmartScreen guidance for release artifacts.
- Accessibility pass on the Flet UI (keyboard focus, contrast).
- Contributor guide (`CONTRIBUTING.md`) if the project gains external PRs.
