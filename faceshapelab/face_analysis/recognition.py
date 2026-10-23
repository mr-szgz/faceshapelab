# Adapted from VisoMaster-Fusion, commit 6563cd21322cf413d0b391aa552f383339636595.
# SPDX-License-Identifier: GPL-3.0-only
from dataclasses import dataclass

import numpy as np
import torch
from skimage import transform
from torchvision.transforms import v2

from . import geometry
from .constants import FFHQ_KPS
from .runtime import Runtime

MODELS = {
    "Inswapper128ArcFace": "w600k_r50.onnx",
    "SimSwapArcFace": "simswap_arcface_model.onnx",
    "GhostArcFace": "ghost_arcface_backbone.onnx",
    "CSCSArcFace": "cscs_arcface_model.onnx",
}


@dataclass
class RecognitionResult:
    embedding: np.ndarray
    crop: np.ndarray


def similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(
        50
        * (1 + np.dot(a.ravel(), b.ravel()) / (np.linalg.norm(a) * np.linalg.norm(b)))
    )


class FaceRecognizer:
    def __init__(self, runtime: Runtime, model="Inswapper128ArcFace"):
        self.runtime = runtime
        self.model = model
        self.filename = MODELS[model]

    @torch.inference_mode()
    def recognize(
        self, image_rgb: torch.Tensor, points5: np.ndarray
    ) -> RecognitionResult:
        if self.model == "CSCSArcFace":
            matrix = transform.SimilarityTransform.from_estimate(points5, FFHQ_KPS)
            image = v2.functional.affine(
                image_rgb,
                angle=matrix.rotation * 57.2958,
                translate=tuple(matrix.translation),
                scale=matrix.scale,
                shear=0.0,
                center=(0, 0),
            )
            image = v2.functional.crop(image, 0, 0, 512, 512)
            image = v2.Resize((112, 112), antialias=False)(image)
        else:
            yaw, pitch = geometry.calc_face_yaw_pitch(points5)
            mode = "arcfacemap" if abs(yaw) > 30 or abs(pitch) > 30 else "arcface112"
            image, _ = geometry.warp_face_by_face_landmark_5(
                image_rgb,
                points5,
                112,
                mode,
                interpolation=v2.InterpolationMode.BILINEAR,
            )
        crop = image.permute(1, 2, 0).cpu().numpy().copy()
        image = image.float()
        if self.model == "SimSwapArcFace":
            image = v2.functional.normalize(
                image / 255, (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)
            )
        else:
            image = image / 127.5 - 1
        image = image.unsqueeze(0).contiguous()
        session = self.runtime.session(self.filename)
        embedding = self.runtime.run(
            self.filename,
            {session.get_inputs()[0].name: image},
            [session.get_outputs()[0].name],
        )[0].ravel()
        if self.model == "CSCSArcFace":
            adapter = self.runtime.run(
                "cscs_id_adapter.onnx", {"input": image}, ["output"]
            )[0].ravel()
            embedding = embedding / np.linalg.norm(
                embedding
            ) + adapter / np.linalg.norm(adapter)
        return RecognitionResult(embedding, crop)


@torch.inference_mode()
def aligned_crop(
    image_rgb: torch.Tensor, points5: np.ndarray, size: int = 512
) -> np.ndarray:
    """ArcFace 128 template scaled to the requested square, in original image space."""
    crop, _ = geometry.warp_face_by_face_landmark_5(
        image_rgb,
        points5,
        size,
        "arcface128",
        interpolation=v2.InterpolationMode.BILINEAR,
    )
    return crop.permute(1, 2, 0).cpu().numpy().copy()
