# import sys
from typing import cast

from src import InputHolder
from pydantic_core import ErrorDetails
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


def str_error(error_type: str, field: str, msg: str, input_raw: str,
              expected: int | None) -> None:

    input_processed = len(input_raw)

    if error_type == "string_too_short":
        if not input_processed:
            print(f"'{field}' cannot be empty.")
        else:
            print(
                f"'{field}' should be larger than or equal to {expected}",
                f"char. Got {input_processed}")
    elif error_type == "string_too_long":
        print(
            f"'{field}' should be smaller than or equal to {expected} char.",
            f"Got {input_processed}")
    else:
        print("Unknown Error:", msg)


def int_error(error_type: str, field: str, msg: str, input_raw: int,
              expected: int | None) -> None:

    input_processed = input_raw

    if error_type == "int_parsing":
        print(f"'{field}' must an integer. Got {input_processed}")
    elif error_type == "less_than_equal":
        if expected == 0:
            print(
                f"'{field}' must be positive. Got {input_processed}")
        else:
            print(
                f"'{field}' should be less than or equal to {expected}.",
                f"Got {input_processed}")
    elif error_type == "greater_than_equal":
        if expected == 0:
            print(
                f"'{field}' must be negative. Got {input_processed}")
        else:
            print(
                f"'{field}' should be greater than or equal to {expected}.",
                f"Got {input_processed}")
    else:
        print("Unknown Error:", msg)


def float_error(error_type: str, field: str, msg: str, input_raw: float,
                expected: float | None) -> None:

    input_processed = input_raw

    if error_type == "float_parsing":
        print(f"'{field}' must a number. Got {input_processed}")
    elif error_type == "less_than_equal":
        if expected == 0:
            print(
                f"'{field}' must be positive. Got {input_processed}")
        else:
            print(
                f"'{field}' should be less than or equal to {expected}.",
                f"Got {input_processed}")
    elif error_type == "greater_than_equal":
        if expected == 0:
            print(
                f"'{field}' must be negative. Got {input_processed}")
        else:
            print(f"'{field}' should be greater than or equal to {expected}.",
                  f"Got {input_processed}")
    else:
        print("Unknown Error:", msg)


# if (min == 0 and max == 100
#    and field_float < min and field_float > max):
#    print("SpaceStation Oxygen Level be a percentage.")


def bool_error(error_type: str, field: str, msg: str, input_raw: bool) -> None:

    input_processed = input_raw

    if error_type == "bool_parsing":
        print(f"'{field}' must a valid boolean. Got {input_processed}")
    else:
        print("Unknown Error:", msg)


# def date_error(error_type: str, field: str, msg: str, input_raw: date,
#                expected: str | None) -> None:

#     input_processed = input_raw

#     if error_type == "date_from_datetime_parsing":
#         print(f"'{field}' must be a valid date. Got {input_processed}")
#     else:
#         print("Unknown Error:", msg)


def error_processing(error_details: list[ErrorDetails]) -> None:

    print()
    print()
    print("\n".join(map(str, error_details)))
    print("ALL:", error_details, sep="\n")
    print()
    print()

    for error in error_details:

        print()
        print("current:", error)
        print()

        error_type = error["type"]
        field = error["loc"][0]
        msg = error["msg"]
        input = error["input"]
        get_expected = error.get("ctx")
        print("get expected:", get_expected)
        expected = (list(get_expected.values())[0]
                    if get_expected else get_expected)

        print("unpacked:", error_type, field, msg, input, expected)
        print()

        if field in ["mode", "dataset_path", "save_directory",
                     "student_answer_path", "student_search_results_path",
                     "question"]:
            expected = cast(str, expected)
            str_error(error_type, field, msg,
                      input, expected)  # pyright: ignore
        elif field in ["max_chunk_size", "max_context_length"]:
            expected = cast(int, expected)
            int_error(error_type, field, msg,
                      input, expected)  # pyright: ignore
        elif field in ["k"]:
            expected = cast(float, expected)
            float_error(error_type, field, msg,
                        input, expected)  # pyright: ignore
        else:
            print("Unknown error:", error)
