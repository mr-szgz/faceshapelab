# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added cached image and video thumbnails to Saved Files with background generation and refresh controls.
- Added persistent folder selections and face-detection settings.
- Added status-bar feedback for media loading and unsupported or unreadable file drops.
- Added regression coverage for folder selection, media drops, playback, settings, and thumbnail caching.

### Changed

- Updated the Designer layout and synchronized the generated Python UI.

### Fixed

- Cleared stale file-tree selections when changing the browse folder.
- Preserved current panel media when a dropped image or video could not be decoded.
- Kept the latest media selection when files were dropped in rapid succession.
- Released video file handles when replacing media or closing the window.
