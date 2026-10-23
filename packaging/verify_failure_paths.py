"""Check real Inno Setup failure exits. Pass ISCC.exe and the built setup EXE."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
compiler, installer = sys.argv[1:]
installer = str(Path(installer).resolve())
flags = ["/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"]

with tempfile.TemporaryDirectory(prefix="FaceShapeLab-installer-test-") as directory:
    work = Path(directory)
    missing_log = work / "missing-cuda.log"
    result = subprocess.run(
        [installer, *flags, f"/DIR={work / 'missing app'}", f"/LOG={missing_log}"],
        env=dict(os.environ, CUDA_PATH=str(work / "missing-cuda")),
        check=False,
    )
    assert result.returncode != 0
    assert not (work / "missing app").exists()
    log = missing_log.read_text(encoding="utf-8-sig")
    assert "CUDA_PATH toolkit check failed" in log
    assert "Downloading" not in log
    print("Missing CUDA toolkit aborts before downloads.")

    # Substitute only the dependency command; execute the real failure checks.
    (work / "bootstrap.cmd").write_text("@echo off\nexit /b 37\n")
    source = (root / "packaging" / "installer.iss").read_text()
    source = source.replace(
        "[Setup]", f"[Setup]\nSourceDir={root / 'packaging'}"
    ).replace(
        "B79C28DE-4238-41B3-A058-8896850F7A63",
        "5A04248D-47D5-4BA2-B920-CA88AEFE3E05",
    )
    source = source.replace("OutputDir=..\\dist", f"OutputDir={work}")
    source = source.replace(
        "OutputBaseFilename=FaceShapeLab-{#AppVersion}-Setup",
        "OutputBaseFilename=failure-test",
    )
    source = source.replace(
        'Source: "bootstrap.cmd";', f'Source: "{work / "bootstrap.cmd"}";'
    )
    source = "\n".join(
        line for line in source.splitlines() if not line.startswith("#include")
    )
    script = work / "failure.iss"
    script.write_text(source)
    subprocess.run([compiler, "/Q", "/DAppVersion=0.1.0", str(script)], check=True)
    failure_log = work / "dependency-failure.log"
    result = subprocess.run(
        [
            str(work / "failure-test.exe"),
            *flags,
            f"/DIR={work / 'failed app'}",
            f"/LOG={failure_log}",
        ],
        check=False,
    )
    assert result.returncode != 0
    assert not (work / "failed app" / "launch.pyw").exists()
    log = failure_log.read_text(encoding="utf-8-sig")
    assert "exited with code 37" in log
    assert "Installation process succeeded" not in log
    print(f"Dependency exit 37 aborts setup (exit {result.returncode}).")
