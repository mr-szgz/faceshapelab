"""Smoke-test the installed Qt application and a real CUDA model session."""

from pathlib import Path

import torch
from PySide6.QtWidgets import QApplication

from faceshapelab.face_analysis.runtime import Runtime
from faceshapelab.main import MainWindow

app = QApplication([])
window = MainWindow()
runtime = Runtime(Path(__file__).resolve().parent / "model_assets")
runtime.session("det_10g.onnx")
print(f"GPU: {torch.cuda.get_device_name(0)}; PyTorch CUDA: {torch.version.cuda}")
print("Installed Qt application and CUDA model session initialized successfully.")
window.close()
