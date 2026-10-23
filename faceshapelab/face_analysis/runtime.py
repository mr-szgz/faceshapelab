"""Explicit CUDA inference for the pinned image-analysis models."""

from pathlib import Path

import numpy as np
import onnxruntime as ort
import torch


class Runtime:
    def __init__(self, model_dir: Path, device_id: int = 0):
        self.model_dir = Path(model_dir)
        self.device_id = device_id
        self.device = torch.device("cuda", device_id)
        torch.cuda.init()
        ort.preload_dlls(directory=str(Path(torch.__file__).parent / "lib"))
        self.sessions = {}

    def session(self, filename: str):
        if filename not in self.sessions:
            # Bound resident GPU models while switching between UI selections.
            if len(self.sessions) == 4:
                del self.sessions[next(iter(self.sessions))]
            options = ort.SessionOptions()
            session = ort.InferenceSession(
                str(self.model_dir / filename),
                sess_options=options,
                providers=[
                    (
                        "CUDAExecutionProvider",
                        {
                            "device_id": self.device_id,
                            "user_compute_stream": str(
                                torch.cuda.current_stream(self.device).cuda_stream
                            ),
                            "arena_extend_strategy": "kSameAsRequested",
                            "cudnn_conv_algo_search": "HEURISTIC",
                        },
                    ),
                    "CPUExecutionProvider",
                ],
            )
            session.disable_fallback()
            self.sessions[filename] = session
        session = self.sessions.pop(filename)
        self.sessions[filename] = session
        return session

    def run(self, filename: str, inputs: dict[str, torch.Tensor], outputs: list[str]):
        session = self.session(filename)
        binding = session.io_binding()
        tensors = {name: value.contiguous() for name, value in inputs.items()}
        for name, value in tensors.items():
            binding.bind_input(
                name,
                "cuda",
                self.device_id,
                np.float32,
                tuple(value.shape),
                value.data_ptr(),
            )
        for name in outputs:
            binding.bind_output(name, "cuda", self.device_id)
        torch.cuda.synchronize(self.device)
        session.run_with_iobinding(binding)
        binding.synchronize_outputs()
        return binding.copy_outputs_to_cpu()
