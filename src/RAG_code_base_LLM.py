from pathlib import Path
from src import (create_file, create_dir, InputHolder,
                 Ingestor, StrSearcher,
                 FileSearcher, StrAnswer, FileAnswer
                 #  ChunkType, Chunk, ChunkRaw, ChunkScorePair
                 #  DefFunctException, Small_LLM_ModelBaseProtocol
                 )
from .placeholders import (Evaluator)

"""
class RAGCodeBaseLLM():

    arg_inputs: InputHolder
    force_create: bool

    def __init__(self, arg_inputs: InputHolder, mode: bool = True) -> None:

        self.force_create = mode

        if not arg_inputs:
            raise ValueError("No Arguments were passed to the Class")

        self.arg_inputs = arg_inputs

        if self.arg_inputs.mode == "index":
            # input_dir_str = self.dataset
            # input_dir_str = "data/to_process/"
            input_dir_str = "../vllm-0.10.1/"
            # output_dir_str = save_directory
            output_dir_str = "data/processed/"

            self._ingest(input_dir_str, output_dir_str)
            print(f"Ingestion complete! Indices saved under {output_dir_str}")
            return

        elif self.arg_inputs.mode == "search":
            input_dir_str = "data/processed/"
            output_file_str = "data/search/search.json"
            self._str_search(input_dir_str, output_file_str)
            print(f"Search Finished! Check in {output_file_str}")

        elif self.arg_inputs.mode == "search_dataset":
            input_dir_str = "data/processed/"
            # output_file_str = "data/search/StudentSearchResults.json"
            output_file_str = self.arg_inputs.student_search_results_path
            self._file_search(input_dir_str, output_file_str)
            print(f"Search Finished! Check in {output_file_str}")

        elif self.arg_inputs.mode == "answer":
            input_dir_str = "data/processed/"
            output_file_str = "data/answer/answer.json"
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

        output_dir_path = create_dir(output_dir_str, self.force_create)

        Ingestor(input_dir_path, output_dir_path, self.arg_inputs)

    def _str_search(self, input_dir_str: str, output_file_str: str) -> None:

        input_dir_path = Path(input_dir_str)
        output_dir_path = Path(output_file_str)

        create_file(output_dir_path, force=self.force_create)

        StrSearcher(input_dir_path, output_dir_path, self.arg_inputs)

    def _file_search(self, input_dir_str: str, output_file_str: str) -> None:

        input_dir_path = Path(input_dir_str)
        output_dir_path = Path(output_file_str)
        create_file(output_dir_path, force=self.force_create)

        FileSearcher(input_dir_path, output_dir_path, self.arg_inputs)

    def _str_answer(self, input_dir_str: str, output_file_str: str) -> None:

        input_dir_path = Path(input_dir_str)
        output_dir_path = Path(output_file_str)
        create_file(output_dir_path, force=self.force_create)

        StrAnswer(input_dir_path, output_dir_path, self.arg_inputs)

    def _file_answer(self, input_dir_str: str, output_file_str: str) -> None:

        input_dir_path = Path(input_dir_str)
        output_dir_path = Path(output_file_str)
        create_file(output_dir_path, force=self.force_create)

        FileAnswer(input_dir_path, output_dir_path, self.arg_inputs)

    def _evaluate(self, code_questions_str: str, docs_questions_str: str,
                  code_answers_str: str, docs_answers_str: str,
                  output_dir_str: str) -> None:

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
"""


def ingest(arg_inputs: InputHolder,
           input_dir_str: str, output_dir_str: str,
           force_create: bool = False) -> None:

    input_dir_path = Path(input_dir_str)
    if not input_dir_path.exists():
        raise ValueError(f"Path '{input_dir_str}' does not exist")
    if not input_dir_path.is_dir():
        raise ValueError(f"Path '{input_dir_str}' is not a Directory")

    output_dir_path = create_dir(output_dir_str, force_create)

    Ingestor(input_dir_path, output_dir_path, arg_inputs)


def str_search(arg_inputs: InputHolder,
               input_dir_str: str, output_file_str: str,
               force_create: bool = False) -> None:

    input_dir_path = Path(input_dir_str)
    if not input_dir_path.exists():
        raise ValueError(f"Path '{input_dir_str}' does not exist")
    if not input_dir_path.is_dir():
        raise ValueError(f"Path '{input_dir_str}' is not a Directory")

    output_dir_path = create_file(output_file_str, force_create)

    StrSearcher(input_dir_path, output_dir_path, arg_inputs)


def file_search(arg_inputs: InputHolder,
                input_dir_str: str, output_file_str: str,
                force_create: bool = False) -> None:

    input_dir_path = Path(input_dir_str)
    if not input_dir_path.exists():
        raise ValueError(f"Path '{input_dir_str}' does not exist")
    if not input_dir_path.is_dir():
        raise ValueError(f"Path '{input_dir_str}' is not a Directory")

    output_dir_path = create_file(output_file_str, force_create)

    FileSearcher(input_dir_path, output_dir_path, arg_inputs)


