from pathlib import Path
from time import sleep
from unittest.mock import patch

import av
import numpy as np
import pytest
from PIL import Image
from PySide6.QtCore import QSettings, QUrl
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
        assert getattr(window.ui, side + "SaveFaceButton").isEnabled()
        getattr(window.ui, side + "DetectLandmarksButton").click()
        wait_idle(window)
        assert window.face_results[panel][2][0].points.shape == (203, 2)
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
    window.ui.compareFacesButton.click()
    wait_idle(window)
    assert "100.00 / 100" in window.statusBar().currentMessage()


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
    window.ui.leftSelectedFaceComboBox.setCurrentIndex(1)
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
