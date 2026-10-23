"""Check the installed GPU dependencies without modifying system CUDA."""

from pathlib import Path

import onnxruntime
import torch
from PySide6.QtWidgets import QApplication

app = QApplication([])
torch.cuda.init()
onnxruntime.preload_dlls(directory=str(Path(torch.__file__).parent / "lib"))
print(f"GPU: {torch.cuda.get_device_name(0)}; PyTorch CUDA: {torch.version.cuda}")
