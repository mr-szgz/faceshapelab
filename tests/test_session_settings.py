"""Restore the workspace without persisting inference results."""

from pathlib import Path

import av
import pytest
from PIL import Image
from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from test_analysis_ui import window  # noqa: F401

from faceshapelab.main import MainWindow


def test_restore_folder_geometry_docks_and_both_images(window, tmp_path):  # noqa: F811
    window.set_folder(str(tmp_path))
    expected = {}
    for side, color in (("left", "red"), ("right", "blue")):
        path = tmp_path / f"{side}.png"
        Image.new("RGB", (80, 40), color).save(path)
        panel = getattr(window.ui, side + "Panel")
        assert window.load_media(panel, QUrl.fromLocalFile(str(path)), True)
        expected[side] = window.image_pixmaps[
            getattr(window.ui, side + "Image")
        ].toImage()
    window.addDockWidget(
        Qt.DockWidgetArea.TopDockWidgetArea, window.ui.compareFacesDock
    )
    window.resize(1200, 800)
    window.move(30, 40)
    QApplication.processEvents()
    size, position = window.size(), window.pos()
    window.close()

    reopened = MainWindow()
    reopened.show()
    QApplication.processEvents()
    assert reopened.ui.folderPath.text() == str(tmp_path)
    assert (
        Path(reopened.files_model.filePath(reopened.ui.filesTree.rootIndex()))
        == tmp_path
    )
    assert reopened.size() == size
    assert reopened.pos() == position
    assert (
        reopened.dockWidgetArea(reopened.ui.compareFacesDock)
        == Qt.DockWidgetArea.TopDockWidgetArea
    )
    for side in ("left", "right"):
        assert (
            reopened.image_pixmaps[getattr(reopened.ui, side + "Image")].toImage()
            == expected[side]
        )
        assert getattr(reopened.ui, side + "SelectedFaceComboBox").count() == 0
        assert (
            getattr(reopened.ui, side + "PreviewModeComboBox").currentText()
            == "Original"
        )
    assert reopened.face_results == {}
    assert reopened.ui.embeddingComparisonTable.rowCount() == 0
    assert not reopened.analysis_worker.isRunning()
    reopened.close()


def test_restore_maximized_window(window):  # noqa: F811
    window.showMaximized()
    QApplication.processEvents()
    window.close()
    reopened = MainWindow()
    reopened.show()
    QApplication.processEvents()
    assert reopened.isMaximized()
    reopened.close()


def wait_media(widget):
    for _ in range(500):
        QApplication.processEvents()
        if not widget.pending_media:
            return
        QTest.qWait(10)
    pytest.fail("Media loading did not finish")


def test_restore_video_and_preserve_saved_media_after_rejected_drop(window, tmp_path):  # noqa: F811
    path = tmp_path / "clip.mp4"
    with av.open(str(path), "w") as container:
        stream = container.add_stream("mpeg4", rate=10)
        stream.width = stream.height = 64
        stream.pix_fmt = "yuv420p"
        for _ in range(10):
            frame = av.VideoFrame.from_image(Image.new("RGB", (64, 64), "blue"))
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    panel = window.ui.leftPanel
    window.load_media(panel, QUrl.fromLocalFile(str(path)), False)
    wait_media(window)
    assert Path(window.settings.value("media/leftPanel/path")) == path
    bad = tmp_path / "broken.mp4"
    bad.write_bytes(b"not a movie")
    window.load_media(panel, QUrl.fromLocalFile(str(bad)), False)
    wait_media(window)
    assert Path(window.settings.value("media/leftPanel/path")) == path
    window.close()

    reopened = MainWindow()
    reopened.show()
    wait_media(reopened)
    player = reopened.media_players[reopened.ui.leftPanel]
    assert player.source() == QUrl.fromLocalFile(str(path))
    assert player.playbackState() == QMediaPlayer.PlaybackState.PausedState
    assert reopened.ui.leftImage in reopened.image_pixmaps
    assert reopened.ui.rightImage not in reopened.image_pixmaps
    assert reopened.face_results == {}
    # Replacing the restored video with a still updates the persisted media type.
    still = tmp_path / "still.png"
    Image.new("RGB", (32, 32), "red").save(still)
    reopened.load_media(reopened.ui.leftPanel, QUrl.fromLocalFile(str(still)), True)
    assert Path(reopened.settings.value("media/leftPanel/path")) == still
    assert reopened.settings.value("media/leftPanel/isImage", type=bool)
    reopened.close()
