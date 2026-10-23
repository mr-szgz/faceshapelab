"""Run image analysis on a detached frame; widgets stay on the GUI thread."""

from pathlib import Path

import numpy as np
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage


def image_array(image: QImage) -> np.ndarray:
    image = image.convertToFormat(QImage.Format.Format_RGB888)
    rows = np.frombuffer(image.constBits(), dtype=np.uint8).reshape(
        image.height(), image.bytesPerLine()
    )
    return rows[:, : image.width() * 3].reshape(image.height(), image.width(), 3).copy()


class AnalysisWorker(QThread):
    completed = Signal(object)

    def __init__(self, model_dir: Path, parent=None):
        super().__init__(parent)
        self.model_dir = model_dir
        self.runtime = None

    def run(self):
        import torch

        from faceshapelab.face_analysis.detection import FaceDetector
        from faceshapelab.face_analysis.landmarks import LandmarkDetector
        from faceshapelab.face_analysis.recognition import FaceRecognizer, aligned_crop
        from faceshapelab.face_analysis.runtime import Runtime

        if self.runtime is None:
            self.runtime = Runtime(self.model_dir)
        image = (
            torch.from_numpy(self.pixels)
            .permute(2, 0, 1)
            .to(self.runtime.device)
            .contiguous()
        )
        if self.action in ("detect", "landmarks"):
            detection = FaceDetector(self.runtime, self.detector).detect(
                image, self.detect_score
            )
            landmarks = []
            if self.action == "landmarks":
                landmarker = LandmarkDetector(self.runtime, self.landmark)
                heads = (
                    landmarker.detect_heads(image) if self.landmark == "hrffa" else None
                )
                landmarks = [
                    landmarker.detect(
                        image, box, points, self.landmark_score, head_boxes=heads
                    )
                    for box, points in zip(detection.boxes, detection.points5)
                ]
            self.completed.emit((detection, landmarks))
        elif self.action == "crop":
            self.completed.emit(aligned_crop(image, self.points5))
        elif self.action == "recognize":
            recognizer = FaceRecognizer(self.runtime, self.recognizer)
            left = recognizer.recognize(image, self.points5)
            other = (
                torch.from_numpy(self.other_pixels)
                .permute(2, 0, 1)
                .to(self.runtime.device)
                .contiguous()
            )
            right = recognizer.recognize(other, self.other_points5)
            from faceshapelab.face_analysis.recognition import similarity

            self.completed.emit(similarity(left.embedding, right.embedding))
