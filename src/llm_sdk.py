from dotenv import load_dotenv
from pathlib import Path
import torch
from transformers import (AutoModelForCausalLM, PreTrainedModel)
from src import ABC_Small_LLM_Model, Small_Tokenizer


# logging.set_verbosity_error()  # keep the console clean


class Small_LLM_Model(ABC_Small_LLM_Model):
    """
    Utility class wrapping a lightweight Hugging Face causal-LM for fast,
    low-memory experimentation.

    Parameters
    ----------
    model_name: str, default="Qwen/Qwen3-0.6B"
        Identifier of the model on the HF Hub.
    device: str | None, default=None
        Computation device. If *None* we automatically select ``mps``
        when available on macOS, ``cuda`` when available,
        otherwise we fall back to ``cpu``.
    dtype: torch.dtype | None, default=None
        Numerical precision. When using a GPU or MPS we default to ``float16``
        to keep memory usage reasonable; on CPU we keep ``float32``
        for maximum compatibility.
    """

    _model_name: str
    _device: str
    _dtype: torch.dtype
    _tokenizer: Small_Tokenizer
    _model: PreTrainedModel | None

    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-0.6B",
        *,
        device: str | None = None,
        dtype: torch.dtype | None = None,
        trust_remote_code: bool = True,
    ) -> None:

        self._model_name = model_name

        load_dotenv()

        # --- load tokenizer & model -----------------------------------------
        self._tokenizer = Small_Tokenizer(
            model_name, trust_remote_code=trust_remote_code)

        # Auto-select device with priority: mps > cuda > cpu
        if device is None:
            if torch.backends.mps.is_available():
                device = "mps"
            elif torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"
        self._device = device

        if dtype is None:
            dtype = (torch.float16 if self._device in ["cuda", "mps"]
                     else torch.float32)
        self._dtype = dtype

        self._model = (
            AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=self._dtype,
                device_map="auto" if self._device == "cuda" else None,
                trust_remote_code=trust_remote_code,
            ))
        self._model.to(self._device)
        self._model.eval()

        # switch to inference-only mode
        for p in self._model.parameters():
            p.requires_grad = False

    def encode(self, text: str) -> list[int]:
        """
        Tokenize *text* and return the vector (list of integers).
        """
        return self._tokenizer.encode(text)

    def decode(self, ids: list[int]) -> str:
        """Inverse of :py:meth:`encode`. Removes special tokens."""
        return self._tokenizer.decode(ids)

    def get_logits_from_input_ids(self, input_ids: list[int]) -> list[float]:
        """
        Given a list of input token ids, return the raw logits
        (no softmax) for the next token.
        """
        if not self._model:
            raise KeyError("Model is not Currently Loaded."
                           "Logits cannot be Generated")
        input_tensor = torch.tensor([input_ids], device=self._device,
                                    dtype=torch.long)
        with torch.no_grad():
            out = self._model(input_ids=input_tensor)
        # Get logits for the last token in the sequence for the batch
        logits = out.logits[0, -1].tolist()
        return [float(x) for x in logits]

    def get_path_to_model_files(self) -> dict[str, Path]:
        return self._tokenizer.get_path_to_model_files()
