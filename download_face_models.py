# Adapted from VisoMaster-Fusion, commit 6563cd21322cf413d0b391aa552f383339636595.
# SPDX-License-Identifier: GPL-3.0-only
"""Download the image-analysis models. Requires requests; no app imports."""

import argparse
import hashlib
from pathlib import Path

import requests

MODELS = {
    "RetinaFace": (
        "det_10g.onnx",
        "https://github.com/visomaster/visomaster-assets/releases/download/v0.1.0/det_10g.onnx",
        "5838f7fe053675b1c7a08b633df49e7af5495cee0493c7dcf6697200b85b5b91",
    ),
    "SCRFD2.5g": (
        "scrfd_2.5g_bnkps.onnx",
        "https://github.com/visomaster/visomaster-assets/releases/download/v0.1.0/scrfd_2.5g_bnkps.onnx",
        "bc24bb349491481c3ca793cf89306723162c280cb284c5a5e49df3760bf5c2ce",
    ),
    "YoloFace8n": (
        "yoloface_8n.onnx",
        "https://github.com/visomaster/visomaster-assets/releases/download/v0.1.0/yoloface_8n.onnx",
        "84d5bb985b0ea75fc851d7454483897b1494c71c211759b4fec3a22ac196d206",
    ),
    "YunetN": (
        "yunet_n_640_640.onnx",
        "https://github.com/visomaster/visomaster-assets/releases/download/v0.1.0/yunet_n_640_640.onnx",
        "9e65c0213faef0173a3d2e05156b4bf44a45cde598bdabb69203da4a6b7ad61e",
    ),
    "FaceLandmark5": (
        "res50.onnx",
        "https://github.com/visomaster/visomaster-assets/releases/download/v0.1.0/res50.onnx",
        "025db4efa3f7bef9911adc8eb92663608c682696a843cc7e1116d90c223354b5",
    ),
    "FaceLandmark68": (
        "2dfan4.onnx",
        "https://github.com/visomaster/visomaster-assets/releases/download/v0.1.0/2dfan4.onnx",
        "1ceedb108439c7d7b3f92cfa2b25bdc69a1f5f6c8b41da228cb283ca98d4181d",
    ),
    "FaceLandmark3d68": (
        "1k3d68.onnx",
        "https://github.com/visomaster/visomaster-assets/releases/download/v0.1.0/1k3d68.onnx",
        "df5c06b8a0c12e422b2ed8947b8869faa4105387f199c477af038aa01f9a45cc",
    ),
    "FaceLandmark98": (
        "peppapig_teacher_Nx3x256x256.onnx",
        "https://github.com/visomaster/visomaster-assets/releases/download/v0.1.0/peppapig_teacher_Nx3x256x256.onnx",
        "d4aa6dbd0081763a6eef04bf51484175b6a133ed12999bdc83b681a03f3f87d2",
    ),
    "FaceLandmark106": (
        "2d106det.onnx",
        "https://github.com/visomaster/visomaster-assets/releases/download/v0.1.0/2d106det.onnx",
        "f001b856447c413801ef5c42091ed0cd516fcd21f2d6b79635b1e733a7109dbf",
    ),
    "FaceLandmark203": (
        "landmark.onnx",
        "https://github.com/visomaster/visomaster-assets/releases/download/v0.1.0/landmark.onnx",
        "31d22a5041326c31f19b78886939a634a5aedcaa5ab8b9b951a1167595d147db",
    ),
    "FaceLandmark478": (
        "face_landmarks_detector_Nx3x256x256.onnx",
        "https://github.com/visomaster/visomaster-assets/releases/download/v0.1.0/face_landmarks_detector_Nx3x256x256.onnx",
        "6d7932bdefc38871f57dd915b8c723d855e599f29cf4cdf19616fb35d0ed572e",
    ),
    "FaceLandmarkTUFA98": (
        "tufa_vits8_256_98pt.onnx",
        "https://github.com/Glat0s/TUFA-onnx/releases/download/v0.0.1/tufa_vits8_256_98pt.onnx",
        "cf8fab1d1e748b3a4b9f7e8421620659b0219d4c6a69792438086c6d610e52cc",
    ),
    "FaceLandmarkTUFA314": (
        "tufa_vits8_256_314pt.onnx",
        "https://github.com/Glat0s/TUFA-onnx/releases/download/v0.0.1/tufa_vits8_256_314pt.onnx",
        "0e848e4e1a8ce18404f9c42bc83ecd08c048ffda16d061dd7f21e98c967f971c",
    ),
    "FaceLandmarkORFormer98": (
        "orformer_hgnet_wflw_98pt_256.onnx",
        "https://github.com/Glat0s/ORFormer-onnx/releases/download/v0.0.1/orformer_hgnet_wflw_98pt_256.onnx",
        "219835e107a44cebf73ce3b8d592b0ed8e2f25400bee918e8fccab36fbb43f1b",
    ),
    "FaceLandmarkHRFFA": (
        "hrffa_vitt_ibug68_1x3x256x256.onnx",
        "https://github.com/PINTO0309/High-Angle_Robust_Fast_FaceAlignment/releases/download/weights/hrffa_vitt_ibug68_1x3x256x256.onnx",
        "f849af432427ae6d2e9fc1ce2d9bd27134af6e2e3a00060d0d7d312ccfc1d602",
    ),
    "DEIMv2Wholebody49Head": (
        "deimv2_hgnetv2_n_wholebody49_boxes_only_webgpu.onnx",
        "https://github.com/PINTO0309/High-Angle_Robust_Fast_FaceAlignment/releases/download/weights/deimv2_hgnetv2_n_wholebody49_boxes_only_webgpu.onnx",
        "f24d8fa18583c75ce8d802e3d983af9d13a07fdc294267968a206dc79df85d36",
    ),
    "FaceBlendShapes": (
        "face_blendshapes_Nx146x2.onnx",
        "https://github.com/visomaster/visomaster-assets/releases/download/v0.1.0/face_blendshapes_Nx146x2.onnx",
        "79065a18016da3b95f71247ff9ade3fe09b9124903a26a1af85af6d9e2a4faf3",
    ),
    "Inswapper128ArcFace": (
        "w600k_r50.onnx",
        "https://github.com/visomaster/visomaster-assets/releases/download/v0.1.0/w600k_r50.onnx",
        "4c06341c33c2ca1f86781dab0e829f88ad5b64be9fba56e56bc9ebdefc619e43",
    ),
    "SimSwapArcFace": (
        "simswap_arcface_model.onnx",
        "https://github.com/visomaster/visomaster-assets/releases/download/v0.1.0/simswap_arcface_model.onnx",
        "58949c864ab4a89012aaefc117f1ab8548c5f470bbc3889474bca13a412fc843",
    ),
    "GhostArcFace": (
        "ghost_arcface_backbone.onnx",
        "https://github.com/visomaster/visomaster-assets/releases/download/v0.1.0/ghost_arcface_backbone.onnx",
        "18bb8057d1cd3ca39411b8a4dde485fa55783e08ceecaf2352f551ca39cd1357",
    ),
    "CSCSArcFace": (
        "cscs_arcface_model.onnx",
        "https://github.com/visomaster/visomaster-assets/releases/download/v0.1.0/cscs_arcface_model.onnx",
        "cd81a1745a736402d100d32c362918aee46d9a3f58c9c5ecbf0e415cf2df9dc0",
    ),
    "CSCSIDArcFace": (
        "cscs_id_adapter.onnx",
        "https://github.com/visomaster/visomaster-assets/releases/download/v0.1.0/cscs_id_adapter.onnx",
        "288ee88fa208e64846261f9c16f19362db000074b2f4c9000ea49b2311a6d55b",
    ),
}


def download_models(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, (filename, url, expected) in MODELS.items():
        print(f"Downloading {name}", flush=True)
        digest = hashlib.sha256()
        with requests.get(url, stream=True, timeout=10) as response:
            response.raise_for_status()
            with (output_dir / filename).open("xb") as destination:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    destination.write(chunk)
                    digest.update(chunk)
        print(
            f"{filename}\n  expected {expected}\n  received {digest.hexdigest()}",
            flush=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "model_assets",
    )
    args = parser.parse_args()
    download_models(args.output_dir)


if __name__ == "__main__":
    main()
