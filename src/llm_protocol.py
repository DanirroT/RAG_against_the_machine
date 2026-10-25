from __future__ import annotations
from pathlib import Path
from typing import Protocol


class Small_LLM_ModelBaseProtocol(Protocol):
    """
    Lightweight abstract base class for a small LLM model.

    This class defines the interface for encoding, decoding,
    and retrieving logits from input IDs.

    It is intended to be subclassed by concrete implementations
    that provide specific functionality.
    """

    _model_name: str
    # _tokenizer: (
    #     "ABC_Small_LLM_Model | TokenizersBackend | SentencePieceBackend")

    def encode(self, text: str) -> list[int]:
        """
        Tokenize *text* and return the vector (list of integers).
        """
        pass
        # return self._tokenizer.encode(text)

    def decode(self, ids: list[int]) -> str:
        """Inverse of :py:meth:`encode`. Removes special tokens."""
        pass
        # return str(self._tokenizer.decode(ids))

    def get_path_to_model_files(self) -> dict[str, Path]:
        pass

    def get_logits_from_input_ids(self, input_ids: list[int]) -> list[float]:
        pass
