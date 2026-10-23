import sys

from PySide6.QtCore import QDir, QEvent, QMimeDatabase, QUrl, Qt
from PySide6.QtGui import QImageReader, QPixmap
from PySide6.QtMultimedia import QMediaPlayer, QVideoSink
from PySide6.QtWidgets import QApplication, QFileDialog, QFileSystemModel, QMainWindow

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
        self.preview_pending = {}
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
            self.preview_pending[panel] = False
            sink.videoFrameChanged.connect(lambda frame, p=panel: self.display_frame(p, frame))
            player.durationChanged.connect(lambda duration, p=panel: self.update_timeline(p))
            player.positionChanged.connect(lambda position, p=panel: self.update_timeline(p))
            player.seekableChanged.connect(lambda seekable, p=panel: self.update_timeline(p))
            player.playbackStateChanged.connect(lambda state, p=panel: self.update_playback(p))
            slider.valueChanged.connect(player.setPosition)
            slider.sliderPressed.connect(player.pause)
            play.clicked.connect(lambda checked=False, p=panel: self.toggle_playback(p))
            backward.clicked.connect(lambda checked=False, p=panel: self.skip_media(p, -2000))
            forward.clicked.connect(lambda checked=False, p=panel: self.skip_media(p, 2000))
        for panel, label in self.panel_images.items():
            panel.installEventFilter(self)
            label.installEventFilter(self)

    def set_folder(self, folder):
        self.ui.folderPath.setText(folder)
        self.ui.filesTree.setRootIndex(self.files_model.setRootPath(folder))

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

    def eventFilter(self, watched, event):
        if watched in self.panel_images and event.type() in (
            QEvent.Type.DragEnter, QEvent.Type.DragMove, QEvent.Type.Drop
        ):
            urls = event.mimeData().urls()
            if len(urls) == 1 and urls[0].isLocalFile():
                reader = QImageReader(urls[0].toLocalFile())
                is_image = reader.canRead()
                is_video = QMimeDatabase().mimeTypeForFile(urls[0].toLocalFile()).name().startswith("video/")
                if is_image or is_video:
                    if event.type() == QEvent.Type.Drop:
                        self.load_media(watched, urls[0], is_image)
                    event.setDropAction(Qt.DropAction.CopyAction)
                    event.accept()
                    return True
            event.ignore()
            return True
        if event.type() == QEvent.Type.Resize and watched in self.image_pixmaps:
            self.scale_image(watched)
        return super().eventFilter(watched, event)

    def load_media(self, panel, url, is_image):
        player = self.media_players[panel]
        self.preview_pending[panel] = False
        player.stop()
        player.setSource(QUrl())
        slider, play, backward, forward, time = self.playback_controls[panel]
        for control in (slider, play, backward, forward):
            control.setEnabled(False)
        slider.setRange(0, 0)
        play.setText("Play")
        label = self.panel_images[panel]
        if is_image:
            reader = QImageReader(url.toLocalFile())
            reader.setAutoTransform(True)
            self.image_pixmaps[label] = QPixmap.fromImage(reader.read())
            self.scale_image(label)
            time.setText("Frame 1 / 1")
        else:
            self.image_pixmaps.pop(label, None)
            label.clear()
            time.setText("00:00 / 00:00")
            self.preview_pending[panel] = True
            player.setSource(url)
            player.play()

    def display_frame(self, panel, frame):
        # Qt sends an empty frame when the video output is cleared.
        if frame.isValid():
            label = self.panel_images[panel]
            self.image_pixmaps[label] = QPixmap.fromImage(frame.toImage())
            self.scale_image(label)
            if self.preview_pending[panel]:
                self.preview_pending[panel] = False
                self.media_players[panel].pause()
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
        for player in self.media_players.values():
            player.stop()
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
