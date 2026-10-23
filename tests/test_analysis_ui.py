from pathlib import Path
from time import sleep
from types import SimpleNamespace
from unittest.mock import patch

import av
import numpy as np
import pytest
from PIL import Image
from PySide6.QtCore import QSettings, Qt, QUrl
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import QVideoFrame
from PySide6.QtWidgets import QApplication

from faceshapelab.analysis_worker import image_array
from faceshapelab.main import MainWindow

FIXTURE = Path(__file__).parent / "fixtures/astronaut.png"


@pytest.fixture
def window(tmp_path):
    app = QApplication.instance() or QApplication([])
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    with (
        patch("faceshapelab.main.QSettings", return_value=settings),
        patch(
            "faceshapelab.thumbnails.user_cache_path", return_value=tmp_path / "cache"
        ),
    ):
        widget = MainWindow()
        widget.ui.outputFolderPath.setText(str(tmp_path))
        widget.show()
        app.processEvents()
        yield widget
        widget.close()


def wait_idle(window):
    for _ in range(12000):
        QApplication.processEvents()
        if not window.analysis_busy and not window.analysis_worker.isRunning():
            return
        sleep(0.01)
    pytest.fail("Analysis worker did not finish")


def load(window, panel):
    window.load_media(panel, QUrl.fromLocalFile(str(FIXTURE.resolve())), True)


