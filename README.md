# Save 4Bucks - GTA IV CE save money editor

**Save 4Bucks** is a Windows desktop tool that edits **cash** in Grand Theft Auto IV **Complete Edition** save files (`SGTA4xx`). It is an **offline save editor only** - no process memory, no injection, no live godmode/weapons.

**Latest changes:** **[CHANGELOG.md](CHANGELOG.md)** (current **v1.1.0** - dual-arch x64/x86 builds, GitHub Actions release pipeline, docs hub).

### Here's what we plan next

**[docs/next-phase-development-plan.md](docs/next-phase-development-plan.md)** - optional UX polish, broader CE verification notes, and packaging improvements. Shipped work is in the **[changelog](docs/CHANGELOG.md)** and **[app overview](docs/app-and-features.md)**.

### Tech stack

<table>
<tr>
<td><b>🧩&nbsp;Core</b></td>
<td>

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![tkinter](https://img.shields.io/badge/UI-tkinter%20(stdlib)-3776AB?style=flat-square&logo=python&logoColor=white)](https://docs.python.org/3/library/tkinter.html)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?style=flat-square&logo=windows&logoColor=white)](https://www.microsoft.com/windows)

</td>
</tr>
<tr>
<td><b>📦&nbsp;Packaging</b></td>
<td>

[![PyInstaller](https://img.shields.io/badge/PyInstaller-6.22.3-000000?style=flat-square)](https://pyinstaller.org/)
[![Pillow](https://img.shields.io/badge/Pillow-12.3.0-8B5CF6?style=flat-square)](https://python-pillow.org/)
[![x64](https://img.shields.io/badge/EXE-x64-2e7d32?style=flat-square)](docs/build-test-and-ci.md)
[![x86](https://img.shields.io/badge/EXE-x86-2e7d32?style=flat-square)](docs/build-test-and-ci.md)

</td>
</tr>
<tr>
<td><b>🛠️&nbsp;Tooling&nbsp;&&nbsp;CI</b></td>
<td>

[![pytest](https://img.shields.io/badge/pytest-9.0.3-0A9EDC?style=flat-square&logo=pytest&logoColor=white)](https://pytest.org/)
[![pip-audit](https://img.shields.io/badge/pip--audit-2.9.0-CB3837?style=flat-square)](https://pypi.org/project/pip-audit/)
[![Gitleaks](https://img.shields.io/badge/Gitleaks-secret%20scan-1E2E3E?style=flat-square)](https://github.com/gitleaks/gitleaks)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-CI-2088FF?style=flat-square&logo=githubactions&logoColor=white)](https://github.com/Metaheurist/4bucks/actions)

</td>
</tr>
</table>

**Repository**: [github.com/Metaheurist/4bucks](https://github.com/Metaheurist/4bucks)

<!-- SAVE4BUCKS_BUILD_INFO_START -->

[![CI builds](https://img.shields.io/badge/build-see%20Actions-2e7d32?style=flat-square)](https://github.com/Metaheurist/4bucks/actions)

**CI builds** (Windows EXE)

| Channel | Notes |
| :--- | :--- |
| ![CI](https://img.shields.io/badge/CI-2e7d32?style=flat-square&logoColor=white) **EXE** x64 | `Save4Bucks-x64.exe` on GitHub Releases |
| ![CI](https://img.shields.io/badge/CI-2e7d32?style=flat-square&logoColor=white) **EXE** x86 | `Save4Bucks-x86.exe` on GitHub Releases |

Latest: [Releases](https://github.com/Metaheurist/4bucks/releases) · [Actions](https://github.com/Metaheurist/4bucks/actions)

<!-- SAVE4BUCKS_BUILD_INFO_END -->

---

### Documentation

Long-form sections live under **`docs/`** so the main README stays short. Open them from the repo’s file tree or use the links below. Icons are SVG assets under [`docs/icons/`](docs/icons/) (referenced with `<img>` for GitHub compatibility).

| | |
| :--- | :--- |
| <img src="docs/icons/lock.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Security](docs/SECURITY.md)** - offline threat model, CVE gates, what we do not do |
| <img src="docs/icons/home.svg" width="32" height="32" alt="" aria-hidden="true"> | **[App overview & features](docs/app-and-features.md)** - UI flow, autobackup, save slots, CLI |
| <img src="docs/icons/settings.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Installation & usage](docs/setup-and-usage.md)** - venv, run from source, dual-arch EXE build |
| <img src="docs/icons/flask.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Testing & configuration](docs/testing-and-configuration.md)** - pytest, pip-audit, manual checklist |
| <img src="docs/icons/timer.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Build, test & CI](docs/build-test-and-ci.md)** - `build.ps1`, Actions, SemVer releases |
| <img src="docs/icons/folder.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Architecture](docs/architecture.md)** - module map and write path |
| <img src="docs/icons/clipboard.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Save format](docs/save-format.md)** - BLOCK / money offsets |
| <img src="docs/icons/shield.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Savegame versioning](docs/versioning.md)** - allowlist / refuse rules (CE v57) |
| <img src="docs/icons/paperclip.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Known issues](docs/known-issues.md)** - OneDrive, autosave episodes, Steam pitfalls |
| <img src="docs/icons/brain.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Research notes](docs/research.md)** - GTAMods / GTASnP / forum sources |
| <img src="docs/icons/folder.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Project reference](docs/project-reference.md)** - tree, deps, troubleshooting |
| <img src="docs/icons/scroll.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Changelog](docs/CHANGELOG.md)** - version history and release notes |
| <img src="docs/icons/rocket.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Next phase plan](docs/next-phase-development-plan.md)** - upcoming improvements |
| <img src="docs/icons/user.svg" width="32" height="32" alt="" aria-hidden="true"> | **[About & support](docs/about-and-support.md)** |

Supported saves: CE with `SAVEGAME_VERSION_NUMBER` **57** (e.g. `1.2.0.59`). Close **GTAIV.exe** before writing.

---

## App icons

Master rasters live under **`assets/`** (`icon.png`, **`icon.ico`**). The frozen EXE and window title use `icon.ico` (generated from PNG by `build.ps1` if missing).

---

## Security

The authoritative guide is **[docs/SECURITY.md](docs/SECURITY.md)** (offline threat model, dependency audits, privileges). Root [`SECURITY.md`](SECURITY.md) is a short pointer for GitHub’s security tab convention.
