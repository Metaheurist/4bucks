# Building Save 4Bucks

Build and CI documentation moved to:

- **[docs/setup-and-usage.md](docs/setup-and-usage.md)** - install, run from source (Flet), one-shot `build.ps1`
- **[docs/build-test-and-ci.md](docs/build-test-and-ci.md)** - dual-arch `flet pack`, Actions, SemVer releases

Quick build:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
# -> dist\Save4Bucks-x64.exe and dist\Save4Bucks-x86.exe
```
