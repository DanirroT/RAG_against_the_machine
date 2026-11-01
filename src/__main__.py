from src import (val_args, rag_code_base_llm, error_processing)
from pydantic_core import ValidationError


def main() -> None:

    try:
        arg_inputs = val_args()
    except ValidationError as e:
        error_processing(e.errors())
        return
    except ValueError as e:
        print(f"Arguments passed incorrectly: {e}")
        return
        # from src import (InputHolder)
        # arg_inputs = InputHolder(
        #     # mode="index",
        #     # mode="search",
        #     # mode="search_dataset",
        #     mode="answer",
        #     # mode="answer_dataset",
        #     # mode="evaluate",
        #     max_chunk_size=2000,
        #     dataset_path=("data/datasets/UnansweredQuestions/"
        #                   "dataset_docs_public.json"),
        #     k=10,
        #     save_directory="data/output/search_results",
        #     student_answer_path=("data/output/search_results/"
        #                          "dataset_docs_public.json"),
        #     max_context_length=2000,
        #     student_search_results_path=("data/output/search_results/"
        #                                  "dataset_docs_public.json"),
        #     question="what are the Imports for inputs?"
        #     # question=""
        # )
        # print(f"Using Preset:\n\n{arg_inputs}")

    try:
        rag_code_base_llm(arg_inputs, False)
        # RAGCodeBaseLLM(arg_inputs)

    except ValueError as e:
        print(f"Error while running RAGCodeBaseLLM: {e}")
        return
    except (IsADirectoryError, FileExistsError):
        return
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        return

    except ModuleNotFoundError as e:
        print("Module Dependencies were not met:\n"
              f"{e}")
        return
    except TypeError as e:
        print("An unexpected type-related error occurred while "
              f"running 'RAGCodeBaseLLM':\n{e}")
        return
    except Exception as e:
        print("An error has occurred while building"
              f" 'RAGCodeBaseLLM':\n{e}")
        return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\rThe program has been forcefully stopped")
