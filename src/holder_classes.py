from pydantic import BaseModel, Field, model_validator  # , field_validator
# from enum import Enum
# from typing import Any


class InputHolder(BaseModel):

    mode: str = Field()
    max_chunk_size: int = Field(gt=0)
    dataset_path: str = Field(min_length=1)
    k: int = Field(gt=0, lt=1)
    save_directory: str = Field(min_length=1)
    student_answer_path: str = Field(min_length=1)
    max_context_length: int = Field(gt=0)
    student_search_results_path: str = Field(min_length=1)
    question: str = Field()

    @model_validator(mode="after")
    def validate_inputs(self) -> "InputHolder":
        if self.mode == "answer" and not self.question:
            raise ValueError(f"when calling the '{self.mode}' mode, a question"
                             " must be provided as the second argument.")

        return (self)


class Parameter(BaseModel):
    p_name: str = Field(min_length=1)
    p_type: str = Field(min_length=1)

    # p_name: str
    # p_type: str

    # def __str__(self) -> str:
    #     return (
    #         f"{self.p_name} t: {self.p_type}"
    #     )

    # def __str__(self) -> str:
    #     return (
    #         f"\n\t\t\t\"{self.p_name}\": " "{"
    #         f"\n\t\t\t\t\"type\": \"{self.p_type}\"" "\n\t\t\t}"
    #     )

    def __str__(self) -> str:
        return (
            f"\"{self.p_name}\":" "{"
            f"\"type\":\"{self.p_type}\"" "}"
        )


# class Returns(BaseModel):
#     # pass
#     p_type: str = Field(min_length=1)


class FunctDef(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(default="")
    parameters: list[Parameter] = Field()
    returns: str = Field(min_length=1)

    # name: str
    # description: str
    # parameters: list[Parameter]
    # returns: str

    # def __str__(self) -> str:
    #     return (
    #         f"Name: {self.name}\n"
    #         f"Description: {self.description}\n"
    #         f"Params: {''.join(map(str, self.parameters))}\n"
    #         f"Return: {self.returns}"
    #     )

    # def __str__(self) -> str:
    #     return (
    #         "\t{\n"
    #         f"\t\t\"name\": \"{self.name}\",\n"
    #         f"\t\t\"description\": \"{self.description}\",\n"
    #         "\t\t\"parameters\": {"
    #         f"{','.join(map(str, self.parameters))}\n"
    #         "\t\t},\n"
    #         "\t\t\"return\": {"
    #         f"\n\t\t\t\"type\": \"{self.returns}\""
    #         "\n\t}\n"
    #     )

    # def __str__(self) -> str:
    #     return (
    #         "{"
    #         f"\"name\":\"{self.name}\","
    #         f"\"description\":\"{self.description}\","
    #         "\"parameters\":{"
    #         f"{','.join(map(str, self.parameters))}"
    #         "},"
    #         "\"return\":{"
    #         f"\"type\":\"{self.returns}\""
    #         "}}\n"
    #     )

    def __str__(self) -> str:
        return (
            f"\"name\":\"{self.name}\","
            f"\"description\":\"{self.description}\","
            "\"parameters\":"
            f"{','.join(map(str, self.parameters))}"
            f",\"return type\":\"{self.returns}\"\n"
        )


# print(FunctDef(name="n", description="desc",
#                parameters=[Parameter(p_name="a", p_type="number")],
#                returns="number"))


class DefFunctException(Exception):

    e_len: int

    def __init__(self, e_len: int, *args: object) -> None:
        super().__init__(*args)
        self.e_len = e_len


"""
import torch

class Null_LLM():

    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-0.6B",
        *,
        device: str = None,
        dtype: torch.dtype = None,
        trust_remote_code: bool = True,
    ) -> None:

        self._model_name = model_name
        device = "cpu"
        self._device = device

        self.trust = trust_remote_code

    def encode(self, text: str) -> torch.Tensor:
        "
        # Tokenise *text* and return a 2-D
        # ``input_ids`` tensor on the target device.
        "
        ids = [[3838, 374, 279, 2629, 315, 220, 17, 323, 220, 18, 30]]
        return torch.tensor([ids], device=self._device, dtype=torch.long)

    def decode(self, ids: torch.Tensor | list[int]) -> str:
        "Inverse of :py:meth:`encode`. Removes special tokens."
        return "decoded"

    def get_logits_from_input_ids(self, input_ids: list[int]) -> list[float]:
        "
        # Given a list of input token ids, return the raw logits
        # (no softmax) for the next token.
        "
        return [float(x/2) for x in range(1, 24)]

    def get_path_to_vocab_file(self) -> str:
        return "vocab_path"

    def get_path_to_merges_file(self) -> str:
        return "merges_path"

    def get_path_to_tokenizer_file(self) -> str:
        return "merges_path"
"""
