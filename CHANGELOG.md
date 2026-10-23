# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added expandable Windows folder shortcuts to the Browse files tree, including cross-drive targets, independent shortcut branches, and dragging target files into the comparison panels.

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
