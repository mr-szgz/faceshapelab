"""Build the online installer with Python 3.12+ and Inno Setup 6.5+."""

import ast
import json
import subprocess
import sys
import tomllib
from pathlib import Path

root = Path(__file__).resolve().parents[1]
build = root / "build" / "installer"
build.mkdir(parents=True, exist_ok=True)
project = tomllib.loads((root / "pyproject.toml").read_text())
manifest = next(
    ast.literal_eval(node.value)
    for node in ast.parse((root / "download_face_models.py").read_text()).body
    if isinstance(node, ast.Assign)
    and any(
        isinstance(target, ast.Name) and target.id == "MODELS"
        for target in node.targets
    )
)
sizes = json.loads((root / "packaging" / "model-sizes.json").read_text())
entries = [
    f'Source: "{url}"; DestDir: "{{app}}\\model_assets"; DestName: "{filename}"; '
    f'ExternalSize: {sizes[filename]}; Hash: "{digest}"; '
    "Flags: external download ignoreversion"
    for filename, url, digest in manifest.values()
]
(build / "models.iss").write_text("\n".join(entries) + "\n")
subprocess.run(
    [
        sys.argv[1],
        f"/DAppVersion={project['project']['version']}",
        str(root / "packaging" / "installer.iss"),
    ],
    check=True,
)
