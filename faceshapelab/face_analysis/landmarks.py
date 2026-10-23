# Adapted from VisoMaster-Fusion, commit 6563cd21322cf413d0b391aa552f383339636595.
# SPDX-License-Identifier: GPL-3.0-only
import math
from dataclasses import dataclass
from itertools import product

import numpy as np
import torch
from torchvision.transforms import v2

from . import geometry as g
from .constants import LANDMARKS_SUBSET_IDXS
from .runtime import Runtime

MODELS = {
    "5": "res50.onnx",
    "68": "2dfan4.onnx",
    "3d68": "1k3d68.onnx",
    "98": "peppapig_teacher_Nx3x256x256.onnx",
    "106": "2d106det.onnx",
    "203": "landmark.onnx",
    "478": "face_landmarks_detector_Nx3x256x256.onnx",
    "tufa98": "tufa_vits8_256_98pt.onnx",
    "tufa314": "tufa_vits8_256_314pt.onnx",
    "orformer98": "orformer_hgnet_wflw_98pt_256.onnx",
    "hrffa": "hrffa_vitt_ibug68_1x3x256x256.onnx",
}
POINT_COUNTS = dict(zip(MODELS, (5, 68, 68, 98, 106, 203, 478, 98, 314, 98, 68)))
HEAD_MODEL = "deimv2_hgnetv2_n_wholebody49_boxes_only_webgpu.onnx"


@dataclass
class LandmarkResult:
    points5: np.ndarray
    points: np.ndarray
    confidence: np.ndarray | None = None
    visibility: np.ndarray | None = None
    blendshapes: np.ndarray | None = None


def prepare_crop(
    image, bbox, points5, size, scale=1.5, from_points=False, mode="arcface128"
):
    if from_points:
        crop, matrix = g.warp_face_by_face_landmark_5(
            image, points5, size, mode, interpolation=v2.InterpolationMode.BILINEAR
        )
    else:
        w, h = bbox[2:] - bbox[:2]
        center = (bbox[:2] + bbox[2:]) / 2
        angle = 0.0
        if points5 is not None:
            dx, dy = points5[1] - points5[0]
            angle = math.degrees(math.atan2(-dy, dx))
        crop, matrix = g.transform(
            image, center, size, size / (max(w, h) * scale), angle
        )
    return crop, g.invertAffineTransform(matrix)


