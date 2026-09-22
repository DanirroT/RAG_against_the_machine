from __future__ import annotations
from dotenv import load_dotenv
from pathlib import Path
from huggingface_hub import hf_hub_download
from typing import TYPE_CHECKING, cast
from src import ABC_Small_LLM_Model

if TYPE_CHECKING:
    from transformers import (TokenizersBackend, SentencePieceBackend)


# logging.set_verbosity_error()  # keep the console clean


class Small_Tokenizer(ABC_Small_LLM_Model):
    """
    Lightweight wrapper around a Hugging Face tokenizer for fast,
    low-memory experimentation.
    """

    _model_name: str
    _tokenizer: TokenizersBackend | SentencePieceBackend

    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-0.6B",
        *,
        trust_remote_code: bool = True,
    ) -> None:

        self._model_name = model_name

        load_dotenv()
        from transformers import (AutoTokenizer)

        # --- load tokenizer & model -----------------------------------------
        self._tokenizer = AutoTokenizer.from_pretrained(
            model_name, trust_remote_code=trust_remote_code
        )
        if self._tokenizer.pad_token_id is None:
            # ensure we have a pad token to keep batch helpers happy
            self._tokenizer.pad_token_id = self._tokenizer.eos_token_id

    def encode(self, text: str) -> list[int]:
        """
        Tokenize *text* and return the vector (list of integers).
        """
        return cast(list[int], self._tokenizer.encode(
            text, add_special_tokens=False))

        # tokenized_prompt = torch.tensor([ids], device=self._device,
        #                                 dtype=torch.long)

        # tokenized_int_prompt: list[int] = (  # pyright: ignore
        #     tokenized_prompt[0].tolist())  # pyright: ignore

        # return (tokenized_int_prompt)

    def decode(self, ids: list[int]) -> str:
        """Inverse of :py:meth:`encode`. Removes special tokens."""
        return cast(str, self._tokenizer.decode(ids, skip_special_tokens=True))

    def get_path_to_model_files(self) -> dict[str, Path]:
        vocab_file_name = self._tokenizer.vocab_files_names.get(
            'vocab_file', "vocab.json")
        vocab_path = hf_hub_download(
            repo_id=self._model_name,
            filename=vocab_file_name
        )

        merges_file_name = self._tokenizer.vocab_files_names.get(
            'merges_file', "merges.txt")
        merges_path = hf_hub_download(
            repo_id=self._model_name,
            filename=merges_file_name
        )

        tokenizer_file_name = self._tokenizer.vocab_files_names.get(
            'tokenizer_file', "tokenizer.json")
        tokenizer_path = hf_hub_download(
            repo_id=self._model_name,
            filename=tokenizer_file_name
        )
        return {"vocab": Path(vocab_path),
                "merges": Path(merges_path),
                "tokenizer": Path(tokenizer_path)}

    def get_logits_from_input_ids(self, input_ids: list[int]) -> list[float]:
        raise NotImplementedError(
            "Small_Tokenizer does not implement get_logits_from_input_ids. "
            "Use a concrete LLM model class for this functionality.")
