# Online installer verification

## 0.2.0 release verification — 2026-10-23

- Built `dist/FaceShapeLab-0.2.0-Setup.exe` with Inno Setup 6.7.3; 2,685,858 bytes.
- SHA-256: `cfa8cddebd611a23705ab780ee81e7d99a4b791f1f909b1fc4b221f946771fbe`.
- The installer is unsigned. Its version metadata is 0.2.0.
- Includes automatic aligned Face previews and coordinate-correct annotations in both views.
- Full source suite: 102 tests and 2 subtests passed; the additional mixed accepted/rejected landmark test also passed.
- Verified Original/Face switching, automatic selection after both detection actions, multiple-face selection, rejected landmarks, no-face results, replaced video frames, and clean saved crops.
- Visually inspected original and aligned face overlays in light and dark themes.
- Ruff, Python compilation, `uv lock --check`, and whitespace checks passed.
- Compiled-installer failure checks passed: missing CUDA aborts before downloads; dependency exit 37 aborts Setup with exit 3.
- Fresh silent installation into `.work/release 0.2.0 app` completed with exit 0, downloading private Python, 38 production packages, and all 22 models.
- All installed model hashes match; all 4 detectors, 11 landmark modes, and 4 recognizers match upstream reference outputs on CUDA.
- Installed GUI launch and automatic aligned previews passed for both panels, with Original/Face annotations checked in light and dark themes.
- Silent uninstall exited 0, removed the app, private Python/venv, and models, and preserved the user-created file.
- Installed Python and package imports resolve under the installation directory; no development packages are installed.
- Installed application source and metadata match the staged release snapshot. Concurrent file-browser edits made after the build are excluded from this release.
- Local evidence: `.work/release-0.2.0-build.log`, `.work/release-0.2.0-install.log`, `.work/release-0.2.0-model-check.log`, `.work/release-0.2.0-preview-check.log`, and `.work/release-preview-*.png`.
- Verification ran on the current Windows host, not a clean Windows VM. Prior 0.1.0 reinstall coverage is recorded below.

## Historical 0.1.0 installer verification

Verified on 2026-10-23 on the current Windows x64 host.

## Artifact

- `dist/FaceShapeLab-0.1.0-Setup.exe`: **2,685,149 bytes** (2.69 MB).
- SHA-256: `3b8dfa10eb42093a9ecc0b4fbdec080991aac9d9281672fa935dc1747266bb8a`.
- Compiled with Inno Setup 6.7.3, without warnings. The executable is unsigned.
- Built at 13:32 Toronto time. Concurrent edits to the application UI and analysis
  worker appeared after 13:41, during verification. Those edits were left untouched
  and are not included in this tested executable. The build script includes the
  working-tree source present whenever it is next run.
- Embedded payload: application Python/UI source, lockfile, license, README, and
  setup/verification scripts. No Python runtime, venv, wheels, or model files are
  embedded.

## Verified behavior

| Check | Result |
| --- | --- |
| Missing toolkit at `CUDA_PATH` | Setup exits 1 before downloads or app installation. |
| Dependency command deliberately exits 37 | Setup exits 3 before application files or shortcuts are installed. |
| Fresh silent installation into a directory containing spaces | Passed; downloaded private Python 3.12.10, installed 38 production packages, and downloaded all 22 models. |
| Environment isolation | Python executable and base interpreter both reside under the installation directory; installed application imports resolve there. No pytest, Ruff, or development `onnx` package is installed. |
| Model integrity | All 22 installed SHA-256 hashes match the source manifest; total model size is 2,143,007,521 bytes. |
| Actual CUDA inference | All 4 detectors, 11 landmark modes, and 4 recognizers match the repository's upstream reference outputs. |
| GUI | Installed Qt window opened, processed its event loop, and closed successfully. |
| Start menu shortcut | Targets the installed venv's `pythonw.exe` and `launch.pyw`, with the user's Documents directory as working directory. |
| Same-version reinstall | Passed using the final release executable; reused the private Python/venv, refreshed model downloads, and passed the post-install Qt/CUDA model-session smoke test. |
| Silent uninstall | Removed the application, private Python, venv, and models. Preserved a deliberately created user file. |
| Source checks | `ruff check packaging` and `git diff --check` passed. |

`CUDA_PATH` explicitly selected the existing CUDA 13.0 toolkit. PyTorch
2.10.0+cu128 used its bundled CUDA 12.8 runtime on the NVIDIA GeForce RTX 3090.
Setup contains no system CUDA/driver installation, environment-variable persistence,
or system PATH changes. It does not search for alternative toolkits.

Dependency setup executes at Inno's `ssInstall` event. Failure injection confirmed
that a nonzero child exit terminates Setup, including `/VERYSILENT` execution.
The implementation does not use file callbacks for failure propagation, since
Inno catches exceptions from those callbacks and may continue installation.

## Reproduction and evidence

Build and failure-check commands are in the root README. The repeatable failure
checks are in `packaging/verify_failure_paths.py`; an installed copy includes
`verify_runtime.py` for the application/CUDA model-session smoke test.

Local evidence from this run (ignored by Git):

- `.work/build.log`
- `.work/final-install.log`
- `.work/installed-runtime-test.log`
- `.work/verify_installed.py` (full installed-model reference comparison)
- `.work/dependency-failure.log`
- `.work/upgrade.log`
- `.work/uninstall.log`

The fresh-install test used a new app directory, no package cache, and freshly
downloaded models. It ran on this existing Windows host, not a clean Windows VM.
The wizard was tested silently; no prior production release was available, so the
upgrade check was a same-version reinstall.

## Test-artifact cleanup limitation

Automatic approval review rejected cleanup of the following artifacts from a
superseded test with the reason **"blocked by policy"**; no more detailed reason
was supplied. They were left in place:

- `C:\Users\shoji\AppData\Local\Temp\.tmpkCWpj2` — interrupted test's uv download cache.
- `S:\Spaces\Image-Reconstruction\.work\release\FaceShapeLab-0.1.0-Setup.exe` — extra test build outside this repository.

The actual installed test copies were uninstalled successfully. These residual
test artifacts are not part of the installer payload or its normal installation.
