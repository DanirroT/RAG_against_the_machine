import sys
from src import (RAGCodeBaseLLM, InputHolder)
# from src import (val_args, RAGCodeBaseLLM, error_processing)
# from pydantic import ValidationError


def main(args: list[str]) -> None:

    mode = False

    # try:
    #     arg_inputs = val_args(args)
    # except ValidationError as e:
    #     error_processing(e.errors())
    #     return
    # except ValueError as e:
    #     print(f"Arguments passed incorrectly: {e}")
    #     return

    arg_inputs: InputHolder = InputHolder(
        mode="index",
        max_chunk_size=2000,
        dataset_path=("data/datasets/UnansweredQuestions/"
                      "dataset_docs_public.json"),
        k=10,
        save_directory="data/output/search_results",
        student_answer_path=("data/output/search_results/"
                             "dataset_docs_public.json"),
        max_context_length=2000,
        student_search_results_path=("data/output/search_results/"
                                     "dataset_docs_public.json"),
        question=""
    )

    try:
        RAGCodeBaseLLM(arg_inputs, mode)

    except (IsADirectoryError, FileExistsError):
        return
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        return
    # except ValueError as e:
    #     print(e)
    #     return
    # except ModuleNotFoundError as e:
    #     print("Module Dependencies were not met:\n"
    #           f"{e}")
    #     return
    # except TypeError as e:
    #     print("An error has occurred while building"
    #           f" 'RAGCodeBaseLLM':\n{e}")
    #     return
    # except Exception as e:
    #     print("An error has occurred while building"
    #           f" 'RAGCodeBaseLLM':\n{e}")
        # return

    # try:
    #     funct_caller.run_model()
    # except Exception as e:
    #     print(f"Error while running model: {e}")
    #     return

    # try:
    #     funct_caller.export_to_file()
    # except FileNotFoundError as e:
    #     print(f"Error while exporting to file: {e}")
    #     return


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print("\rThe program has been forcefully stopped")
