"""Capture upstream golden outputs: python scripts/capture_upstream_reference.py CHECKOUT.

CHECKOUT must be VisoMaster-Fusion commit 6563cd21322cf413d0b391aa552f383339636595.
This is a developer tool, never imported by the application.
"""

import ast
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import torch
from PIL import Image
from torchvision.transforms import v2

from download_face_models import MODELS
from faceshapelab.face_analysis.constants import FFHQ_KPS, LANDMARKS_SUBSET_IDXS
from faceshapelab.face_analysis.runtime import Runtime

root = Path(sys.argv[1]) / "app/processors"
geometry = {}
exec(  # noqa: S102 -- Execute the pinned upstream source to capture reference outputs.
    compile(
        (root / "utils/faceutil.py").read_text(),
        str(root / "utils/faceutil.py"),
        "exec",
    ),
    geometry,
)
faceutil = SimpleNamespace(**geometry)


def load(filename, name):
    tree = ast.parse((root / filename).read_text())
    tree.body = [
        n
        for n in tree.body
        if not isinstance(n, ast.ImportFrom) or not (n.module or "").startswith("app.")
    ]
    env = {"faceutil": faceutil, "models_dir": Path("model_assets")}
    exec(compile(tree, str(root / filename), "exec"), env)  # noqa: S102
    return env[name]


runtime = Runtime(Path("model_assets"))
mp = SimpleNamespace(
    models={},
    device="cuda:0",
    device_type="cuda",
    binding_device_id=0,
    model_lock=threading.Lock(),
    main_window=SimpleNamespace(control={}),
    mean_lmk=[1],
    FFHQ_kps=FFHQ_KPS,
    LandmarksSubsetIdxs=LANDMARKS_SUBSET_IDXS,
    normalize=v2.Normalize([0, 0, 0], [1, 1, 1]),
    check_and_clear_pending_build=lambda name: False,
    unload_model=lambda name: None,
)


def load_model(name):
    mp.models[name] = runtime.session(MODELS[name][0])
    return mp.models[name]


mp.load_model = load_model


def run(session, binding):
    torch.cuda.synchronize()
    session.run_with_iobinding(binding)
    binding.synchronize_outputs()


worker = SimpleNamespace(run_ort_with_iobinding=run)
det = load("face_detectors.py", "FaceDetectors")(mp, worker)
land = load("face_landmark_detectors.py", "FaceLandmarkDetectors")(mp, worker)
rec = load("face_swappers.py", "FaceSwappers")(mp, worker)
image = (
    torch.from_numpy(np.array(Image.open("tests/fixtures/astronaut.png")))
    .permute(2, 0, 1)
    .to("cuda")
    .contiguous()
)
gold = {}
for mode in ("RetinaFace", "SCRFD", "Yolov8", "Yunet"):
    info = det.detector_map[mode]
    boxes, points, _, scores = info["function"](
        img=image,
        score=0.5,
        rotation_angles=[0],
        max_num=20,
        input_size=(640, 640),
        ort_session=load_model(info["model_name"]),
        use_landmark_detection=False,
        landmark_detect_mode="203",
        landmark_score=0.5,
        from_points=False,
    )
    gold[mode + "_boxes"] = boxes
    gold[mode + "_points"] = points
    gold[mode + "_scores"] = scores
    print("reference detector", mode, flush=True)
box, points = gold["RetinaFace_boxes"][0], gold["RetinaFace_points"][0]
for mode in (
    "5",
    "68",
    "3d68",
    "98",
    "106",
    "203",
    "478",
    "tufa98",
    "tufa314",
    "orformer98",
    "hrffa",
):
    p5, all_points, scores = land.run_detect_landmark(image, box, points, mode)
    gold["land_" + mode] = all_points
    gold["p5_" + mode] = p5
    gold["scores_" + mode] = np.asarray(scores)
    print("reference landmark", mode, flush=True)
    runtime.sessions.clear()
    mp.models.clear()
for mode in ("Inswapper128ArcFace", "SimSwapArcFace", "GhostArcFace", "CSCSArcFace"):
    embedding, crop = rec.run_recognize_direct(image, points, arcface_model=mode)
    gold["embedding_" + mode] = embedding
    gold["crop_" + mode] = crop.cpu().numpy()
    runtime.sessions.clear()
    mp.models.clear()
    print("reference recognition", mode, flush=True)
np.savez_compressed("tests/fixtures/upstream_reference.npz", **gold)