class LandmarkDetector:
    def __init__(self, runtime: Runtime, mode="203"):
        self.runtime = runtime
        self.mode = mode
        self.filename = MODELS[mode]
        self.priors = None

    def _run(self, image, input_name, output_names):
        return self.runtime.run(
            self.filename, {input_name: image.float().unsqueeze(0)}, output_names
        )

    @torch.inference_mode()
    def detect(
        self,
        image_rgb,
        bbox,
        detector_points5,
        score_threshold=0.5,
        from_points=False,
        use_mean_eyes=False,
        head_boxes=None,
    ) -> LandmarkResult | None:
        mode = self.mode
        confidence = visibility = blendshapes = None
        if mode == "5":
            crop, inverse = prepare_crop(
                image_rgb,
                bbox,
                None if not from_points else detector_points5,
                512,
                from_points=from_points,
            )
            mean = torch.tensor([104, 117, 123], device=image_rgb.device).view(3, 1, 1)
            conf, raw = self._run(crop.float() - mean, "input", ["conf", "landmarks"])
            if self.priors is None:
                self.priors = np.array(
                    [
                        [
                            (x + 0.5) * step / 512,
                            (y + 0.5) * step / 512,
                            size / 512,
                            size / 512,
                        ]
                        for step, sizes in (
                            (8, (16, 32)),
                            (16, (64, 128)),
                            (32, (256, 512)),
                        )
                        for y, x in product(range(512 // step), repeat=2)
                        for size in sizes
                    ],
                    dtype=np.float32,
                )
            scores = conf.reshape(-1, 2)[:, 1]
            best = scores.argmax()
            if scores[best] <= 0.1:
                return None
            points = (
                self.priors[best, :2]
                + raw.reshape(-1, 5, 2)[best] * 0.1 * self.priors[best, 2:]
            ) * 512
            points = g.trans_points2d(points, inverse)
            points5, confidence = points, scores[best : best + 1]
        elif mode == "68":
            if from_points:
                crop, inverse = prepare_crop(
                    image_rgb, bbox, detector_points5, 256, from_points=True
                )
            else:
                crop, matrix = g.warp_face_by_bounding_box_for_landmark_68(
                    image_rgb, bbox, (256, 256)
                )
                inverse = g.invertAffineTransform(matrix)
            raw, heatmaps = self._run(
                crop.float() / 255, "input", ["landmarks_xyscore", "heatmaps"]
            )
            points = g.trans_points2d(raw[0, :, :2] * 4, inverse)
            scores = heatmaps.max(axis=(2, 3)).reshape(-1, 1)
            points5, confidence = g.convert_face_landmark_68_to_5(points, scores)
        elif mode == "98":
            if from_points:
                crop, inverse = prepare_crop(
                    image_rgb, bbox, detector_points5, 256, from_points=True
                )
            else:
                crop, detail = g.warp_face_by_bounding_box_for_landmark_98(
                    image_rgb, bbox, (256, 256)
                )
                if crop is None:
                    return None  # Upstream model excludes faces <=20 pixels.
            raw = self._run(crop.float() / 255, "input", ["landmarks_xyscore"])[0][0]
            points = raw[:, :2].copy()
            if from_points:
                points = g.trans_points2d(points * 256, inverse)
            else:
                h, w, top, left, pad = detail
                points = points * [w, h] + [left - pad, top - pad]
            points5, confidence = g.convert_face_landmark_98_to_5(points, raw[:, 2])
        elif mode in ("3d68", "106"):
            crop, inverse = prepare_crop(
                image_rgb, bbox, detector_points5, 192, from_points=from_points
            )
            raw = self._run(crop, "data", ["fc1"])[0][0]
            points = raw.reshape(-1, 3) if mode == "3d68" else raw.reshape(-1, 2)
            points = points[-POINT_COUNTS[mode] :].copy()
            points[:, :2] = (points[:, :2] + 1) * 96
            if mode == "3d68":
                points[:, 2] *= 96
            points = g.trans_points(points, inverse)[:, :2]
            if mode == "3d68":
                points5 = g.convert_face_landmark_68_to_5(points, [])[0]
            else:
                points5 = g.convert_face_landmark_106_to_5(points)
        elif mode == "203":
            crop, inverse = prepare_crop(
                image_rgb, bbox, detector_points5, 224, from_points=from_points
            )
            raw = self._run(crop.float() / 255, "input", ["output", "853", "856"])[2]
            points = g.trans_points2d(raw.reshape(-1, 2) * 224, inverse)
            points5 = g.convert_face_landmark_203_to_5(points, use_mean_eyes)
        elif mode == "478":
            crop, inverse = prepare_crop(
                image_rgb,
                bbox,
                detector_points5,
                256,
                from_points=from_points,
                mode="arcfacemap",
            )
            raw = self._run(
                crop.float() / 255, "input_12", ["Identity", "Identity_1", "Identity_2"]
            )[0]
            points = g.trans_points3d(raw.reshape(478, 3), inverse)[:, :2]
            subset = torch.as_tensor(
                points[LANDMARKS_SUBSET_IDXS],
                dtype=torch.float32,
                device=image_rgb.device,
            ).unsqueeze(0)
            blendshapes = self.runtime.run(
                "face_blendshapes_Nx146x2.onnx", {"input_points": subset}, ["output"]
            )[0].ravel()
            points5 = g.convert_face_landmark_478_to_5(points, use_mean_eyes)
        elif mode in ("tufa98", "tufa314", "orformer98"):
            scale = 1.2 if mode == "orformer98" else 1.15
            crop, inverse = prepare_crop(image_rgb, bbox, detector_points5, 256, scale)
            names = (
                ["landmarks", "occlusion"] if mode == "orformer98" else ["landmarks"]
            )
            outputs = self._run(crop.float() / 255, "image", names)
            points = outputs[0].reshape(-1, 2)
            if mode == "orformer98":
                cells = np.clip((points / 16).astype(np.int32), 0, 15)
                visibility = (
                    1 - outputs[1].reshape(16, 16)[cells[:, 1], cells[:, 0]]
                ).astype(np.float32)
            else:
                points = points * 256
            points = g.trans_points2d(points, inverse)
            if mode == "tufa314":
                points5 = g.convert_face_landmark_314_to_5(points, [], use_mean_eyes)[0]
            else:
                points5 = points[[96, 97, 54, 76, 82]]
        elif mode == "hrffa":
            if head_boxes is None:
                head_boxes = self.detect_heads(image_rgb)
            head = match_head(head_boxes, bbox)
            if head is None:
                return None
            crop, inverse = prepare_crop(image_rgb, head, None, 256, 1.1)
            raw = self._run(crop.float() / 127.5 - 1, "images", ["points"])[0]
            points = g.trans_points2d(raw.reshape(-1, 2) * 256, inverse)
            points5 = g.convert_face_landmark_68_to_5(points, [])[0]
        if confidence is not None and confidence.mean() < score_threshold:
            return None
        return LandmarkResult(
            points5.astype(np.float32),
            points.astype(np.float32),
            confidence,
            visibility,
            blendshapes,
        )

    @torch.inference_mode()
    def detect_heads(self, image_rgb):
        session = self.runtime.session(HEAD_MODEL)
        inp = session.get_inputs()[0]
        image = v2.functional.resize(
            image_rgb,
            inp.shape[2:],
            interpolation=v2.InterpolationMode.BILINEAR,
            antialias=True,
        )
        outputs = self.runtime.run(
            HEAD_MODEL,
            {inp.name: image.float().unsqueeze(0) / 255},
            ["label_xyxy_score"],
        )
        pred = outputs[0].reshape(-1, 6)
        pred = pred[(pred[:, 0] == 7) & (pred[:, 5] >= 0.3)]
        h, w = image_rgb.shape[1:]
        boxes = pred[:, 1:5].copy() * [w, h, w, h]
        boxes[:, [0, 2]] = np.clip(boxes[:, [0, 2]], 0, w - 1)
        boxes[:, [1, 3]] = np.clip(boxes[:, [1, 3]], 0, h - 1)
        valid = ((boxes[:, 2:] - boxes[:, :2]) >= 2).all(axis=1)
        return np.concatenate((boxes[valid], pred[valid, 5:6]), axis=1).astype(
            np.float32
        )


def match_head(head_boxes, face_bbox):
    area = np.prod(face_bbox[2:] - face_bbox[:2])
    intersection = np.clip(
        np.minimum(head_boxes[:, 2:4], face_bbox[2:])
        - np.maximum(head_boxes[:, :2], face_bbox[:2]),
        0,
        None,
    ).prod(axis=1)
    containment = intersection / area
    indices = np.flatnonzero(containment >= 0.5)
    if not len(indices):
        return None
    centers = (head_boxes[indices, :2] + head_boxes[indices, 2:4]) / 2
    distance = np.linalg.norm(centers - (face_bbox[:2] + face_bbox[2:]) / 2, axis=1)
    order = np.lexsort((distance, -containment[indices]))
    return head_boxes[indices[order[0]], :4]
