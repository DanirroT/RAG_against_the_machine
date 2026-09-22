from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING
from src.tokenizer_sdk import Small_Tokenizer

if TYPE_CHECKING:
    import torch
    from transformers import (PreTrainedModel)


class ABC_Small_LLM_Model(ABC):
    """
    Lightweight abstract base class for a small LLM model.

    This class defines the interface for encoding, decoding,
    and retrieving logits from input IDs.

    It is intended to be subclassed by concrete implementations
    that provide specific functionality.
    """

    _model_name: str
    _device: str
    _dtype: torch.dtype
    _tokenizer: Small_Tokenizer
    _model: PreTrainedModel | None

    @abstractmethod
    def __init__(
        self,
        mode: bool = True,
        model_name: str = "Qwen/Qwen3-0.6B",
        *,
        device: str | None = None,
        dtype: torch.dtype | None = None,
        trust_remote_code: bool = True,
    ) -> None:
        pass

    @abstractmethod
    def encode(self, text: str) -> list[int]:
        """
        Tokenize *text* and return the vector (list of integers).
        """
        return self._tokenizer.encode(text)

    @abstractmethod
    def decode(self, ids: list[int]) -> str:
        """Inverse of :py:meth:`encode`. Removes special tokens."""
        return self._tokenizer.decode(ids)

    @abstractmethod
    def get_logits_from_input_ids(self, input_ids: list[int]) -> list[float]:
        pass

    @abstractmethod
    def get_path_to_model_files(self) -> dict[str, Path]:
        pass
