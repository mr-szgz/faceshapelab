"""Real CUDA regression tests against the pinned upstream successful paths."""

import hashlib
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
import pytest
import torch
from PIL import Image

from download_face_models import MODELS as ASSETS
from faceshapelab.face_analysis import geometry as g
from faceshapelab.face_analysis.detection import MODELS as DETECTORS
from faceshapelab.face_analysis.detection import FaceDetector
from faceshapelab.face_analysis.landmarks import MODELS as LANDMARKS
from faceshapelab.face_analysis.landmarks import (
    POINT_COUNTS,
    LandmarkDetector,
    match_head,
)
from faceshapelab.face_analysis.recognition import MODELS as RECOGNIZERS
from faceshapelab.face_analysis.recognition import (
    FaceRecognizer,
    aligned_crop,
    similarity,
)
from faceshapelab.face_analysis.runtime import Runtime

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def runtime():
    return Runtime(ROOT / "model_assets")


@pytest.fixture(scope="module")
def image(runtime):
    pixels = np.array(Image.open(FIXTURES / "astronaut.png"))
    return torch.from_numpy(pixels).permute(2, 0, 1).to(runtime.device).contiguous()


@pytest.fixture(scope="module")
def reference():
    with np.load(FIXTURES / "upstream_reference.npz") as data:
        return dict(data)


@pytest.mark.models
@pytest.mark.parametrize("name", ASSETS)
def test_model_hash(name):
    filename, _, expected = ASSETS[name]
    with (ROOT / "model_assets" / filename).open("rb") as stream:
        assert hashlib.file_digest(stream, "sha256").hexdigest() == expected


@pytest.mark.models
@pytest.mark.parametrize("mode", DETECTORS)
def test_detector_upstream_parity(runtime, image, reference, mode):
    result = FaceDetector(runtime, mode).detect(image)
    np.testing.assert_allclose(result.boxes, reference[mode + "_boxes"], atol=0.02)
    np.testing.assert_allclose(result.points5, reference[mode + "_points"], atol=0.02)
    np.testing.assert_allclose(result.scores, reference[mode + "_scores"], atol=1e-4)
    assert (
        runtime.session(DETECTORS[mode]).get_providers()[0] == "CUDAExecutionProvider"
    )
    runtime.sessions.clear()


@pytest.mark.models
@pytest.mark.parametrize("mode", LANDMARKS)
def test_landmarks_upstream_parity(runtime, image, reference, mode):
    result = LandmarkDetector(runtime, mode).detect(
        image, reference["RetinaFace_boxes"][0], reference["RetinaFace_points"][0]
    )
    assert result is not None
    assert result.points.shape == (POINT_COUNTS[mode], 2)
    np.testing.assert_allclose(result.points, reference["land_" + mode], atol=0.05)
    np.testing.assert_allclose(result.points5, reference["p5_" + mode], atol=0.05)
    if mode == "478":
        assert result.confidence is None and result.blendshapes.shape == (52,)
    if mode == "orformer98":
        assert result.confidence is None and result.visibility.shape == (98,)
    runtime.sessions.clear()


@pytest.mark.models
@pytest.mark.parametrize("mode", RECOGNIZERS)
def test_recognition_upstream_parity(runtime, image, reference, mode):
    result = FaceRecognizer(runtime, mode).recognize(
        image, reference["RetinaFace_points"][0]
    )
    assert result.embedding.shape == (512,)
    np.testing.assert_allclose(
        result.embedding, reference["embedding_" + mode], atol=2e-4, rtol=2e-4
    )
    np.testing.assert_array_equal(result.crop, reference["crop_" + mode])
    assert similarity(result.embedding, result.embedding) == pytest.approx(
        100, abs=1e-4
    )
    runtime.sessions.clear()


@pytest.mark.models
@pytest.mark.parametrize("mode", DETECTORS)
def test_empty_image(runtime, mode):
    result = FaceDetector(runtime, mode).detect(
        torch.zeros((3, 250, 430), dtype=torch.uint8, device=runtime.device)
    )
    assert result.boxes.shape == (0, 4)
    assert result.points5.shape == (0, 5, 2)
    assert result.scores.shape == (0,)


@pytest.mark.models
@pytest.mark.parametrize("mode", DETECTORS)
def test_multiple_faces_and_limit(runtime, image, mode):
    doubled = torch.cat((image, image), dim=2)
    result = FaceDetector(runtime, mode).detect(doubled)
    assert len(result.boxes) == 2
    order = np.argsort(result.boxes[:, 0])
    np.testing.assert_allclose(
        result.points5[order[1]] - [512, 0], result.points5[order[0]], atol=3
    )
    limited = FaceDetector(runtime, mode).detect(doubled, max_faces=1)
    assert len(limited.boxes) == 1
    assert len(FaceDetector(runtime, mode).detect(image, score_threshold=1).boxes) == 0
    runtime.sessions.clear()


