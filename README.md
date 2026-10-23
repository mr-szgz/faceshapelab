# FaceShapeLab

Detect faces, find landmarks, compare identities, and save aligned crops from still
images or a paused video frame. The two panels keep independent source images and face
selections. No live-camera or VR processing is included.

## Setup

Python 3.12+, Windows, and an NVIDIA CUDA-capable GPU are required for this implementation.
The lockfile selects PyTorch CUDA 12.8 wheels and ONNX Runtime GPU 1.26.0. ONNX Runtime
uses CUDA and CPU graph operations; inference exceptions propagate without retries.

```powershell
uv sync
uv run python download_face_models.py
uv run faceshapelab
```

The standalone downloader needs only `requests`; it does not import the app, Qt, or
inference libraries. `--output-dir PATH` selects its destination. The application reads
`model_assets` beside the project/package directory. It downloads 22 assets from the
pinned VisoMaster-Fusion manifest: four face detectors, eleven landmark models, four
recognizers, and the CSCS adapter, blendshape, and whole-head dependency graphs.

Downloads are sequential, one attempt per asset. Existing filenames raise
`FileExistsError` instead of being overwritten. Network/filesystem exceptions propagate.
Expected and received SHA-256 digests are printed; automated hash verification is in
the model test suite. No models are downloaded automatically when launching the app.

## Workflow

1. Drop an image or video onto either panel. For video, seek to the frame to analyze.
2. Choose a detector and click **Detect Faces**, or click **Detect Landmarks** to run
   detection and the chosen landmark model together. Starting analysis pauses playback.
3. Choose a face in the panel's selection list. Overlay checkboxes control boxes and
   landmarks without altering the source pixels.
4. **Save Face** writes the bounding-box crop. **Save Cropped Face** writes a 512×512
   ArcFace-128 aligned crop. Both save lossless RGB PNGs to the output folder with unique
   filenames and refresh Saved Files. Detected five-point landmarks can align a crop
   without a dense-landmark pass. A rejected dense result is never silently replaced.
5. Detect faces in both panels and click **Compare Selected Faces**. The selected
   recognizer embeds both faces and reports `50 × (1 + cosine_similarity)` on a 0–100
   scale. This is a similarity score, not an identity probability.

Loading another image or receiving another video frame invalidates existing detections.
Results from an older frame are discarded. Analysis runs on one background worker;
widgets and pixmaps stay on the GUI thread. The GPU session cache holds at most four
recently used model graphs.

## Model behavior

- Detectors: RetinaFace, SCRFD, YOLOv8, YuNet. Detection threshold defaults to 0.5;
  up to 20 faces are returned. The backend additionally accepts rotation angles.
- Landmarks: 5, 68, 3d68, 98, 106, 203, 478, TUFA98, TUFA314, ORFormer98, HRFFA.
  All public landmark coordinates are 2D image pixels, including the 3d68 projection.
- The Python landmark API supports five-point input alignment (`from_points`) for the
  original seven models and mean-eye conversion for 203/478/TUFA314. TUFA and ORFormer
  use their upright bbox crops; HRFFA uses an axis-aligned whole-head crop.
- Confidence, ORFormer visibility, and 478 blendshapes are separate outputs. The score
  slider filters only model confidence. It does not filter visibility/blendshapes or
  regression models without confidence outputs.
- HRFFA runs its head detector once per image; faces without a matched head have no
  landmark result. All inference uses FP32, including TUFA and ORFormer.

## Verification

```powershell
uv run pytest
uv run ruff check faceshapelab/main.py faceshapelab/analysis_worker.py faceshapelab/face_analysis download_face_models.py tests/test_face_analysis.py tests/test_analysis_ui.py tests/test_downloader.py
```

The full suite requires the downloaded models and CUDA, and fails when dependencies
are missing. `uv run pytest -m "not models"` runs the geometry/downloader/layout tests.
The real-model suite compares against pinned upstream outputs and exercises blank,
multiple-face, rotated, cropped, and frame-replacement cases. Qt tests click the actual
analysis/save/compare controls. Fixture provenance is in `tests/fixtures/README.md`.

## Attribution

The inference and geometry code is adapted from
[VisoMaster-Fusion](https://github.com/VisoMasterFusion/VisoMaster-Fusion/tree/6563cd21322cf413d0b391aa552f383339636595),
commit `6563cd21322cf413d0b391aa552f383339636595`, under GPLv3 (see `LICENSE`).
Model files are downloaded from their original registry URLs and retain their respective
upstream terms. They are excluded from version control.
