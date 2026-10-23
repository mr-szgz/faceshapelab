from hashlib import sha256
from pathlib import Path

import av
from PIL import Image, ImageOps
from platformdirs import user_cache_path
from PySide6.QtCore import QMimeDatabase, QThread, Signal
from PySide6.QtGui import QImage


class ThumbnailWorker(QThread):
    thumbnail_ready = Signal(str, QImage)

    def __init__(self, folder, parent=None):
        super().__init__(parent)
        self.folder = Path(folder)

    def run(self):
        cache = user_cache_path("FaceShapeLab", appauthor=False) / "thumbnails"
        cache.mkdir(parents=True, exist_ok=True)
        mime_database = QMimeDatabase()
        for path in sorted(self.folder.iterdir()):
            if self.isInterruptionRequested():
                return
            if not path.is_file():
                continue
            mime = mime_database.mimeTypeForFile(str(path)).name()
            if not mime.startswith(("image/", "video/")):
                continue
            stat = path.stat()
            key = sha256(
                f"v1:{path.resolve()}:{stat.st_mtime_ns}:{stat.st_size}".encode("utf-8")
            ).hexdigest()
            thumbnail = cache / f"{key}.png"
            if not thumbnail.exists():
                if mime.startswith("image/"):
                    with Image.open(path) as source:
                        image = ImageOps.exif_transpose(source).convert("RGBA")
                else:
                    with av.open(str(path)) as container:
                        image = next(container.decode(video=0)).to_image()
                image.thumbnail((120, 120), Image.Resampling.LANCZOS)
                image.save(thumbnail)
            self.thumbnail_ready.emit(str(path), QImage(str(thumbnail)))
