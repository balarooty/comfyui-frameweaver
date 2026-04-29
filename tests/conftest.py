"""Shared test fixtures and mock setup for FrameWeaver tests.

This conftest ensures tests can run offline without ComfyUI, torch,
or GPU hardware by providing lightweight module mocks.
"""

import sys
import types


def _mock(name, attrs=None):
    """Create and register a mock module."""
    if name in sys.modules:
        return sys.modules[name]
    m = types.ModuleType(name)
    if attrs:
        for k, v in attrs.items():
            setattr(m, k, v)
    sys.modules[name] = m
    return m


def pytest_configure(config):
    """Set up module mocks before any imports happen."""

    # ---- torch ----
    torch_mod = _mock("torch", {
        "Tensor": type("Tensor", (), {}),
        "from_numpy": lambda x: x,
        "zeros": lambda *a, **kw: None,
        "cat": lambda *a, **kw: None,
        "clamp": lambda *a, **kw: None,
        "float32": "float32",
        "ones": lambda *a, **kw: None,
        "randn_like": lambda x: x,
        "where": lambda *a: a[1],
        "tensor": lambda *a, **kw: None,
        "linspace": lambda *a, **kw: None,
        "no_grad": lambda: type("ctx", (), {
            "__enter__": lambda s: None,
            "__exit__": lambda s, *a: None,
        })(),
    })
    torch_mod.device = lambda x: x

    cuda_mod = _mock("torch.cuda", {
        "is_available": lambda: False,
        "empty_cache": lambda: None,
    })
    torch_mod.cuda = cuda_mod

    amp_mod = _mock("torch.cuda.amp", {
        "autocast": lambda: type("c", (), {
            "__enter__": lambda s: None,
            "__exit__": lambda s, *a: None,
        })(),
    })
    cuda_mod.amp = amp_mod

    _mock("torch.nn", {})
    _mock("torch.nn.functional", {
        "interpolate": lambda *a, **kw: None,
        "pad": lambda *a, **kw: None,
        "avg_pool2d": lambda *a, **kw: None,
        "conv2d": lambda *a, **kw: None,
    })

    # ---- comfy ----
    comfy_mod = _mock("comfy", {})
    comfy_utils = _mock("comfy.utils", {})
    comfy_mm = _mock("comfy.model_management", {
        "get_torch_device": lambda: "cpu",
        "intermediate_device": lambda: "cpu",
    })
    comfy_mod.utils = comfy_utils
    comfy_mod.model_management = comfy_mm

    # ---- folder_paths ----
    _mock("folder_paths", {
        "models_dir": "/tmp/models",
        "get_input_directory": lambda: "/tmp/input",
        "get_filename_list": lambda x: [],
        "get_output_directory": lambda: "/tmp/output",
    })

    # ---- kornia ----
    kornia_mod = _mock("kornia", {})
    kc = _mock("kornia.color", {
        "rgb_to_lab": lambda x: x,
        "lab_to_rgb": lambda x: x,
    })
    kornia_mod.color = kc

    # ---- PIL ----
    pil = _mock("PIL", {})
    pi = _mock("PIL.Image", {"open": lambda *a: None})
    po = _mock("PIL.ImageOps", {"exif_transpose": lambda x: x})
    pil.Image = pi
    pil.ImageOps = po

    # ---- server ----
    server_mod = _mock("server", {})

    class MockPromptServer:
        instance = type("inst", (), {
            "send_sync": staticmethod(lambda event, data: None),
        })()

    server_mod.PromptServer = MockPromptServer

    # ---- transformers (Whisper) ----
    transformers_mod = _mock("transformers", {})

    class MockWhisperProcessor:
        @classmethod
        def from_pretrained(cls, name):
            return cls()

    class MockWhisperModel:
        @classmethod
        def from_pretrained(cls, name):
            return cls()

        def to(self, device):
            return self

        def eval(self):
            return self

    transformers_mod.WhisperProcessor = MockWhisperProcessor
    transformers_mod.WhisperForConditionalGeneration = MockWhisperModel

    # ---- torchaudio ----
    ta_func = type("ta_func", (), {
        "resample": staticmethod(lambda *a: a[0]),
    })()
    _mock("torchaudio", {"functional": ta_func})
