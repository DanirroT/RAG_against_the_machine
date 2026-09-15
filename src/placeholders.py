from pathlib import Path
import json
from typing import Any
from src import (InputHolder, Chunk,
                 #  ChunkType,
                 Small_LLM_Model)


class FileSearcher():

    _llm: Small_LLM_Model
    database: list[Chunk]
    arg_inputs: InputHolder

    llm_files: dict[str, Path]

    vocab_text_int: dict[str, int]
    vocab_int_text: dict[int, str]

    def __init__(self, query: str, input_dir_path: Path, output_dir_path: Path,
                 database_path: Path, arg_inputs: InputHolder) -> None:

        self.arg_inputs = arg_inputs
        self.input_dir_path = input_dir_path

        self.output_dir_path = output_dir_path
        self.query = query
    #     self.database = self._load_ingest_files(database_path)

    # def _load_ingest_files(self, database_path: Path) -> list[Chunk]:

    #     database_ingest_out: list[Chunk] = []

    #     print()
    #     for path in database_path.rglob("*"):
    #         print()
    #         print(path)
    #         new_file: list[dict[str, Any]]
    #         with path.open("r") as file:
    #             new_file = json.load(file)
    #         add_chunks: list[Chunk] = []
    #         for chunk in new_file:
    #             print(chunk)
    #             add_chunks.append(Chunk(**chunk))

    #         database_ingest_out += add_chunks

    #     return database_ingest_out

    def _load_llm(self) -> None:

        # self._llm = Small_LLM_Model()
        self._llm = Small_LLM_Model(device="cpu")

        self.llm_files = self._llm.get_path_to_model_files()

        with self.llm_files["vocab"].open() as vocab_file:
            self.vocab_text_int: dict[str, int] = json.load(vocab_file)

        self.vocab_int_text = {}

        for k, v in self.vocab_text_int.items():
            self.vocab_int_text[v] = k


class StrAnswerer():

    _llm: Small_LLM_Model
    database: list[Chunk]
    arg_inputs: InputHolder

    llm_files: dict[str, Path]

    vocab_text_int: dict[str, int]
    vocab_int_text: dict[int, str]

    def __init__(self, query: str, input_dir_path: Path, output_dir_path: Path,
                 database_path: Path, arg_inputs: InputHolder) -> None:

        self.arg_inputs = arg_inputs
        self.input_dir_path = input_dir_path

        self.output_dir_path = output_dir_path
        self.query = query
    #     self.database = self._load_ingest_files(database_path)

    # def _load_ingest_files(self, database_path: Path) -> list[Chunk]:

    #     database_ingest_out: list[Chunk] = []

    #     print()
    #     for path in database_path.rglob("*"):
    #         print()
    #         print(path)
    #         new_file: list[dict[str, Any]]
    #         with path.open("r") as file:
    #             new_file = json.load(file)
    #         add_chunks: list[Chunk] = []
    #         for chunk in new_file:
    #             print(chunk)
    #             add_chunks.append(Chunk(**chunk))

    #         database_ingest_out += add_chunks

    #     return database_ingest_out

    def _load_llm(self) -> None:

        # self._llm = Small_LLM_Model()
        self._llm = Small_LLM_Model(device="cpu")

        self.llm_files = self._llm.get_path_to_model_files()

        with self.llm_files["vocab"].open() as vocab_file:
            self.vocab_text_int: dict[str, int] = json.load(vocab_file)

        self.vocab_int_text = {}

        for k, v in self.vocab_text_int.items():
            self.vocab_int_text[v] = k


class FileAnswerer():

    _llm: Small_LLM_Model
    database: list[Chunk]
    arg_inputs: InputHolder

    llm_files: dict[str, Path]

    vocab_text_int: dict[str, int]
    vocab_int_text: dict[int, str]

    def __init__(self, query: str, input_dir_path: Path, output_dir_path: Path,
                 database_path: Path, arg_inputs: InputHolder) -> None:

        self.arg_inputs = arg_inputs
        self.input_dir_path = input_dir_path

        self.output_dir_path = output_dir_path
        self.query = query
    #     self.database = self._load_ingest_files(database_path)

    # def _load_ingest_files(self, database_path: Path) -> list[Chunk]:

    #     database_ingest_out: list[Chunk] = []

    #     print()
    #     for path in database_path.rglob("*"):
    #         print()
    #         print(path)
    #         new_file: list[dict[str, Any]]
    #         with path.open("r") as file:
    #             new_file = json.load(file)
    #         add_chunks: list[Chunk] = []
    #         for chunk in new_file:
    #             print(chunk)
    #             add_chunks.append(Chunk(**chunk))

    #         database_ingest_out += add_chunks

    #     return database_ingest_out

    def _load_llm(self) -> None:

        # self._llm = Small_LLM_Model()
        self._llm = Small_LLM_Model(device="cpu")

        self.llm_files = self._llm.get_path_to_model_files()

        with self.llm_files["vocab"].open() as vocab_file:
            self.vocab_text_int: dict[str, int] = json.load(vocab_file)

        self.vocab_int_text = {}

        for k, v in self.vocab_text_int.items():
            self.vocab_int_text[v] = k


class Evaluator():

    _llm: Small_LLM_Model
    database: list[Chunk]
    arg_inputs: InputHolder

    llm_files: dict[str, Path]

    vocab_text_int: dict[str, int]
    vocab_int_text: dict[int, str]

    def __init__(self, code_questions_file: Path, docs_questions_file: Path,
                 code_answers_file: Path, docs_answers_file: Path,
                 output_dir_path: Path, ingest_database_path: Path,
                 arg_inputs: InputHolder) -> None:

        self.arg_inputs = arg_inputs
        self.code_questions_file = code_questions_file
        self.docs_questions_file = docs_questions_file
        self.code_answers_file = code_answers_file
        self.docs_answers_file = docs_answers_file
        self.output_dir_path = output_dir_path

        # print("current output\n\n")

        # print("\n".join(map(str, ingest_out)))

        # print("output:", output_dir_path)

        # input("starting creation")
        # for obj in ingest_out:
        #     json_path = (output_dir_path /
        #                  obj.path.relative_to(input_dir_path))
        #     json_path = json_path.with_suffix(json_path.suffix + ".json")
        #     json_path.parent.mkdir(parents=True, exist_ok=True)
        #     print("folder created")
        #     with json_path.open("w") as file:
        #         json.dump(obj.to_dict(), file, indent=4, ensure_ascii=False)

        self.database = self._load_ingest_files(ingest_database_path)

    def process(self) -> None:

        self._load_llm()

    def print(self) -> None:

        print("files created")

    def _load_ingest_files(self, ingest_database_path: Path) -> list[Chunk]:

        database_ingest_out: list[Chunk] = []

        print()
        for path in ingest_database_path.rglob("*"):
            print()
            print(path)
            new_file: list[dict[str, Any]]
            with path.open("r") as file:
                new_file = json.load(file)
            add_chunks: list[Chunk] = []
            for chunk in new_file:
                print(chunk)
                add_chunks.append(Chunk(**chunk))

            database_ingest_out += add_chunks

        return database_ingest_out

    def _load_llm(self) -> None:

        # self._llm = Small_LLM_Model()
        self._llm = Small_LLM_Model(device="cpu")

        self.llm_files = self._llm.get_path_to_model_files()

        with self.llm_files["vocab"].open() as vocab_file:
            self.vocab_text_int: dict[str, int] = json.load(vocab_file)

        self.vocab_int_text = {}

        for k, v in self.vocab_text_int.items():
            self.vocab_int_text[v] = k