@pytest.mark.models
def test_real_buttons_detect_landmark_save_compare(window, tmp_path):
    assert not window.ui.leftDetectFacesButton.isEnabled()
    for side in ("left", "right"):
        panel = getattr(window.ui, side + "Panel")
        load(window, panel)
        getattr(window.ui, side + "DetectFacesButton").click()
        assert window.analysis_busy
        assert not window.ui.compareFacesButton.isEnabled()
        wait_idle(window)
        selection = getattr(window.ui, side + "SelectedFaceComboBox")
        assert selection.count() == 1
        assert getattr(window.ui, side + "PreviewModeComboBox").currentText() == "Face"
        getattr(window.ui, side + "PreviewModeComboBox").setCurrentText("Original")
        assert getattr(window.ui, side + "SaveFaceButton").isEnabled()
        getattr(window.ui, side + "DetectLandmarksButton").click()
        wait_idle(window)
        assert window.face_results[panel][2][0].points.shape == (203, 2)
        assert getattr(window.ui, side + "PreviewModeComboBox").currentText() == "Face"
    for side in ("left", "right"):
        panel = getattr(window.ui, side + "Panel")
        label = getattr(window.ui, side + "Image")
        mode = getattr(window.ui, side + "PreviewModeComboBox")
        mode.setCurrentText("Original")
        original = image_array(label.pixmap().toImage())
        mode.setCurrentText("Face")
        expected = window.face_previews[panel][0].scaled(
            label.contentsRect().size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        np.testing.assert_array_equal(
            image_array(label.pixmap().toImage()), image_array(expected.toImage())
        )
        mode.setCurrentText("Original")
        np.testing.assert_array_equal(image_array(label.pixmap().toImage()), original)
    before = image_array(window.image_pixmaps[window.ui.leftImage].toImage())
    window.ui.showBoundingBoxesCheckBox.setChecked(True)
    window.ui.showLandmarksCheckBox.setChecked(True)
    np.testing.assert_array_equal(
        before, image_array(window.image_pixmaps[window.ui.leftImage].toImage())
    )
    window.ui.leftSaveFaceButton.click()
    raw = list(tmp_path.glob("face_*.png"))
    assert len(raw) == 1
    with Image.open(raw[0]) as crop:
        assert 80 < crop.width < 110 and 100 < crop.height < 140
    window.ui.leftSaveCroppedFaceButton.click()
    wait_idle(window)
    aligned = list(tmp_path.glob("aligned_*.png"))
    assert len(aligned) == 1
    with Image.open(aligned[0]) as crop:
        assert crop.size == (512, 512)
        np.testing.assert_array_equal(
            np.array(crop),
            image_array(window.face_previews[window.ui.leftPanel][0].toImage()),
        )
    window.ui.compareFacesButton.click()
    wait_idle(window)
    assert window.ui.embeddingComparisonTable.item(0, 1).data(Qt.ItemDataRole.DisplayRole) == pytest.approx(1)


@pytest.mark.models
def test_video_frame_analysis_and_stale_result(window):
    panel = window.ui.leftPanel
    image = QImage(str(FIXTURE))
    window.display_frame(panel, QVideoFrame(image))
    window.ui.leftDetectFacesButton.click()
    wait_idle(window)
    assert len(window.face_results[panel][1].boxes) == 1
    window.ui.leftDetectLandmarksButton.click()
    # A new frame invalidates both the selection and the pending result.
    replacement = QImage(400, 300, QImage.Format.Format_RGB32)
    replacement.fill(0)
    window.display_frame(panel, QVideoFrame(replacement))
    wait_idle(window)
    assert panel not in window.face_results
    assert window.ui.leftSelectedFaceComboBox.count() == 0
    assert not window.ui.leftSaveFaceButton.isEnabled()
    assert "discarded" in window.statusBar().currentMessage()


@pytest.mark.models
def test_multiple_face_selection_and_no_face_state(window):
    image = np.array(Image.open(FIXTURE))
    pixels = np.concatenate((image, image), axis=1)
    qimage = QImage(
        pixels.data,
        pixels.shape[1],
        pixels.shape[0],
        pixels.strides[0],
        QImage.Format.Format_RGB888,
    ).copy()
    window.display_frame(window.ui.leftPanel, QVideoFrame(qimage))
    window.ui.leftDetectFacesButton.click()
    wait_idle(window)
    assert window.ui.leftSelectedFaceComboBox.count() == 2
    window.ui.leftPreviewModeComboBox.setCurrentText("Face")
    window.ui.leftSelectedFaceComboBox.setCurrentIndex(1)
    expected = window.face_previews[window.ui.leftPanel][1].scaled(
        window.ui.leftImage.contentsRect().size(),
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    np.testing.assert_array_equal(
        image_array(window.ui.leftImage.pixmap().toImage()),
        image_array(expected.toImage()),
    )
    np.testing.assert_allclose(
        window.selected_points(window.ui.leftPanel),
        window.face_results[window.ui.leftPanel][1].points5[1],
    )
    blank = QImage(512, 512, QImage.Format.Format_RGB32)
    blank.fill(0)
    window.display_frame(window.ui.leftPanel, QVideoFrame(blank))
    window.ui.leftDetectFacesButton.click()
    wait_idle(window)
    assert "0 face(s)" in window.statusBar().currentMessage()
    assert window.ui.leftPreviewModeComboBox.currentText() == "Original"
    assert not window.ui.leftPreviewModeComboBox.model().item(1).isEnabled()
    assert not window.ui.leftSaveCroppedFaceButton.isEnabled()


@pytest.mark.models
def test_comparison_discards_replaced_right_image(window):
    for panel in (window.ui.leftPanel, window.ui.rightPanel):
        load(window, panel)
        window.start_analysis(panel, "detect")
        wait_idle(window)
    window.ui.compareFacesButton.click()
    load(window, window.ui.rightPanel)
    wait_idle(window)
    assert "discarded" in window.statusBar().currentMessage()
    assert not window.ui.compareFacesButton.isEnabled()


@pytest.mark.models
def test_rejected_landmarks_disable_alignment_and_comparison(window):
    load(window, window.ui.leftPanel)
    window.ui.landmarkDetectModelComboBox.setCurrentText("5")
    window.ui.landmarkDetectScoreSlider.setValue(100)
    window.ui.leftDetectLandmarksButton.click()
    wait_idle(window)
    assert window.face_results[window.ui.leftPanel][2] == [None]
    assert window.ui.leftSaveFaceButton.isEnabled()
    assert not window.ui.leftSaveCroppedFaceButton.isEnabled()
    assert not window.ui.compareFacesButton.isEnabled()
    assert window.ui.leftPreviewModeComboBox.currentText() == "Original"
    assert not window.ui.leftPreviewModeComboBox.model().item(1).isEnabled()


@pytest.mark.models
def test_close_during_crop_does_not_save_queued_result(window, tmp_path):
    load(window, window.ui.leftPanel)
    window.ui.leftDetectFacesButton.click()
    wait_idle(window)
    window.ui.leftSaveCroppedFaceButton.click()
    window.close()
    QApplication.processEvents()
    assert not window.analysis_worker.isRunning()
    assert not list(tmp_path.glob("aligned_*.png"))


@pytest.mark.models
def test_decoded_video_frame_landmark_and_export(window, tmp_path):
    path = tmp_path / "face.mp4"
    with Image.open(FIXTURE) as source, av.open(str(path), "w") as container:
        stream = container.add_stream("mpeg4", rate=24)
        stream.width, stream.height = source.size
        stream.pix_fmt = "yuv420p"
        for _ in range(24):
            for packet in stream.encode(av.VideoFrame.from_image(source)):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    panel = window.ui.leftPanel
    window.load_media(panel, QUrl.fromLocalFile(str(path)), False)
    for _ in range(1000):
        QApplication.processEvents()
        if window.ui.leftDetectLandmarksButton.isEnabled():
            break
        sleep(0.01)
    assert window.ui.leftDetectLandmarksButton.isEnabled()
    assert Path(window.media_players[panel].source().toLocalFile()) == path
    window.ui.leftDetectLandmarksButton.click()
    wait_idle(window)
    assert len(window.face_results[panel][1].boxes) == 1
    assert window.face_results[panel][2][0].points.shape == (203, 2)
    window.ui.leftSaveCroppedFaceButton.click()
    wait_idle(window)
    with Image.open(next(tmp_path.glob("aligned_*.png"))) as crop:
        assert crop.size == (512, 512)


def test_rgb_conversion_respects_row_padding():
    pixels = np.arange(18, dtype=np.uint8).reshape(2, 3, 3)
    source = QImage(pixels.data, 3, 2, 9, QImage.Format.Format_RGB888).copy()
    assert source.bytesPerLine() == 12
    np.testing.assert_array_equal(image_array(source), pixels)


def test_only_supported_model_choices(window):
    detectors = window.ui.faceDetectModelComboBox
    assert [detectors.itemText(i) for i in range(detectors.count())] == [
        "RetinaFace",
        "Yolov8",
        "SCRFD",
        "Yunet",
    ]
    landmarks = window.ui.landmarkDetectModelComboBox
    assert landmarks.count() == 11 and landmarks.itemText(10) == "hrffa"


@pytest.mark.models
@pytest.mark.parametrize("action", ["detect", "landmarks"])
def test_annotations_in_original_and_aligned_face(window, action):
    panel = window.ui.leftPanel
    load(window, panel)
    window.start_analysis(panel, action)
    wait_idle(window)
    _, detection, landmarks = window.face_results[panel]
    points = landmarks[0].points if landmarks else detection.points5[0]
    source = image_array(window.image_pixmaps[window.ui.leftImage].toImage())
    crop = image_array(window.face_previews[panel][0].toImage())
    for mode in ("Original", "Face"):
        window.ui.showBoundingBoxesCheckBox.setChecked(False)
        window.ui.showLandmarksCheckBox.setChecked(False)
        window.ui.leftPreviewModeComboBox.setCurrentText(mode)
        clean = image_array(window.ui.leftImage.pixmap().toImage())
        window.ui.showLandmarksCheckBox.setChecked(True)
        marked = image_array(window.ui.leftImage.pixmap().toImage())
        mapped = points.copy()
        if mode == "Face":
            matrix = window.face_preview_matrices[panel][0]
            mapped = np.column_stack((points, np.ones(len(points)))) @ matrix.T
        h, w = crop.shape[:2] if mode == "Face" else source.shape[:2]
        mapped = mapped * [marked.shape[1] / w, marked.shape[0] / h]
        visible = 0
        for x, y in mapped:
            x, y = round(x), round(y)
            if 3 <= x < marked.shape[1] - 3 and 3 <= y < marked.shape[0] - 3:
                visible += 1
                assert np.any(
                    marked[y - 3 : y + 4, x - 3 : x + 4]
                    != clean[y - 3 : y + 4, x - 3 : x + 4]
                )
        assert visible > 0
        window.ui.showLandmarksCheckBox.setChecked(False)
        window.ui.showBoundingBoxesCheckBox.setChecked(True)
        boxed = image_array(window.ui.leftImage.pixmap().toImage())
        assert np.any(boxed != clean)
        window.ui.showBoundingBoxesCheckBox.setChecked(False)
        np.testing.assert_array_equal(
            image_array(window.ui.leftImage.pixmap().toImage()), clean
        )
    np.testing.assert_array_equal(
        image_array(window.image_pixmaps[window.ui.leftImage].toImage()), source
    )
    np.testing.assert_array_equal(
        image_array(window.face_previews[panel][0].toImage()), crop
    )


def test_auto_preview_selects_accepted_face_and_clears_rejected_selection(window):
    panel = window.ui.leftPanel
    load(window, panel)
    points = np.array([[10, 10], [30, 10], [20, 20], [12, 30], [28, 30]])
    detection = SimpleNamespace(
        boxes=np.array([[0, 0, 40, 40], [0, 0, 40, 40]]),
        points5=np.array([points, points]),
        scores=np.array([0.9, 0.8]),
    )
    window.analysis_panel = panel
    window.analysis_key = window.image_pixmaps[window.ui.leftImage].cacheKey()
    window.analysis_worker.action = "landmarks"
    window.analysis_completed(
        (
            detection,
            [None, SimpleNamespace(points=points, points5=points, model="5")],
            [None, np.full((512, 512, 3), 80, dtype=np.uint8)],
            [None, np.array([[1, 0, 0], [0, 1, 0]])],
        )
    )
    assert window.ui.leftSelectedFaceComboBox.currentIndex() == 1
    assert window.ui.leftPreviewModeComboBox.currentText() == "Face"
    window.ui.leftSelectedFaceComboBox.setCurrentIndex(0)
    assert window.ui.leftPreviewModeComboBox.currentText() == "Original"
    assert not window.ui.leftPreviewModeComboBox.model().item(1).isEnabled()
    assert window.ui.rightPreviewModeComboBox.currentText() == "Original"
