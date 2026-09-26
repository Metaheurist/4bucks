# Save 4Bucks

Offline Windows editor for Grand Theft Auto IV **Complete Edition** `SGTA4xx` saves. Edits PlayerInfo fields only: cash, weapons/ammo, health, armour, and maxima. No process memory, injection, or live trainers.

**Changelog:** [CHANGELOG.md](CHANGELOG.md) · **Releases:** [GitHub Releases](https://github.com/Metaheurist/4bucks/releases)

### Roadmap

[docs/next-phase-development-plan.md](docs/next-phase-development-plan.md)

### Tech stack

<table>
<tr>
<td valign="middle" width="140">
<img src="docs/icons/core.svg" width="28" height="28" alt="" aria-hidden="true">&nbsp;<b>Core</b>
</td>
<td>

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flet](https://img.shields.io/badge/UI-Flet%201.0.1%20(Flutter)-02569B?style=flat-square&logo=flutter&logoColor=white)](https://flet.dev/)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?style=flat-square&logo=windows&logoColor=white)](https://www.microsoft.com/windows)

</td>
</tr>
<tr>
<td valign="middle" width="140">
<img src="docs/icons/package.svg" width="28" height="28" alt="" aria-hidden="true">&nbsp;<b>Packaging</b>
</td>
<td>

[![Flet pack](https://img.shields.io/badge/flet%20pack-PyInstaller-000000?style=flat-square)](https://flet.dev/)
[![x64](https://img.shields.io/badge/EXE-x64-2e7d32?style=flat-square)](docs/build-test-and-ci.md)
[![x86](https://img.shields.io/badge/EXE-x86-2e7d32?style=flat-square)](docs/build-test-and-ci.md)

</td>
</tr>
<tr>
<td valign="middle" width="140">
<img src="docs/icons/tools.svg" width="28" height="28" alt="" aria-hidden="true">&nbsp;<b>Tooling &amp; CI</b>
</td>
<td>

[![pytest](https://img.shields.io/badge/pytest-9.0.3-0A9EDC?style=flat-square&logo=pytest&logoColor=white)](https://pytest.org/)
[![pip-audit](https://img.shields.io/badge/pip--audit-2.9.0-CB3837?style=flat-square)](https://pypi.org/project/pip-audit/)
[![Gitleaks](https://img.shields.io/badge/Gitleaks-secret%20scan-1E2E3E?style=flat-square)](https://github.com/gitleaks/gitleaks)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-CI-2088FF?style=flat-square&logo=githubactions&logoColor=white)](https://github.com/Metaheurist/4bucks/actions)

</td>
</tr>
</table>

**Repository:** [github.com/Metaheurist/4bucks](https://github.com/Metaheurist/4bucks)

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

| | |
| :--- | :--- |
| <img src="docs/icons/lock.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Security](docs/SECURITY.md)** - threat model, CVE gates, out of scope |
| <img src="docs/icons/home.svg" width="32" height="32" alt="" aria-hidden="true"> | **[App overview & features](docs/app-and-features.md)** - views, autobackup, CLI |
| <img src="docs/icons/settings.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Installation & usage](docs/setup-and-usage.md)** - source run, dual-arch build |
| <img src="docs/icons/flask.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Testing & configuration](docs/testing-and-configuration.md)** - pytest, pip-audit |
| <img src="docs/icons/timer.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Build, test & CI](docs/build-test-and-ci.md)** - `build.ps1`, Actions, SemVer |
| <img src="docs/icons/folder.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Architecture](docs/architecture.md)** - module map and write path |
| <img src="docs/icons/clipboard.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Save format](docs/save-format.md)** - PlayerInfo offsets |
| <img src="docs/icons/shield.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Savegame versioning](docs/versioning.md)** - allowlist and write techniques |
| <img src="docs/icons/paperclip.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Known issues](docs/known-issues.md)** - OneDrive, autosave, peers |
| <img src="docs/icons/brain.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Research notes](docs/research.md)** - public sources and local dumps |
| <img src="docs/icons/folder.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Project reference](docs/project-reference.md)** - tree and dependencies |
| <img src="docs/icons/scroll.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Changelog](docs/CHANGELOG.md)** |
| <img src="docs/icons/rocket.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Roadmap](docs/next-phase-development-plan.md)** |
| <img src="docs/icons/user.svg" width="32" height="32" alt="" aria-hidden="true"> | **[About & support](docs/about-and-support.md)** |
| <img src="docs/icons/paperclip.svg" width="32" height="32" alt="" aria-hidden="true"> | **[Contributing](CONTRIBUTING.md)** |

Supported saves: `SAVEGAME_VERSION_NUMBER` **57** (CE 1.2.0.32 / 1.2.0.43+ / 1.2.0.59 and matching pre-CE samples; see [versioning](docs/versioning.md)). Close **GTAIV.exe** before writing.

---

## App icons

Rasters under **`assets/`** (`icon.png`, `icon.ico`). The EXE and window use `icon.ico` (generated from PNG by `build.ps1` if missing).

---

## Security

Authoritative guide: **[docs/SECURITY.md](docs/SECURITY.md)**. Root [`SECURITY.md`](SECURITY.md) points GitHub's security tab at that file.
