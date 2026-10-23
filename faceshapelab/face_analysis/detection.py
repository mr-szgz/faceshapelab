# Adapted from VisoMaster-Fusion, commit 6563cd21322cf413d0b391aa552f383339636595.
# SPDX-License-Identifier: GPL-3.0-only
from dataclasses import dataclass

import numpy as np
import torch
from torchvision.ops import nms
from torchvision.transforms import v2

from . import geometry
from .runtime import Runtime

MODELS = {
    "RetinaFace": "det_10g.onnx",
    "SCRFD": "scrfd_2.5g_bnkps.onnx",
    "Yolov8": "yoloface_8n.onnx",
    "Yunet": "yunet_n_640_640.onnx",
}


@dataclass
class DetectionResult:
    boxes: np.ndarray
    points5: np.ndarray
    scores: np.ndarray


class FaceDetector:
    def __init__(self, runtime: Runtime, model="RetinaFace"):
        self.runtime = runtime
        self.model = model
        self.filename = MODELS[model]

    def _decode(self, outputs, size, threshold):
        if self.model == "Yolov8":
            values = outputs[0][0].T
            values = values[values[:, 4] > threshold]
            center, wh = values[:, :2], values[:, 2:4]
            return (
                np.concatenate((center - wh / 2, center + wh / 2), axis=1),
                values[:, 5:].reshape(-1, 5, 3)[:, :, :2],
                values[:, 4],
            )
        boxes, points, scores = [], [], []
        for i, stride in enumerate((8, 16, 32)):
            centers = (
                np.stack(np.mgrid[: size // stride, : size // stride][::-1], axis=-1)
                .astype(np.float32)
                .reshape(-1, 2)
                * stride
            )
            if self.model == "Yunet":
                confidence = outputs[i].ravel() * outputs[i + 3].ravel()
                keep = confidence >= threshold
                reg = outputs[i + 6].reshape(-1, 4)[keep]
                xy = reg[:, :2] * stride + centers[keep]
                wh = np.exp(np.clip(reg[:, 2:], -10, 10)) * stride
                boxes.append(np.concatenate((xy - wh / 2, xy + wh / 2), axis=1))
                points.append(
                    outputs[i + 9].reshape(-1, 5, 2)[keep] * stride
                    + centers[keep, None, :]
                )
            else:
                centers = np.repeat(centers, 2, axis=0)
                confidence = outputs[i].ravel()
                keep = confidence >= threshold
                reg = outputs[i + 3][keep] * stride
                boxes.append(
                    np.concatenate(
                        (centers[keep] - reg[:, :2], centers[keep] + reg[:, 2:]), axis=1
                    )
                )
                points.append(
                    outputs[i + 6].reshape(-1, 5, 2)[keep] * stride
                    + centers[keep, None, :]
                )
            scores.append(confidence[keep])
        return np.concatenate(boxes), np.concatenate(points), np.concatenate(scores)

    @torch.inference_mode()
    def detect(
        self, image_rgb, score_threshold=0.5, max_faces=20, rotation_angles=(0,)
    ) -> DetectionResult:
        session = self.runtime.session(self.filename)
        # RetinaFace/SCRFD declare dynamic axes; the published exports' heads are 640px.
        size = 640
        height, width = image_rgb.shape[1:]
        if height > width:
            new_h, new_w = size, int(size * width / height)
        else:
            new_h, new_w = int(size * height / width), size
        scale = new_h / height
        image = v2.Resize((new_h, new_w), antialias=True)(image_rgb)
        if self.model in ("RetinaFace", "SCRFD"):
            image = image.float()
        image = torch.nn.functional.pad(image, (0, size - new_w, 0, size - new_h))
        if self.model in ("RetinaFace", "SCRFD"):
            image = (image - 127.5) / 128
        elif self.model == "Yunet":
            image = image[[2, 1, 0]]
        boxes, points, scores = [], [], []
        for angle in rotation_angles:
            rotated = image
            if angle:
                rotated, matrix = geometry.transform(
                    image, (size / 2, size / 2), size, 1.0, angle
                )
            batch = rotated.float().unsqueeze(0)
            if self.model == "Yolov8":
                batch = batch / 255
            outputs = self.runtime.run(
                self.filename,
                {session.get_inputs()[0].name: batch},
                [o.name for o in session.get_outputs()],
            )
            b, p, s = self._decode(outputs, size, score_threshold)
            if angle:
                inverse = geometry.invertAffineTransform(matrix)
                corners = b[:, [0, 1, 2, 1, 2, 3, 0, 3]].reshape(-1, 2)
                corners = geometry.trans_points2d(corners, inverse).reshape(-1, 4, 2)
                b = np.concatenate((corners.min(axis=1), corners.max(axis=1)), axis=1)
                p = geometry.trans_points2d(p.reshape(-1, 2), inverse).reshape(-1, 5, 2)
            boxes.append(b)
            points.append(p)
            scores.append(s)
        b = torch.as_tensor(np.concatenate(boxes), device=self.runtime.device)
        p = torch.as_tensor(np.concatenate(points), device=self.runtime.device)
        s = torch.as_tensor(np.concatenate(scores), device=self.runtime.device)
        keep = nms(b, s, 0.4)
        b, p, s = b[keep], p[keep], s[keep]
        margin = (b[:, 2:] - b[:, :2]) * 0.15
        valid = (
            ((p >= (b[:, :2] - margin)[:, None]) & (p <= (b[:, 2:] + margin)[:, None]))
            .all(dim=2)
            .all(dim=1)
        )
        # Exclude detections entirely in padding or outside a rotated image.
        extent = b.new_tensor([new_w, new_h])
        valid &= (torch.minimum(b[:, 2:], extent) > b[:, :2].clamp(min=0)).all(dim=1)
        b, p, s = b[valid], p[valid], s[valid]
        if max_faces > 0 and len(b) > max_faces:
            areas = ((b[:, 2] - b[:, 0]) * (b[:, 3] - b[:, 1])).clamp(min=1)
            order = torch.argsort(
                (s / (s.max() + 1e-6)) ** 2 * 0.8 + areas / (areas.max() + 1e-6) * 0.2,
                descending=True,
            )[:max_faces]
        else:
            order = torch.argsort(s, descending=True)
        return DetectionResult(
            (b[order] / scale).cpu().numpy(),
            (p[order] / scale).cpu().numpy(),
            s[order].cpu().numpy(),
        )