@pytest.mark.models
@pytest.mark.parametrize("angle", [90, 180, 270])
def test_single_rotation_inverse_maps_keypoints(runtime, image, angle):
    rotated = torch.rot90(image, angle // 90, (1, 2)).contiguous()
    result = FaceDetector(runtime).detect(rotated, rotation_angles=(angle,))
    assert len(result.boxes) == 1
    points = result.points5[0]
    assert np.isfinite(points).all()
    assert (points >= result.boxes[0, :2] - 1).all()
    assert (points <= result.boxes[0, 2:] + 1).all()


@pytest.mark.models
@pytest.mark.parametrize("mode", ["5", "68", "3d68", "98", "106", "203", "478"])
def test_landmark_from_points(runtime, image, reference, mode):
    result = LandmarkDetector(runtime, mode).detect(
        image,
        reference["RetinaFace_boxes"][0],
        reference["RetinaFace_points"][0],
        from_points=True,
        score_threshold=0.01,
    )
    assert result is not None
    assert np.isfinite(result.points).all()
    assert result.points.shape == (POINT_COUNTS[mode], 2)
    np.testing.assert_allclose(result.points5, reference["p5_" + mode], atol=20)
    runtime.sessions.clear()


@pytest.mark.models
def test_confidence_is_not_visibility_or_blendshapes(runtime, image, reference):
    box, pts = reference["RetinaFace_boxes"][0], reference["RetinaFace_points"][0]
    assert (
        LandmarkDetector(runtime, "5").detect(image, box, pts, score_threshold=1)
        is None
    )
    for mode in ("478", "orformer98", "hrffa"):
        assert (
            LandmarkDetector(runtime, mode).detect(image, box, pts, score_threshold=1)
            is not None
        )
    runtime.sessions.clear()


@pytest.mark.models
def test_missing_model_and_invalid_input_propagate(runtime):
    with pytest.raises(Exception, match="missing.onnx"):
        runtime.session("missing.onnx")
    tensor = torch.zeros((1, 3, 10, 10), device=runtime.device)
    with pytest.raises(Exception, match="dimensions|Got invalid"):
        runtime.run("yoloface_8n.onnx", {"images": tensor}, ["output0"])


def test_arcface128_offsets_every_x_coordinate_only():
    points = g.arcface_src[0].copy()
    points[:, 0] += 8
    matrix, _ = g.estimate_norm(points, 128, "arcface128")
    np.testing.assert_allclose(matrix, [[1, 0, 0], [0, 1, 0]], atol=2e-5)


def test_detections_outside_source_are_excluded():
    centers = np.array([[-60, 50], [700, 50], [50, -60], [50, 700], [5, 50]])
    raw = np.zeros((1, 20, len(centers)), dtype=np.float32)
    raw[0, :2] = centers.T
    raw[0, 2:4] = 40
    raw[0, 4] = 0.9
    for index in range(5):
        raw[0, 5 + index * 3 : 7 + index * 3] = centers.T
    session = SimpleNamespace(
        get_inputs=lambda: [SimpleNamespace(name="images")],
        get_outputs=lambda: [SimpleNamespace(name="output0")],
    )
    runtime = SimpleNamespace(
        device="cpu", session=lambda filename: session, run=lambda *args: [raw]
    )
    result = FaceDetector(runtime, "Yolov8").detect(
        torch.zeros((3, 640, 640), dtype=torch.uint8)
    )
    np.testing.assert_array_equal(result.boxes, [[-15, 30, 25, 70]])


def test_coordinate_roundtrip():
    points = np.array([[1, 2], [30, 90], [-4, 8]], dtype=np.float32)
    matrix = np.array([[1.2, -0.3, 15], [0.3, 1.2, -21]])
    restored = g.trans_points2d(
        g.trans_points2d(points, matrix), g.invertAffineTransform(matrix)
    )
    np.testing.assert_allclose(restored, points, atol=1e-5)


def test_dark_crop_preserves_byte_luminance_scale():
    pixels = np.full((256, 256, 3), 20, dtype=np.uint8)
    crop, _ = g.warp_face_by_bounding_box_for_landmark_68(
        torch.from_numpy(pixels).permute(2, 0, 1),
        np.array([30.5, 30.5, 225.5, 225.5]),
        (256, 256),
    )
    lab = cv2.cvtColor(pixels, cv2.COLOR_RGB2Lab)
    lab[:, :, 0] = cv2.createCLAHE(clipLimit=2).apply(lab[:, :, 0])
    expected = cv2.cvtColor(lab, cv2.COLOR_Lab2RGB)
    np.testing.assert_allclose(crop.permute(1, 2, 0).numpy(), expected, atol=2)


def test_head_matching_no_synthetic_box():
    face = np.array([20, 30, 60, 70])
    assert match_head(np.empty((0, 5)), face) is None
    heads = np.array([[0, 0, 80, 100, 0.9], [200, 0, 280, 100, 0.99]])
    np.testing.assert_array_equal(match_head(heads, face), heads[0, :4])


@pytest.mark.models
def test_aligned_crop_roundtrip(runtime, image, reference):
    crop = aligned_crop(image, reference["RetinaFace_points"][0])
    assert crop.shape == (512, 512, 3) and crop.dtype == np.uint8
    assert crop.std() > 30
    result = FaceDetector(runtime, "Yunet").detect(
        torch.from_numpy(crop).permute(2, 0, 1).to(runtime.device).contiguous()
    )
    assert len(result.boxes) == 1
    assert abs(result.points5[0, 0, 1] - result.points5[0, 1, 1]) < 12
