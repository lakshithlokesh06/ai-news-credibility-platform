def select_device(device_preference: str = "auto") -> str:
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError(
            "PyTorch is required for transformer training and inference. Install backend transformer dependencies."
        ) from exc

    if device_preference == "cpu":
        return "cpu"
    if device_preference == "cuda":
        if torch.cuda.is_available():
            return "cuda"
        raise RuntimeError("CUDA was requested but is not available.")
    if device_preference == "mps":
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        raise RuntimeError("Apple MPS was requested but is not available.")

    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"

