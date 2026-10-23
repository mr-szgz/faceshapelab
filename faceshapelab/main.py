import sys
from pathlib import Path

from PySide6.QtCore import QDir, QEvent, QFileInfo, QMimeDatabase, QModelIndex, QSettings, QUrl, Qt
from PySide6.QtGui import QImageReader, QPixmap
from PySide6.QtMultimedia import QMediaPlayer, QVideoSink
from PySide6.QtWidgets import QApplication, QFileDialog, QFileSystemModel, QLabel, QMainWindow, QVBoxLayout, QWidget

from faceshapelab.thumbnails import ThumbnailWorker
from faceshapelab.ui.core.main_window import Ui_MainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.splitDockWidget(
            self.ui.filesFoldersDock, self.ui.savedFilesDock, Qt.Orientation.Vertical
        )
        self.files_model = QFileSystemModel(self)
        self.ui.filesTree.setModel(self.files_model)
        self.ui.filesTree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        for column in (1, 2, 3):
            self.ui.filesTree.hideColumn(column)
        self.set_folder(QDir.currentPath())
        self.ui.browseFolderButton.clicked.connect(self.select_folder)
        self.ui.outputFolderPath.setText(QDir.currentPath())
        self.ui.browseOutputFolderButton.clicked.connect(self.select_output_folder)
        self.panel_images = {
            self.ui.leftPanel: self.ui.leftImage,
            self.ui.rightPanel: self.ui.rightImage,
        }
        self.image_pixmaps = {}
        self.media_players = {}
        self.video_sinks = {}
        self.pending_media = {}
        self.playback_controls = {}
        for side in ("left", "right"):
            panel = getattr(self.ui, side + "Panel")
            slider = getattr(self.ui, side + "TimelineSlider")
            play = getattr(self.ui, side + "PlayPauseButton")
            backward = getattr(self.ui, side + "SkipBackwardButton")
            forward = getattr(self.ui, side + "SkipForwardButton")
            time = getattr(self.ui, side + "TimeLabel")
            self.playback_controls[panel] = (slider, play, backward, forward, time)
            player = QMediaPlayer(self)
            sink = QVideoSink(self)
            player.setVideoSink(sink)
            self.media_players[panel] = player
            self.video_sinks[panel] = sink
            self.connect_player(panel)
            slider.valueChanged.connect(lambda position, p=panel: self.media_players[p].setPosition(position))
            slider.sliderPressed.connect(lambda p=panel: self.media_players[p].pause())
            play.clicked.connect(lambda checked=False, p=panel: self.toggle_playback(p))
            backward.clicked.connect(lambda checked=False, p=panel: self.skip_media(p, -2000))
            forward.clicked.connect(lambda checked=False, p=panel: self.skip_media(p, 2000))
        for panel, label in self.panel_images.items():
            panel.installEventFilter(self)
            label.installEventFilter(self)
        self.settings = QSettings("FaceShapeLab", "FaceShapeLab")
        self.settings_controls = (
            (self.ui.folderPath, "text", "setText", "textChanged", str),
            (self.ui.outputFolderPath, "text", "setText", "textChanged", str),
            (self.ui.recognitionModelComboBox, "currentIndex", "setCurrentIndex", "currentIndexChanged", int),
            (self.ui.faceDetectModelComboBox, "currentIndex", "setCurrentIndex", "currentIndexChanged", int),
            (self.ui.landmarkDetectModelComboBox, "currentIndex", "setCurrentIndex", "currentIndexChanged", int),
            (self.ui.detectScoreSlider, "value", "setValue", "valueChanged", int),
            (self.ui.landmarkDetectScoreSlider, "value", "setValue", "valueChanged", int),
            (self.ui.showLandmarksCheckBox, "isChecked", "setChecked", "toggled", bool),
            (self.ui.showBoundingBoxesCheckBox, "isChecked", "setChecked", "toggled", bool),
        )
        for control, getter, setter, signal, value_type in self.settings_controls:
            key = "controls/" + control.objectName()
            if self.settings.contains(key):
                getattr(control, setter)(self.settings.value(key, type=value_type))
            getattr(control, signal).connect(
                lambda value, k=key: self.settings.setValue(k, value)
            )
        self.set_folder(self.ui.folderPath.text())
        self.thumbnail_worker = None
        self.outputs_refresh_pending = False
        self.ui.outputThumbnailsGrid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.ui.refreshOutputsButton.clicked.connect(self.refresh_outputs)
        self.ui.outputFolderPath.editingFinished.connect(self.refresh_outputs)
        self.refresh_outputs()

    def set_folder(self, folder):
        self.ui.folderPath.setText(folder)
        self.ui.folderPath.setToolTip(folder)
        self.ui.filesTree.setRootIndex(self.files_model.setRootPath(folder))
        self.ui.filesTree.clearSelection()
        self.ui.filesTree.setCurrentIndex(QModelIndex())
        self.ui.filesTree.collapseAll()

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select folder", self.ui.folderPath.text()
        )
        if folder:
            self.set_folder(folder)

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select output folder", self.ui.outputFolderPath.text()
        )
        if folder:
            self.ui.outputFolderPath.setText(folder)
            self.refresh_outputs()

    def refresh_outputs(self):
        if self.thumbnail_worker is not None and self.thumbnail_worker.isRunning():
            self.outputs_refresh_pending = True
            self.thumbnail_worker.requestInterruption()
            return
        self.outputs_refresh_pending = False
        if self.thumbnail_worker is not None:
            self.thumbnail_worker.thumbnail_ready.disconnect(self.add_output_thumbnail)
            self.thumbnail_worker.finished.disconnect(self.outputs_finished)
            self.thumbnail_worker.deleteLater()
        grid = self.ui.outputThumbnailsGrid
        while grid.count():
            grid.takeAt(0).widget().deleteLater()
        self.ui.refreshOutputsButton.setEnabled(False)
        self.thumbnail_worker = ThumbnailWorker(self.ui.outputFolderPath.text(), self)
        self.thumbnail_worker.thumbnail_ready.connect(self.add_output_thumbnail)
        self.thumbnail_worker.finished.connect(self.outputs_finished)
        self.thumbnail_worker.start()

    def add_output_thumbnail(self, path, image):
        if self.sender() != self.thumbnail_worker:
            return
        tile = QWidget(self.ui.outputThumbnailsContents)
        tile.setFixedWidth(132)
        tile.setToolTip(path)
        layout = QVBoxLayout(tile)
        layout.setContentsMargins(4, 4, 4, 4)
        preview = QLabel(tile)
        preview.setFixedSize(124, 124)
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview.setPixmap(QPixmap.fromImage(image))
        layout.addWidget(preview)
        name = QLabel(Path(path).name, tile)
        name.setTextFormat(Qt.TextFormat.PlainText)
        name.setWordWrap(True)
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name)
        index = self.ui.outputThumbnailsGrid.count()
        self.ui.outputThumbnailsGrid.addWidget(tile, index // 2, index % 2)

    def outputs_finished(self):
        if self.sender() == self.thumbnail_worker:
            if self.outputs_refresh_pending:
                self.refresh_outputs()
            else:
                self.ui.refreshOutputsButton.setEnabled(True)

    def eventFilter(self, watched, event):
        if watched in self.panel_images and event.type() in (
            QEvent.Type.DragEnter, QEvent.Type.DragMove, QEvent.Type.Drop
        ):
            urls = event.mimeData().urls()
            if len(urls) != 1 or not urls[0].isLocalFile():
                self.statusBar().showMessage("Warning: Drop one local image or video file at a time.")
            elif not QFileInfo(urls[0].toLocalFile()).isFile():
                self.statusBar().showMessage("Warning: Drop a file, not a folder or missing item.")
            else:
                path = urls[0].toLocalFile()
                reader = QImageReader(path)
                is_image = reader.canRead()
                is_video = QMimeDatabase().mimeTypeForFile(path).name().startswith("video/")
                if is_image or is_video:
                    if event.type() == QEvent.Type.Drop:
                        if not self.load_media(watched, urls[0], is_image):
                            event.ignore()
                            return True
                    event.setDropAction(Qt.DropAction.CopyAction)
                    event.accept()
                    return True
                self.statusBar().showMessage(f"Warning: Unsupported image or video: {urls[0].fileName()}")
            event.ignore()
            return True
        if event.type() == QEvent.Type.Resize and watched in self.image_pixmaps:
            self.scale_image(watched)
        return super().eventFilter(watched, event)

    def load_media(self, panel, url, is_image):
        if is_image:
            reader = QImageReader(url.toLocalFile())
            reader.setAutoTransform(True)
            image = reader.read()
            if image.isNull():
                self.statusBar().showMessage(f"Warning: Cannot load {url.fileName()}: {reader.errorString()}")
                return False
        if panel in self.pending_media:
            self.discard_pending_media(panel)
        if not is_image:
            player = QMediaPlayer(self)
            sink = QVideoSink(player)
            player.setVideoSink(sink)
            self.pending_media[panel] = player
            sink.videoFrameChanged.connect(lambda frame: self.accept_video(panel, player, frame))
            player.errorOccurred.connect(
                lambda error, message: self.reject_video(panel, player, message)
            )
            player.mediaStatusChanged.connect(
                lambda status: self.check_video_tracks(panel, player, status)
            )
            self.statusBar().showMessage(f"Loading {url.fileName()} into {panel.title()}…")
            player.setSource(url)
            player.play()
            return True
        player = self.media_players[panel]
        player.stop()
        player.setSource(QUrl())
        slider, play, backward, forward, time = self.playback_controls[panel]
        for control in (slider, play, backward, forward):
            control.setEnabled(False)
        slider.setRange(0, 0)
        play.setText("Play")
        label = self.panel_images[panel]
        self.image_pixmaps[label] = QPixmap.fromImage(image)
        self.scale_image(label)
        time.setText("Frame 1 / 1")
        self.statusBar().showMessage(f"Loaded {url.fileName()} into {panel.title()}.")
        return True

    def connect_player(self, panel):
        player = self.media_players[panel]
        self.video_sinks[panel].videoFrameChanged.connect(lambda frame: self.display_frame(panel, frame))
        player.durationChanged.connect(lambda duration: self.update_timeline(panel))
        player.positionChanged.connect(lambda position: self.update_timeline(panel))
        player.seekableChanged.connect(lambda seekable: self.update_timeline(panel))
        player.playbackStateChanged.connect(lambda state: self.update_playback(panel))

    def discard_pending_media(self, panel):
        player = self.pending_media.pop(panel)
        player.videoSink().videoFrameChanged.disconnect()
        player.errorOccurred.disconnect()
        player.mediaStatusChanged.disconnect()
        player.stop()
        player.setSource(QUrl())
        player.deleteLater()

    def reject_video(self, panel, player, message):
        if self.pending_media.get(panel) is player:
            name = player.source().fileName()
            self.discard_pending_media(panel)
            self.statusBar().showMessage(f"Warning: Cannot load {name}: {message}")

    def check_video_tracks(self, panel, player, status):
        if status == QMediaPlayer.MediaStatus.LoadedMedia and not player.hasVideo():
            self.reject_video(panel, player, "No supported video track.")

    def accept_video(self, panel, player, frame):
        if not frame.isValid() or self.pending_media.get(panel) is not player:
            return
        image = frame.toImage()
        if image.isNull():
            self.reject_video(panel, player, "Cannot decode the video frame.")
            return
        del self.pending_media[panel]
        sink = player.videoSink()
        sink.videoFrameChanged.disconnect()
        player.errorOccurred.disconnect()
        player.mediaStatusChanged.disconnect()
        player.pause()
        old_player = self.media_players[panel]
        old_sink = self.video_sinks[panel]
        old_sink.videoFrameChanged.disconnect()
        old_player.stop()
        old_player.durationChanged.disconnect()
        old_player.positionChanged.disconnect()
        old_player.seekableChanged.disconnect()
        old_player.playbackStateChanged.disconnect()
        old_player.setSource(QUrl())
        old_sink.deleteLater()
        old_player.deleteLater()
        self.media_players[panel] = player
        self.video_sinks[panel] = sink
        self.connect_player(panel)
        label = self.panel_images[panel]
        self.image_pixmaps[label] = QPixmap.fromImage(image)
        self.scale_image(label)
        self.playback_controls[panel][1].setEnabled(True)
        self.update_timeline(panel)
        self.update_playback(panel)
        self.statusBar().showMessage(f"Loaded {player.source().fileName()} into {panel.title()}.")

    def display_frame(self, panel, frame):
        # Qt sends an empty frame when the video output is cleared.
        if frame.isValid():
            label = self.panel_images[panel]
            self.image_pixmaps[label] = QPixmap.fromImage(frame.toImage())
            self.scale_image(label)
            self.playback_controls[panel][1].setEnabled(True)

    def update_timeline(self, panel):
        player = self.media_players[panel]
        slider, play, backward, forward, time = self.playback_controls[panel]
        slider.blockSignals(True)
        slider.setRange(0, player.duration())
        if not slider.isSliderDown():
            slider.setValue(player.position())
        slider.blockSignals(False)
        for control in (slider, backward, forward):
            control.setEnabled(player.isSeekable() and player.duration() > 0)
        position = player.position() // 1000
        duration = player.duration() // 1000
        time.setText(f"{position // 60:02}:{position % 60:02} / {duration // 60:02}:{duration % 60:02}")

    def update_playback(self, panel):
        playing = self.media_players[panel].playbackState() == QMediaPlayer.PlaybackState.PlayingState
        self.playback_controls[panel][1].setText("Pause" if playing else "Play")

    def toggle_playback(self, panel):
        player = self.media_players[panel]
        if player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            player.pause()
        else:
            if player.position() >= player.duration():
                player.setPosition(0)
            player.play()

    def skip_media(self, panel, milliseconds):
        player = self.media_players[panel]
        player.setPosition(max(0, min(player.duration(), player.position() + milliseconds)))

    def closeEvent(self, event):
        self.outputs_refresh_pending = False
        for panel in list(self.pending_media):
            self.discard_pending_media(panel)
        self.thumbnail_worker.requestInterruption()
        self.thumbnail_worker.wait()
        for control, getter, setter, signal, value_type in self.settings_controls:
            self.settings.setValue("controls/" + control.objectName(), getattr(control, getter)())
        self.settings.sync()
        for player in self.media_players.values():
            player.stop()
            player.setSource(QUrl())
        super().closeEvent(event)

    def scale_image(self, label):
        label.setPixmap(self.image_pixmaps[label].scaled(
            label.contentsRect().size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ))


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
