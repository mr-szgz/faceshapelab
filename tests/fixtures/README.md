# Face-analysis regression fixtures

`astronaut.png` is the scikit-image astronaut test image: Eileen Collins, photographed
by NASA. It is public domain. The file was saved losslessly from `skimage.data.astronaut()`.

`upstream_reference.npz` contains actual outputs from VisoMaster-Fusion commit
`6563cd21322cf413d0b391aa552f383339636595`: four detectors, eleven landmark modes,
and four recognition pipelines, including the CSCS identity adapter. Reference calls
use CUDA FP32, the original upstream preprocessing/decoding, detection size 640,
score 0.5, bbox-based landmarks, and no temporal tracking or refinement fallback.
The reference harness supplies ONNX sessions and synchronizes I/O without Qt.

Regenerate deliberately, from the repository root, with the pinned upstream checkout:

```powershell
uv run python scripts/capture_upstream_reference.py PATH_TO_PINNED_UPSTREAM_CHECKOUT
```

The harness skips the upstream unused mean-shape pickle preload by supplying a nonempty
mean-shape field. It does not replace the upstream inference or coordinate math.
The downloaded model files are checked independently against all 22 upstream SHA-256
digests. Golden tolerances allow small CUDA numerical differences, not pixel-scale drift.

Intentional departures have independent regression tests instead of changed goldens:
ArcFace-128 shifts every landmark's x coordinate (the upstream slice shifts the first
point's x and y); 68-point low-light CLAHE uses byte Lab luminance correctly; single-angle
rotated detections inverse-map their keypoints; all-invalid geometric detections stay
empty; missing HRFFA heads do not generate synthetic head boxes.
