from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import av
from PIL import Image
from PySide6.QtCore import QFile, QIODevice, QMimeData, QPointF, QSettings, QUrl, Qt
from PySide6.QtDesigner import QFormBuilder
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from PySide6.QtMultimedia import QMediaPlayer, QVideoFrame
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QGridLayout

from faceshapelab.main import MainWindow


class LayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.settings_folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.settings_folder.cleanup)
        settings = QSettings(str(Path(self.settings_folder.name, "settings.ini")), QSettings.Format.IniFormat)
        self.settings_patch = patch("faceshapelab.main.QSettings", return_value=settings)
        self.settings_patch.start()
        self.addCleanup(self.settings_patch.stop)
        self.cache_patch = patch("faceshapelab.thumbnails.user_cache_path", return_value=Path(self.settings_folder.name, "cache"))
        self.cache_patch.start()
        self.addCleanup(self.cache_patch.stop)
        self.window = MainWindow()
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        self.window.close()

    def wait_for_outputs(self):
        for _ in range(500):
            self.app.processEvents()
            if self.window.ui.refreshOutputsButton.isEnabled():
                return
            QTest.qWait(10)
        self.fail("Output generation did not complete")

    def test_output_thumbnails_cache_refresh_and_video(self):
        self.wait_for_outputs()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            Image.new("RGB", (400, 200), "red").save(root / "photo.png")
            (root / "notes.txt").write_text("Not media", encoding="utf-8")
            with av.open(str(root / "clip.mp4"), "w") as container:
                stream = container.add_stream("mpeg4", rate=24)
                stream.width = 64
                stream.height = 64
                stream.pix_fmt = "yuv420p"
                frame = av.VideoFrame.from_image(Image.new("RGB", (64, 64), "blue"))
                for packet in stream.encode(frame):
                    container.mux(packet)
                for packet in stream.encode():
                    container.mux(packet)
            self.window.ui.outputFolderPath.setText(folder)
            self.window.ui.refreshOutputsButton.click()
            self.wait_for_outputs()
            grid = self.window.ui.outputThumbnailsGrid
            self.assertEqual(grid.count(), 2)
            self.assertEqual(grid.itemAt(1).widget().toolTip(), str(root / "photo.png"))
            cache = Path(self.settings_folder.name, "cache", "thumbnails")
            cached = {path.name: path.stat().st_mtime_ns for path in cache.glob("*.png")}
            self.assertEqual(len(cached), 2)
            self.window.ui.refreshOutputsButton.click()
            self.wait_for_outputs()
            self.assertEqual(cached, {path.name: path.stat().st_mtime_ns for path in cache.glob("*.png")})
            Image.new("RGB", (200, 400), "green").save(root / "photo.png")
            (root / "clip.mp4").unlink()
            self.window.ui.refreshOutputsButton.click()
            self.wait_for_outputs()
            self.assertEqual(grid.count(), 1)
            self.assertEqual(len(list(cache.glob("*.png"))), 3)
            self.window.ui.outputFolderPath.setText(str(Path.cwd()))

    def test_settings_restore_on_new_window(self):
        self.wait_for_outputs()
        self.window.ui.outputFolderPath.setText(self.settings_folder.name)
        self.window.ui.detectScoreSlider.setValue(73)
        self.window.ui.landmarkDetectModelComboBox.setCurrentIndex(3)
        self.window.ui.showLandmarksCheckBox.setChecked(True)
        self.window.close()
        settings = QSettings(str(Path(self.settings_folder.name, "settings.ini")), QSettings.Format.IniFormat)
        with patch("faceshapelab.main.QSettings", return_value=settings):
            self.window = MainWindow()
        self.wait_for_outputs()
        self.assertEqual(self.window.ui.outputFolderPath.text(), self.settings_folder.name)
        self.assertEqual(self.window.ui.detectScoreSlider.value(), 73)
        self.assertEqual(self.window.ui.landmarkDetectModelComboBox.currentIndex(), 3)
        self.assertTrue(self.window.ui.showLandmarksCheckBox.isChecked())

    def test_generated_ui_matches_source(self):
        root = Path(__file__).resolve().parents[1]
        generated = subprocess.check_output(
            ["uv", "run", "pyside6-uic", "faceshapelab/ui/core/MainWindow.ui"],
            cwd=root,
            text=True,
        )
        self.assertEqual(
            generated,
            (root / "faceshapelab/ui/core/main_window.py").read_text(encoding="utf-8"),
        )

    def test_menu_status_and_controls_grids(self):
        ui = self.window.ui
        self.assertEqual(self.window.menuBar().actions()[0].text(), "&File")
        self.assertTrue(self.window.statusBar().isVisible())
        for grid in (ui.leftControlsGrid, ui.rightControlsGrid):
            self.assertIsInstance(grid, QGridLayout)
            self.assertEqual(grid.count(), 4)
            self.assertEqual(grid.itemAtPosition(0, 0).widget().text(), "Detect Faces")
            self.assertEqual(grid.itemAtPosition(0, 1).widget().text(), "Detect Landmarks")
            self.assertEqual(grid.itemAtPosition(1, 0).widget().text(), "Save Face")
            self.assertEqual(grid.itemAtPosition(1, 1).widget().text(), "Save Cropped Face")
        QTest.keyClick(self.window, Qt.Key.Key_F, Qt.KeyboardModifier.AltModifier)
        self.app.processEvents()
        self.assertEqual(self.window.menuBar().activeAction(), ui.menuFile.menuAction())
        QTest.keyClick(self.window.menuBar(), Qt.Key.Key_Escape)

    def test_resizing_keeps_panels_equal_and_separate(self):
        ui = self.window.ui
        for width, height in ((640, 480), (1200, 800)):
            with self.subTest(size=(width, height)):
                self.window.resize(width, height)
                self.app.processEvents()
                self.assertLessEqual(abs(ui.leftPanel.width() - ui.rightPanel.width()), 1)
                self.assertLess(ui.leftPanel.geometry().right(), ui.rightPanel.geometry().left())
                for panel, image, playback, controls in (
                    (ui.leftPanel, ui.leftImage, ui.leftPlaybackLayout, ui.leftControls),
                    (ui.rightPanel, ui.rightImage, ui.rightPlaybackLayout, ui.rightControls),
                ):
                    self.assertTrue(panel.rect().contains(image.geometry()))
                    self.assertTrue(panel.rect().contains(controls.geometry()))
                    self.assertTrue(panel.rect().contains(playback.geometry()))
                    self.assertLess(image.geometry().bottom(), playback.geometry().top())
                    self.assertLess(playback.geometry().bottom(), controls.geometry().top())

    def test_still_media_has_one_frame_and_disabled_transport(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder, "still.png"))
            pixmap = QPixmap(80, 40)
            pixmap.fill(Qt.GlobalColor.red)
            self.assertTrue(pixmap.save(path))
            for panel in self.window.panel_images:
                self.window.load_media(panel, QUrl.fromLocalFile(path), True)
                slider, play, backward, forward, time = self.window.playback_controls[panel]
                self.assertEqual(time.text(), "Frame 1 / 1")
                self.assertEqual(slider.maximum(), 0)
                for control in (slider, play, backward, forward):
                    self.assertFalse(control.isEnabled())
                self.assertEqual(self.window.image_pixmaps[self.window.panel_images[panel]].size(), pixmap.size())

    def test_video_frames_update_only_their_panels_working_image(self):
        ui = self.window.ui
        self.assertEqual(ui.leftPanel.title(), "Media 1")
        self.assertEqual(ui.rightPanel.title(), "Media 2")
        for panel, color in ((ui.leftPanel, Qt.GlobalColor.red), (ui.rightPanel, Qt.GlobalColor.blue)):
            pixmap = QPixmap(80, 40)
            pixmap.fill(color)
            self.window.video_sinks[panel].setVideoFrame(QVideoFrame(pixmap.toImage()))
        self.app.processEvents()
        for label, color in ((ui.leftImage, Qt.GlobalColor.red), (ui.rightImage, Qt.GlobalColor.blue)):
            self.assertEqual(self.window.image_pixmaps[label].toImage().pixelColor(0, 0), color)
            self.assertEqual(label.pixmap().toImage().pixelColor(0, 0), color)

    def test_both_image_surfaces_render_pixmaps(self):
        for label, color in (
            (self.window.ui.leftImage, Qt.GlobalColor.red),
            (self.window.ui.rightImage, Qt.GlobalColor.blue),
        ):
            pixmap = QPixmap(80, 80)
            pixmap.fill(color)
            label.setPixmap(pixmap)
            self.app.processEvents()
            rendered = label.grab().toImage()
            self.assertEqual(
                rendered.pixelColor(rendered.width() // 2, rendered.height() // 2),
                pixmap.toImage().pixelColor(40, 40),
            )

    def test_designer_form_loads_with_left_dock(self):
        source = QFile(str(Path(__file__).resolve().parents[1] / "faceshapelab/ui/core/MainWindow.ui"))
        self.assertTrue(source.open(QIODevice.OpenModeFlag.ReadOnly))
        builder = QFormBuilder()
        form = builder.load(source)
        self.assertIsNotNone(form, builder.errorString())
        dock = form.findChild(type(self.window.ui.filesFoldersDock), "filesFoldersDock")
        self.assertEqual(dock.windowTitle(), "Browse Files")
        self.assertEqual(form.dockWidgetArea(dock), Qt.DockWidgetArea.LeftDockWidgetArea)
        form.close()
        source.close()

    def test_compare_faces_dock_defaults_to_bottom_and_can_move(self):
        ui = self.window.ui
        dock = ui.compareFacesDock
        self.assertEqual(dock.windowTitle(), "Compare Faces")
        self.assertEqual(self.window.dockWidgetArea(dock), Qt.DockWidgetArea.BottomDockWidgetArea)
        self.assertTrue(dock.isVisible())
        for control in (
            ui.showLandmarksCheckBox,
            ui.showBoundingBoxesCheckBox,
            ui.compareFacesButton,
        ):
            self.assertTrue(dock.isAncestorOf(control))
            self.assertFalse(ui.faceSettingsDock.isAncestorOf(control))
        self.assertEqual(ui.compareFacesButton.text(), "Compare Face Embeddings")
        self.window.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, dock)
        self.assertEqual(self.window.dockWidgetArea(dock), Qt.DockWidgetArea.TopDockWidgetArea)
        dock.setFloating(True)
        self.app.processEvents()
        self.assertTrue(dock.isFloating())
        self.assertTrue(ui.compareFacesButton.isVisible())

    def test_saved_files_dock_and_output_folder_picker(self):
        ui = self.window.ui
        self.assertEqual(ui.savedFilesDock.windowTitle(), "Saved Files")
        self.assertEqual(self.window.dockWidgetArea(ui.savedFilesDock), Qt.DockWidgetArea.LeftDockWidgetArea)
        self.assertLess(ui.filesFoldersDock.geometry().bottom(), ui.savedFilesDock.geometry().top())
        self.assertEqual(ui.filesFoldersDock.geometry().left(), ui.savedFilesDock.geometry().left())
        with tempfile.TemporaryDirectory() as folder:
            with patch("faceshapelab.main.QFileDialog.getExistingDirectory", return_value=folder):
                ui.browseOutputFolderButton.click()
            self.assertEqual(ui.outputFolderPath.text(), folder)
            self.wait_for_outputs()
            with patch("faceshapelab.main.QFileDialog.getExistingDirectory", return_value=""):
                ui.browseOutputFolderButton.click()
            self.assertEqual(ui.outputFolderPath.text(), folder)

    def test_folder_picker_changes_tree_root(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "nested").mkdir()
            with patch("faceshapelab.main.QFileDialog.getExistingDirectory", return_value=folder):
                self.window.ui.browseFolderButton.click()
            self.assertEqual(self.window.ui.folderPath.text(), folder)
            self.assertEqual(
                Path(self.window.files_model.filePath(self.window.ui.filesTree.rootIndex())),
                Path(folder),
            )
            self.assertTrue(self.window.files_model.index(str(Path(folder, "nested"))).isValid())
            with patch("faceshapelab.main.QFileDialog.getExistingDirectory", return_value=""):
                self.window.ui.browseFolderButton.click()
            self.assertEqual(self.window.ui.folderPath.text(), folder)

    def test_tree_image_drops_and_non_image_rejection(self):
        with tempfile.TemporaryDirectory() as folder:
            self.window.set_folder(folder)
            for panel, label, color in (
                (self.window.ui.leftPanel, self.window.ui.leftImage, Qt.GlobalColor.red),
                (self.window.ui.rightPanel, self.window.ui.rightImage, Qt.GlobalColor.blue),
            ):
                path = str(Path(folder, panel.objectName() + ".png"))
                pixmap = QPixmap(1600, 800)
                pixmap.fill(color)
                self.assertTrue(pixmap.save(path))
                mime = self.window.files_model.mimeData([self.window.files_model.index(path)])
                enter = QDragEnterEvent(QPointF(20, 20), Qt.DropAction.CopyAction, mime,
                                        Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
                QApplication.sendEvent(panel, enter)
                self.assertTrue(enter.isAccepted())
                drop = QDropEvent(QPointF(20, 20), Qt.DropAction.CopyAction, mime,
                                  Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
                QApplication.sendEvent(panel, drop)
                self.assertTrue(drop.isAccepted())
                self.assertEqual(label.pixmap().toImage().pixelColor(0, 0), pixmap.toImage().pixelColor(0, 0))
                self.assertLessEqual(label.pixmap().width(), label.width())
                self.assertLessEqual(label.pixmap().height(), label.height())
            self.window.resize(900, 600)
            self.app.processEvents()
            for label in (self.window.ui.leftImage, self.window.ui.rightImage):
                self.assertLessEqual(label.pixmap().width(), label.width())
                self.assertLessEqual(label.pixmap().height(), label.height())
                self.assertAlmostEqual(label.pixmap().width() / label.pixmap().height(), 2, delta=0.02)
            text_path = Path(folder, "notes.txt")
            text_path.write_text("Not an image", encoding="utf-8")
            for path in (str(text_path), folder):
                mime = self.window.files_model.mimeData([self.window.files_model.index(path)])
                enter = QDragEnterEvent(QPointF(20, 20), Qt.DropAction.CopyAction, mime,
                                        Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
                QApplication.sendEvent(self.window.ui.leftPanel, enter)
                self.assertFalse(enter.isAccepted())
            self.assertEqual(self.window.ui.leftImage.pixmap().toImage().pixelColor(0, 0), Qt.GlobalColor.red)


    def drop_urls(self, target, urls):
        mime = QMimeData()
        mime.setUrls(urls)
        enter = QDragEnterEvent(QPointF(20, 20), Qt.DropAction.CopyAction, mime,
                                Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        QApplication.sendEvent(target, enter)
        if not enter.isAccepted():
            return False
        drop = QDropEvent(QPointF(20, 20), Qt.DropAction.CopyAction, mime,
                          Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
        QApplication.sendEvent(target, drop)
        return drop.isAccepted()

    def wait_for_media(self, panel):
        for _ in range(500):
            self.app.processEvents()
            if panel not in self.window.pending_media:
                return
            QTest.qWait(10)
        self.fail("Media loading did not finish")

    def create_video(self, path):
        with av.open(str(path), "w") as container:
            stream = container.add_stream("mpeg4", rate=10)
            stream.width = 64
            stream.height = 64
            stream.pix_fmt = "yuv420p"
            for index in range(50):
                frame = av.VideoFrame.from_image(Image.new("RGB", (64, 64), (index * 5, 0, 255)))
                for packet in stream.encode(frame):
                    container.mux(packet)
            for packet in stream.encode():
                container.mux(packet)

    def test_folder_change_clears_old_selection_and_cancel_keeps_root(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            first = root / "first"
            second = root / "second"
            first.mkdir()
            second.mkdir()
            (first / "selected.txt").write_text("test")
            self.window.set_folder(str(first))
            self.window.ui.filesTree.setCurrentIndex(self.window.files_model.index(str(first / "selected.txt")))
            with patch("faceshapelab.main.QFileDialog.getExistingDirectory", return_value=str(second)) as picker:
                QTest.keyClick(self.window.ui.browseFolderButton, Qt.Key.Key_Space)
            picker.assert_called_once_with(self.window, "Select folder", str(first))
            tree = self.window.ui.filesTree
            self.assertFalse(tree.currentIndex().isValid())
            self.assertEqual(tree.selectionModel().selectedIndexes(), [])
            self.assertEqual(Path(self.window.files_model.filePath(tree.rootIndex())), second)
            self.assertEqual(self.window.ui.folderPath.toolTip(), str(second))
            with patch("faceshapelab.main.QFileDialog.getExistingDirectory", return_value=""):
                self.window.ui.browseFolderButton.click()
            self.assertEqual(Path(self.window.files_model.filePath(tree.rootIndex())), second)

    def test_rejected_drops_warn_and_preserve_both_panels(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            image = root / "image.png"
            Image.new("RGB", (80, 40), "red").save(image)
            text = root / "notes.txt"
            text.write_text("not media")
            fake = root / "fake.png"
            fake.write_text("not a PNG")
            for panel in self.window.panel_images:
                self.assertTrue(self.drop_urls(panel, [QUrl.fromLocalFile(str(image))]))
            for urls in ([QUrl.fromLocalFile(str(text))], [QUrl.fromLocalFile(str(fake))],
                         [QUrl.fromLocalFile(folder)], [QUrl.fromLocalFile(str(root / "missing.png"))],
                         [QUrl("https://example.com/image.png")], [],
                         [QUrl.fromLocalFile(str(image)), QUrl.fromLocalFile(str(text))]):
                for panel in self.window.panel_images:
                    self.assertFalse(self.drop_urls(panel, urls))
                    self.assertTrue(self.window.statusBar().currentMessage().startswith("Warning:"))
                    self.assertEqual(self.window.image_pixmaps[self.window.panel_images[panel]].toImage().pixelColor(0, 0), Qt.GlobalColor.red)
            self.assertTrue(self.drop_urls(self.window.ui.leftPanel, [QUrl.fromLocalFile(str(image))]))
            self.assertIn("Loaded image.png into Media 1", self.window.statusBar().currentMessage())

    def test_tree_video_drop_playback_replacement_and_invalid_video(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            nested = root / "nested"
            nested.mkdir()
            video = nested / "clip.mp4"
            self.create_video(video)
            bad = nested / "broken.mp4"
            bad.write_bytes(b"not a movie")
            still = root / "still.png"
            Image.new("RGB", (80, 40), "red").save(still)
            self.window.set_folder(folder)
            tree = self.window.ui.filesTree
            tree.expand(self.window.files_model.index(str(nested)))
            for panel in self.window.panel_images:
                index = self.window.files_model.index(str(video))
                mime = self.window.files_model.mimeData([index])
                self.assertTrue(self.drop_urls(panel, mime.urls()))
                self.wait_for_media(panel)
                player = self.window.media_players[panel]
                self.assertEqual(player.source(), QUrl.fromLocalFile(str(video)))
                self.assertEqual(player.playbackState(), QMediaPlayer.PlaybackState.PausedState)
                slider, play, back, forward, time = self.window.playback_controls[panel]
                self.assertTrue(slider.isEnabled())
                slider.setValue(1000)
                forward.click()
                self.assertEqual(player.position(), 3000)
                back.click()
                self.assertEqual(player.position(), 1000)
                play.click()
                QTest.qWait(250)
                self.assertGreater(player.position(), 1000)
                play.click()
                self.assertEqual(player.playbackState(), QMediaPlayer.PlaybackState.PausedState)
                position = player.position()
                image_key = self.window.image_pixmaps[self.window.panel_images[panel]].cacheKey()
                self.assertTrue(self.drop_urls(panel, [QUrl.fromLocalFile(str(bad))]))
                self.wait_for_media(panel)
                self.assertIn("Warning: Cannot load broken.mp4", self.window.statusBar().currentMessage())
                self.assertIs(self.window.media_players[panel], player)
                self.assertEqual(player.position(), position)
                self.assertEqual(self.window.image_pixmaps[self.window.panel_images[panel]].cacheKey(), image_key)
                self.assertTrue(self.drop_urls(panel, [QUrl.fromLocalFile(str(still))]))
                self.assertEqual(time.text(), "Frame 1 / 1")
                self.assertFalse(play.isEnabled())
                self.assertTrue(self.drop_urls(panel, [QUrl.fromLocalFile(str(video))]))
                self.wait_for_media(panel)
                slider.setValue(2000)
                self.assertEqual(self.window.media_players[panel].position(), 2000)
            self.window.close()

    def test_corrupt_image_does_not_replace_current_frame(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder, "image.png")
            Image.new("RGB", (80, 40), "red").save(path)
            panel = self.window.ui.leftPanel
            self.assertTrue(self.drop_urls(panel, [QUrl.fromLocalFile(str(path))]))
            bad = Path(folder, "truncated.png")
            bad.write_bytes(path.read_bytes()[:33])
            self.assertFalse(self.drop_urls(panel, [QUrl.fromLocalFile(str(bad))]))
            self.assertTrue(self.window.statusBar().currentMessage().startswith("Warning:"))
            self.assertEqual(self.window.image_pixmaps[self.window.ui.leftImage].toImage().pixelColor(0, 0), Qt.GlobalColor.red)

    def test_audio_only_mp4_is_rejected_without_replacing_image(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            image = root / "image.png"
            Image.new("RGB", (80, 40), "red").save(image)
            audio = root / "audio.mp4"
            with av.open(str(audio), "w") as container:
                stream = container.add_stream("aac", rate=48000)
                frame = av.AudioFrame(format="fltp", layout="mono", samples=1024)
                frame.sample_rate = 48000
                for plane in frame.planes:
                    plane.update(bytes(plane.buffer_size))
                for packet in stream.encode(frame):
                    container.mux(packet)
                for packet in stream.encode():
                    container.mux(packet)
            panel = self.window.ui.leftPanel
            self.drop_urls(panel, [QUrl.fromLocalFile(str(image))])
            self.drop_urls(panel, [QUrl.fromLocalFile(str(audio))])
            self.wait_for_media(panel)
            self.assertTrue(self.window.statusBar().currentMessage().startswith("Warning:"))
            self.assertEqual(self.window.image_pixmaps[self.window.ui.leftImage].toImage().pixelColor(0, 0), Qt.GlobalColor.red)

    def test_rapid_drop_keeps_latest_media_and_close_releases_video(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            video = root / "clip.mp4"
            self.create_video(video)
            image = root / "image.png"
            Image.new("RGB", (80, 40), "red").save(image)
            panel = self.window.ui.leftPanel
            self.drop_urls(panel, [QUrl.fromLocalFile(str(video))])
            self.drop_urls(panel, [QUrl.fromLocalFile(str(image))])
            QTest.qWait(100)
            self.assertEqual(self.window.ui.leftTimeLabel.text(), "Frame 1 / 1")
            self.assertEqual(self.window.image_pixmaps[self.window.ui.leftImage].toImage().pixelColor(0, 0), Qt.GlobalColor.red)
            self.drop_urls(panel, [QUrl.fromLocalFile(str(video))])
            self.drop_urls(panel, [QUrl.fromLocalFile(str(video))])
            self.wait_for_media(panel)
            self.assertEqual(self.window.media_players[panel].source(), QUrl.fromLocalFile(str(video)))
            self.window.close()
            video.rename(root / "released.mp4")

    def test_drop_on_image_viewer(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder, "image.png")
            Image.new("RGB", (80, 40), "blue").save(path)
            for label in self.window.panel_images.values():
                self.assertTrue(self.drop_urls(label, [QUrl.fromLocalFile(str(path))]))
                self.assertEqual(label.pixmap().toImage().pixelColor(0, 0), Qt.GlobalColor.blue)


if __name__ == "__main__":
    unittest.main()
