# import sys
# from typing import Any

from src import InputHolder


def val_args(args: list[str]) -> dict[str, str]:

    argc = len(args)

    if (args[1] in ['index',  # Index the repository
                    'search',  # Search for a single query
                    'search_dataset',  # Process multiple questions and output search results
                    'answer',  # Answer a single question with context
                    'answer_dataset',  # Generate answers from search results
                    'evaluate',  # Evaluate search results against ground truth
                    ]):
        mode = args[1]
    else:
        raise ValueError(f"Unknow First Argument: {args[1]}\n"
                         "Must be: 'ingest', 'search', 'answer' or 'evaluate'")

    inputs: dict[str, int | str] = {
        "mode": mode,
        "max_chunk_size": 2000,
        "dataset_path": "data/datasets/UnansweredQuestions/dataset_docs_public.json",
        "k": 10,
        "save_directory": "data/output/search_results",
        "student_answer_path": "data/output/search_results/dataset_docs_public.json",
        "max_context_length": 2000,
        "student_search_results_path": "data/output/search_results/dataset_docs_public.json",
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

    return InputHolder(**inputs)


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
