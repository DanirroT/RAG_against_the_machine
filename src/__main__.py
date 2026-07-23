import sys
from src import (val_args, FunctCallLLM, error_processing)
from pydantic import ValidationError


def main(args: list[str]) -> None:

    try:
        arg_inputs = val_args(args)
    except ValidationError as e:
        error_processing(e.errors())
        return
    except ValueError as e:
        print(f"Arguments passed incorrectly: {e}")
        return

    try:
        funct_caller = FunctCallLLM(arg_inputs)
    except FileExistsError:
        return
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        return
    except ValueError as e:
        print(e)
        return
    except ModuleNotFoundError as e:
        print("Module Dependencies were not met:\n"
              f"{e}")
        return
    except TypeError as e:
        print("An error has occurred while building"
              f" 'FunctCallLLM':\n{e}")
        return
    except Exception as e:
        print("An error has occurred while building"
              f" 'FunctCallLLM':\n{e}")
        return
    try:
        funct_caller.run_model()
    except Exception as e:
        print(f"Error while running model: {e}")
        return

    try:
        funct_caller.export_to_file()
    except FileNotFoundError as e:
        print(f"Error while exporting to file: {e}")
        return


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print("\rThe program has been forcefully stopped")