def str_answer(arg_inputs: InputHolder,
               input_dir_str: str, output_file_str: str,
               force_create: bool = False) -> None:

    input_dir_path = Path(input_dir_str)
    if not input_dir_path.exists():
        raise ValueError(f"Path '{input_dir_str}' does not exist")
    if not input_dir_path.is_dir():
        raise ValueError(f"Path '{input_dir_str}' is not a Directory")

    output_dir_path = create_file(output_file_str, force_create)

    StrAnswer(input_dir_path, output_dir_path, arg_inputs)


def file_answer(arg_inputs: InputHolder,
                input_dir_str: str, output_file_str: str,
                force_create: bool = False) -> None:

    input_dir_path = Path(input_dir_str)
    if not input_dir_path.exists():
        raise ValueError(f"Path '{input_dir_str}' does not exist")
    if not input_dir_path.is_dir():
        raise ValueError(f"Path '{input_dir_str}' is not a Directory")

    output_dir_path = create_file(output_file_str, force_create)

    FileAnswer(input_dir_path, output_dir_path, arg_inputs)


def evaluate(arg_inputs: InputHolder,
             code_questions_str: str, docs_questions_str: str,
             code_answers_str: str, docs_answers_str: str,
             output_dir_str: str, force_create: bool = False) -> None:

    code_questions_file = Path(code_questions_str)
    if not code_questions_file.exists():
        raise ValueError(f"Path '{code_questions_str}' does not exist")
    if code_questions_file.is_dir():
        raise ValueError(f"Path '{code_questions_str}' is a Directory")

    docs_questions_file = Path(docs_questions_str)
    if not docs_questions_file.exists():
        raise ValueError(f"Path '{docs_questions_str}' does not exist")
    if docs_questions_file.is_dir():
        raise ValueError(f"Path '{docs_questions_str}' is a Directory")

    code_answers_file = Path(code_answers_str)
    if not code_answers_file.exists():
        raise ValueError(f"Path '{code_answers_str}' does not exist")
    if code_answers_file.is_dir():
        raise ValueError(f"Path '{code_answers_str}' is a Directory")

    docs_answers_file = Path(docs_answers_str)
    if not docs_answers_file.exists():
        raise ValueError(f"Path '{docs_answers_str}' does not exist")
    if docs_answers_file.is_dir():
        raise ValueError(f"Path '{docs_answers_str}' is a Directory")

    output_dir_path = create_dir(output_dir_str, force_create)

    Evaluator(code_questions_file, docs_questions_file, code_answers_file,
              docs_answers_file, output_dir_path,
              Path("data/processed/"), arg_inputs)


def rag_code_base_llm(arg_inputs: InputHolder,
                      force_create: bool = True) -> None:

    if not isinstance(arg_inputs, InputHolder):
        raise ValueError("No Arguments were passed to the Class")

    if arg_inputs.mode == "index":
        # input_dir_str = dataset
        # input_dir_str = "data/to_process/"
        input_dir_str = "../vllm-0.10.1/"
        # output_dir_str = save_directory
        output_dir_str = "data/processed/"

        ingest(arg_inputs, input_dir_str, output_dir_str, force_create)
        print(f"Ingestion complete! Indices saved under {output_dir_str}")
        return

    elif arg_inputs.mode == "search":
        input_dir_str = "data/processed/"
        output_file_str = "data/search/search.json"
        str_search(arg_inputs, input_dir_str, output_file_str, force_create)
        print(f"Search Finished! Check in {output_file_str}")

    elif arg_inputs.mode == "search_dataset":
        input_dir_str = "data/processed/"
        # output_file_str = "data/search/StudentSearchResults.json"
        output_file_str = arg_inputs.student_search_results_path
        file_search(arg_inputs, input_dir_str, output_file_str, force_create)
        print(f"Search Finished! Check in {output_file_str}")

    elif arg_inputs.mode == "answer":
        input_dir_str = "data/processed/"
        output_file_str = "data/answer/answer.json"
        str_answer(arg_inputs, input_dir_str, output_file_str, force_create)
        print(f"Answer Provided! Check in {output_file_str}")

    elif arg_inputs.mode == "answer_dataset":
        input_dir_str = "data/processed/"
        output_file_str = "data/answer/StudentSearchResultsAndAnswer.json"
        file_answer(arg_inputs, input_dir_str, output_file_str, force_create)
        print(f"Answer Provided! Check in {output_file_str}")

    elif arg_inputs.mode == "evaluate":
        code_questions_str = ("data/datasets/UnansweredQuestions/"
                              "dataset_code_public.json")
        docs_questions_str = ("data/datasets/UnansweredQuestions/"
                              "dataset_docs_public.json")
        code_answers_str = ("data/datasets/AnsweredQuestions/"
                            "dataset_code_public.json")
        docs_answers_str = ("data/datasets/AnsweredQuestions/"
                            "dataset_docs_public.json")
        output_dir_str = "data/eval_results/"

        evaluate(arg_inputs, code_questions_str, docs_questions_str,
                 code_answers_str, docs_answers_str,
                 output_dir_str, force_create)
        print(f"Evaluation Finished! Check in {output_dir_str}")
