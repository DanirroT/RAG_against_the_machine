# import sys
# from typing import Any

from src import InputHolder
import json
from typing import Any
from pathlib import Path
from shutil import rmtree


def val_args(args: list[str]) -> InputHolder:

    # argc = len(args)

    if (args[1] in ['index',  # Index the repository
                    'search',  # Search for a single query
                    'search_dataset',
                    # Process multiple questions and output search results
                    'answer',  # Answer a single question with context
                    'answer_dataset',  # Generate answers from search results
                    'evaluate',  # Evaluate search results against ground truth
                    ]):
        mode = args[1]
    else:
        raise ValueError(f"Unknown First Argument: {args[1]}\n"
                         "Must be: 'ingest', 'search', 'answer' or 'evaluate'")

    inputs: dict[str, str] = {
        "mode": mode,
        "max_chunk_size": "2000",
        "dataset_path": ("data/datasets/UnansweredQuestions/"
                         "dataset_docs_public.json"),
        "k": "10",
        "save_directory": "data/output/search_results",
        "student_answer_path": ("data/output/search_results/"
                                "dataset_docs_public.json"),
        "max_context_length": "2000",
        "student_search_results_path": ("data/output/search_results/"
                                        "dataset_docs_public.json"),
        "question": ""
    }
    fail: bool = False
    next_ins: None | str = None

    for arg in args[1:]:

        if next_ins:
            inputs[next_ins] = arg
            next_ins = None
            continue

        elif arg is args[2] and inputs["mode"] == "answer":
            inputs["question"] = arg

        elif arg in ["--max_chunk_size", "--dataset_path", "--k",
                     "--save_directory", "--student_answer_path",
                     "--max_context_length", "--student_search_results_path"]:

            next_ins = arg[2:]

        elif arg.startswith("--"):
            print(f"Error: Unknown Parameter: {arg}")
            fail = True
            break
        else:
            print("Error: Unknown Argument")
            fail = True
            break

    if fail:
        raise ValueError("\nProgram Stopped")

    return InputHolder(**inputs)  # pyright: ignore


def get_from_json_file(file_path: str) -> Any:

    with open(file_path) as file_obj:
        output = json.load(file_obj)

    return output


def create_file(file_name: str, force: bool = False) -> Path:

    file_path = Path(file_name)

    if file_path.exists():
        if not force:
            print(f"File '{file_name}' "
                  "already exists, do you wish to replace it?")
            answer = input("Y for 'yes', any for 'no': ").strip().lower()
            if answer != "y":
                print("Stopping Program")
                raise FileExistsError(file_name)
            print("Continuing...")
        if file_path.is_file():
            file_path.unlink()
        elif file_path.is_dir():
            if not force:
                print(f"'{file_name}' "
                      "is a directory are you SURE you wish to replace it?")
                answer = input("Y for 'yes', any for 'no': ").strip().lower()
                if answer != "y":
                    print("Stopping Program")
                    raise IsADirectoryError(file_path)
            rmtree(file_path)
        else:
            raise ValueError("Unsupported path type")

    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("x"):
        pass

    return file_path


def create_dir(dir_name: str, force: bool = False) -> Path:

    dir_path = Path(dir_name)

    if dir_path.exists():
        if not force:
            print(f"Directory '{dir_name}' "
                  "already exists, do you wish to replace it?")
            answer = input("Y for 'yes', any for 'no': ").strip().lower()
            if answer != "y":
                print("Stopping Program")
                raise FileExistsError(dir_name)
            print("Continuing...")
        if dir_path.is_file():
            if not force:
                print(f"'{dir_name}' "
                      "is a file are you SURE you wish to replace it?")
                answer = input("Y for 'yes', any for 'no': ").strip().lower()
                if answer != "y":
                    print("Stopping Program")
                    raise FileExistsError(dir_path)
            dir_path.unlink()
        elif dir_path.is_dir():
            if not force:
                print(f"'{dir_name}' "
                      "is a directory are you SURE you wish to replace it?")
                answer = input("Y for 'yes', any for 'no': ").strip().lower()
                if answer != "y":
                    print("Stopping Program")
                    raise IsADirectoryError(dir_path)
            rmtree(dir_path)
        else:
            raise ValueError("Unsupported path type")
    dir_path.mkdir(parents=True)

    return dir_path


def ft_repr(s: str) -> str:
    out: str = ""
    for char in s:
        if char in ["\"", "\\"]:
            out += "\\" + char
        elif char == "\n":
            out += "\n"
        elif char == "\t":
            out += "\t"
        elif char == "\0":
            out += "\0"
        elif char == "\v":
            out += "\v"
        else:
            out += char
    return out


class FileHolder(ABC):

    path: Path

    @abstractmethod
    def __init__(self, path: Path) -> None:
        self.path = path


class PyHolder(FileHolder):
    imports: list[str]
    functs: list[FunctHolder]
    classes: list[ClassHolder]
    start_line: int
    end_line: int

    def __init__(self, path: Path,
                 start_line: int,
                 end_line: int,
                 imports: list[str] | None,
                 functs: list[FunctHolder] | None = None,
                 classes: list[ClassHolder] | None = None) -> None:
        super().__init__(path)
        self.start_line = start_line
        self.end_line = end_line
        self.imports = imports if imports is not None else []
        self.functs = functs if functs is not None else []
        self.classes = classes if classes is not None else []

    def __str__(self) -> str:
        return (
            f"\"path\": {self.path}\n"
            f"\"imports\":\t{'\n\t\t'.join(self.imports)}\n"
            f"\"functs\":\n{'\n\n'.join(map(str, self.functs))}\n\n"
            f"\"classes\":\n{'\n\n\n'.join(map(str, self.classes))}\n"
        )
