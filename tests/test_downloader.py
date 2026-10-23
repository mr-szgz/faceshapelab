import hashlib
import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest
import requests

import download_face_models as downloader
from faceshapelab.face_analysis.detection import MODELS as DETECTORS
from faceshapelab.face_analysis.landmarks import HEAD_MODEL
from faceshapelab.face_analysis.landmarks import MODELS as LANDMARKS
from faceshapelab.face_analysis.recognition import MODELS as RECOGNIZERS


class Response:
    def __init__(self, content=b"model", status=200):
        self.content, self.status = content, status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def raise_for_status(self):
        if self.status != 200:
            raise requests.HTTPError(str(self.status))

    def iter_content(self, chunk_size):
        yield self.content[:2]
        yield self.content[2:]


def test_manifest_covers_only_required_models():
    required = (
        set(DETECTORS.values()) | set(LANDMARKS.values()) | set(RECOGNIZERS.values())
    )
    required |= {HEAD_MODEL, "face_blendshapes_Nx146x2.onnx", "cscs_id_adapter.onnx"}
    assert {spec[0] for spec in downloader.MODELS.values()} == required
    assert len(downloader.MODELS) == 22
    assert all("VR" not in name for name in downloader.MODELS)


def test_download_streams_and_reports_digest(tmp_path, capsys):
    digest = hashlib.sha256(b"model").hexdigest()
    with (
        patch.object(
            downloader,
            "MODELS",
            {"test": ("model.onnx", "https://example.org/model", digest)},
        ),
        patch.object(downloader.requests, "get", return_value=Response()) as get,
    ):
        downloader.download_models(tmp_path / "assets")
    assert (tmp_path / "assets/model.onnx").read_bytes() == b"model"
    assert digest in capsys.readouterr().out
    get.assert_called_once_with("https://example.org/model", stream=True, timeout=10)


def test_http_failure_is_not_retried(tmp_path):
    with (
        patch.object(
            downloader,
            "MODELS",
            {"test": ("model.onnx", "https://example.org/missing", "hash")},
        ),
        patch.object(
            downloader.requests, "get", return_value=Response(status=404)
        ) as get,
        pytest.raises(requests.HTTPError),
    ):
        downloader.download_models(tmp_path)
    get.assert_called_once()
    assert not list(tmp_path.iterdir())


def test_existing_file_is_not_overwritten(tmp_path):
    destination = tmp_path / "model.onnx"
    destination.write_bytes(b"existing")
    with (
        patch.object(
            downloader,
            "MODELS",
            {"test": ("model.onnx", "https://example.org/model", "hash")},
        ),
        patch.object(downloader.requests, "get", return_value=Response()),
        pytest.raises(FileExistsError),
    ):
        downloader.download_models(tmp_path)
    assert destination.read_bytes() == b"existing"


def test_standalone_import_has_no_application_or_filesystem_dependency(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    spec = importlib.util.spec_from_file_location(
        "standalone_download", Path(downloader.__file__)
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert len(module.MODELS) == 22
    assert list(tmp_path.iterdir()) == []
