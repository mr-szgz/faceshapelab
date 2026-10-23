# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added landmark region mappings for all eleven models and persistent per-region annotation colors.
- Added Procrustes shape comparison between corresponding landmark arrays and automatic region comparisons for the selected faces.
- Added sortable region and embedding similarity tables with percentage displays to two decimal places and `-1` for unavailable region scores.
- Added a movable Compare Faces dock, initially at the bottom, containing the landmark and bounding-box visibility controls and the renamed Compare Face Embeddings button.
- Added expandable Windows folder shortcuts to the Browse files tree, including cross-drive targets, independent shortcut branches, and dragging target files into the comparison panels.

### Changed

- Stacked comparison controls above the embedding and region tables and moved embedding scores out of the status bar.
- Labeled both face selectors Detected Faces and placed them beside their labels below the Controls button grids.

### Fixed

- Cleared outdated comparison scores when selected faces or media changed and excluded landmark results from a different selected model.
- Corrected the video-drop regression test to account for queued frames arriving after playback paused.

## [0.2.0] - 2026-10-23

### Added

- Added independent Original/Face preview selectors with cached 512 × 512 aligned crops.
- Added a small Windows online installer with locked dependency installation, private Python/venv, verified model downloads, and explicit `CUDA_PATH` checks.

- Added CUDA face detection, eleven landmark modes, recognition, and aligned image crops from pinned VisoMaster-Fusion implementations.
- Added a standalone downloader for the 22 image-analysis model assets.
- Connected frame analysis, face selection, overlays, crop saving, and face comparison to both panels.
- Added real-model parity, geometry, downloader, and end-to-end Qt regression tests.
- Added cached image and video thumbnails to Saved Files with background generation and refresh controls.
- Added persistent folder selections and face-detection settings.
- Added status-bar feedback for media loading and unsupported or unreadable file drops.
- Added regression coverage for folder selection, media drops, playback, settings, and thumbnail caching.

### Changed

- Automatically opened the first available aligned face after face or landmark detection.

- Changed face bounding boxes to red and landmarks to yellow, with thicker overlays for the selected face.
- Updated the Designer layout and synchronized the generated Python UI.

### Removed

- Removed VR detector selections while preserving video playback and frame analysis.

### Fixed

- Transformed bounding boxes and landmarks into aligned face coordinates while preserving clean source and exported pixels.
- Reset unavailable face previews when media changes or landmarks are rejected.

- Synchronized CUDA inference with the background worker's PyTorch stream.
- Corrected ArcFace-128 alignment offsets, dark-image landmark preprocessing, and YuNet confidence decoding.
- Excluded detections outside source images and corrected rotated detection coordinates.
- Discarded outdated analysis and export results after frame replacement or window closure.
- Cleared the processing status when either comparison image changed during recognition.
- Cleared stale file-tree selections when changing the browse folder.
- Preserved current panel media when a dropped image or video could not be decoded.
- Kept the latest media selection when files were dropped in rapid succession.
- Released video file handles when replacing media or closing the window.
