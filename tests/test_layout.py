from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from PySide6.QtCore import QFile, QIODevice, QPointF, QUrl, Qt
from PySide6.QtDesigner import QFormBuilder
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from PySide6.QtMultimedia import QVideoFrame
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QGridLayout

from faceshapelab.main import MainWindow


class LayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])

    def setUp(self):
        self.window = MainWindow()
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        self.window.close()

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
                    (ui.leftPanel, ui.leftImage, ui.leftPlaybackControls, ui.leftControls),
                    (ui.rightPanel, ui.rightImage, ui.rightPlaybackControls, ui.rightControls),
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


if __name__ == "__main__":
    unittest.main()
