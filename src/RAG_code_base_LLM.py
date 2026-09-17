from pathlib import Path
from shutil import rmtree
from typing import Any
from src import (get_from_json_file, create_file, create_dir,
                 InputHolder,
                 Ingestor, StrSearcher
                 #  ChunkType, Chunk, ChunkRaw, ChunkScorePair
                 #  DefFunctException, Small_LLM_Model
                 )
from .placeholders import (StrAnswerer, FileAnswerer,
                           FileSearcher, Evaluator)


class RAGCodeBaseLLM():

    # _llm: Small_LLM_Model

    dataset: dict[str, Any]

    arg_inputs: InputHolder

    save_directory: Path
    student_answer_path: Path
    student_search_results_path: Path

    llm_files: dict[str, str]

    vocab_text_int: dict[str, int]
    vocab_int_text: dict[int, str]

    def __init__(self, arg_inputs: InputHolder, mode: bool = True) -> None:

        force = True

        if arg_inputs:
            # print("arg_inputs Exists")

            if arg_inputs.mode in ["search_dataset", "answer_dataset"]:
                self.save_directory = create_dir(
                    arg_inputs.save_directory, force)
                print(f"{self.save_directory} Created")

            # if arg_inputs.mode == "answer":
            #     self.student_answer_path = create_file(
            #         arg_inputs.student_answer_path, force)
            #     print(f"{self.student_answer_path} Created")

            if arg_inputs.mode == "search":
                self.student_search_results_path = create_file(
                    arg_inputs.student_search_results_path, force)
                print(f"{self.student_search_results_path} Created")

            self.dataset = get_from_json_file(arg_inputs.dataset_path)
            print(f"{arg_inputs.dataset_path} Loaded")
        else:
            raise ValueError("No Arguments were passed to the Class")

        self.arg_inputs = arg_inputs

        if self.arg_inputs.mode == "index":
            # input_dir_str = self.dataset
            input_dir_str = "data/to_process/"
            # output_dir_str = save_directory
            output_dir_str = "data/processed/"

            self._ingest(input_dir_str, output_dir_str)
            print(f"Ingestion complete! Indices saved under {output_dir_str}")
            return

        elif self.arg_inputs.mode == "search":
            input_dir_str = "data/processed/"
            output_file_str = "data/search/search.txt"
            lookup = ""
            self._str_search(lookup,
                             input_dir_str, output_file_str)
            print(f"Search Finished! Check in {output_file_str}")

        elif self.arg_inputs.mode == "search_dataset":
            input_dir_str = "data/processed/"
            output_file_str = "data/search/StudentSearchResults.json"
            lookup = ""
            self._file_search(lookup, input_dir_str, output_file_str)
            print(f"Search Finished! Check in {output_file_str}")

        elif self.arg_inputs.mode == "answer":
            input_dir_str = "data/processed/"
            output_file_str = "data/answer/answer.txt"
            self._str_answer(input_dir_str, output_file_str)
            print(f"Answer Provided! Check in {output_file_str}")

        elif self.arg_inputs.mode == "answer_dataset":
            input_dir_str = "data/processed/"
            output_file_str = "data/answer/StudentSearchResultsAndAnswer.json"
            self._file_answer(input_dir_str, output_file_str)
            print(f"Answer Provided! Check in {output_file_str}")

        elif self.arg_inputs.mode == "evaluate":
            code_questions_str = ("data/datasets/UnansweredQuestions/"
                                  "dataset_code_public.json")
            docs_questions_str = ("data/datasets/UnansweredQuestions/"
                                  "dataset_docs_public.json")
            code_answers_str = ("data/datasets/AnsweredQuestions/"
                                "dataset_code_public.json")
            docs_answers_str = ("data/datasets/AnsweredQuestions/"
                                "dataset_docs_public.json")
            output_dir_str = "data/eval_results/"

            self._evaluate(code_questions_str, docs_questions_str,
                           code_answers_str, docs_answers_str,
                           output_dir_str)
            print(f"Evaluation Finished! Check in {output_dir_str}")

    def _ingest(self, input_dir_str: str, output_dir_str: str) -> None:

        input_dir_path = Path(input_dir_str)
        if not input_dir_path.exists():
            raise ValueError(f"Path '{input_dir_str}' does not exist")
        if not input_dir_path.is_dir():
            raise ValueError(f"Path '{input_dir_str}' is not a Directory")

        output_dir_path = Path(output_dir_str)
        if output_dir_path.exists():
            # if not output_dir_path.is_dir():
            #     answer = input(
            #         f"'{output_dir_str}' exists but is not a directory."
            #         "\nReplace it with a directory? [y/N]: "
            #     ).strip().lower()
            # else:
            #     answer = input(
            #         f"Directory '{output_dir_str}' already exists.\n"
            #         "Overwrite its contents? [y/N]: "
            #     ).strip().lower()

            # if answer != "y":
            #     print("Operation cancelled.")
            #     raise FileExistsError
            # else:
            if output_dir_path.is_file():
                output_dir_path.unlink()
            else:
                rmtree(output_dir_path)
        output_dir_path.mkdir(parents=True)

        print("input:", input_dir_path)

        Ingestor(input_dir_path, output_dir_path, self.arg_inputs)
        # ingestor = Ingestor(input_dir_path, output_dir_path, self.arg_inputs)
        # ingestor.process()
        # input()
        # ingestor.print()

    def _str_search(self, lookup: str,
                    input_dir_str: str, output_file_str: str) -> None:

        input_dir_path = Path(input_dir_str)
        output_dir_path = Path(output_file_str)
        if output_dir_path.exists():
            # if not output_dir_path.is_dir():
            #     answer = input(
            #         f"'{output_file_str}' exists but is not a directory."
            #         "\nReplace it with a directory? [y/N]: "
            #     ).strip().lower()
            # else:
            #     answer = input(
            #         f"Directory '{output_file_str}' already exists.\n"
            #         "Overwrite its contents? [y/N]: "
            #     ).strip().lower()

            # if answer != "y":
            #     print("Operation cancelled.")
            #     raise FileExistsError
            # else:
            if output_dir_path.is_file():
                output_dir_path.unlink()
            else:
                rmtree(output_dir_path)

        create_file(output_dir_path, force=True)

        query = self.arg_inputs.question

        StrSearcher(query, input_dir_path, output_dir_path,
                    Path("data/processed/"), self.arg_inputs)

    def _file_search(self, lookup: str,
                     input_dir_str: str, output_file_str: str) -> None:

        input_dir_path = Path(input_dir_str)
        output_dir_path = Path(output_file_str)
        if output_dir_path.exists():
            # if not output_dir_path.is_dir():
            #     answer = input(
            #         f"'{output_file_str}' exists but is not a directory."
            #         "\nReplace it with a directory? [y/N]: "
            #     ).strip().lower()
            # else:
            #     answer = input(
            #         f"Directory '{output_file_str}' already exists.\n"
            #         "Overwrite its contents? [y/N]: "
            #     ).strip().lower()

            # if answer != "y":
            #     print("Operation cancelled.")
            #     raise FileExistsError
            # else:
            if output_dir_path.is_file():
                output_dir_path.unlink()
            else:
                rmtree(output_dir_path)

        create_file(output_dir_path, force=True)
        
        query = self.arg_inputs.question
        FileSearcher(query, input_dir_path, output_dir_path,
                     Path("data/processed/"), self.arg_inputs)

    def _str_answer(self, input_dir_str: str, output_file_str: str) -> None:

        pass

        input_dir_path = Path(input_dir_str)
        output_dir_path = Path(output_file_str)
        if output_dir_path.exists():
            if output_dir_path.is_file():
                output_dir_path.unlink()
            else:
                rmtree(output_dir_path)
        output_dir_path.mkdir(parents=True)
        query = self.arg_inputs.question

        StrAnswerer(query, input_dir_path, output_dir_path,
                    Path("data/processed/"), self.arg_inputs)

    def _file_answer(self, input_dir_str: str, output_file_str: str) -> None:

        pass

        input_dir_path = Path(input_dir_str)
        output_dir_path = Path(output_file_str)
        if output_dir_path.exists():
            if output_dir_path.is_file():
                output_dir_path.unlink()
            else:
                rmtree(output_dir_path)
        output_dir_path.mkdir(parents=True)
        query = self.arg_inputs.question

        FileAnswerer(query, input_dir_path, output_dir_path,
                     Path("data/processed/"), self.arg_inputs)

    def _evaluate(self, code_questions_str: str, docs_questions_str: str,
                  code_answers_str: str, docs_answers_str: str,
                  output_dir_str: str) -> None:

        pass

        code_questions_file = Path(code_questions_str)
        docs_questions_file = Path(docs_questions_str)
        code_answers_file = Path(code_answers_str)
        docs_answers_file = Path(docs_answers_str)

        output_dir_path = Path(output_dir_str)
        if output_dir_path.exists():
            if output_dir_path.is_file():
                output_dir_path.unlink()
            else:
                rmtree(output_dir_path)
        output_dir_path.mkdir(parents=True)
        pass
        Evaluator(code_questions_file, docs_questions_file, code_answers_file,
                  docs_answers_file, output_dir_path,
                  Path("data/processed/"), self.arg_inputs)

    # def _load_llm(self, mode: bool = True) -> None:

    #     self._llm = Small_LLM_Model(mode)

    #     self.llm_files = self._llm.get_path_to_model_files()

    #     with self.llm_files["vocab"].open() as vocab_file:
    #         self.vocab_text_int: dict[str, int] = json.load(vocab_file)

    #     self.vocab_int_text = {}

    #     for k, v in self.vocab_text_int.items():
    #         self.vocab_int_text[v] = k
