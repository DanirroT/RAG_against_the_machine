def val_args(args: list[str]) -> dict[str, str]:

    argc = len(args)

    arg_inputs: dict[str, str] = {
        "functions_definition": "data/input/functions_definition.json",
        "input": "data/input/function_calling_tests.json",
        "output": "data/output/function_calls.json"
    }
    fail: bool = False
    next_ins: None | str = None

    for arg in args:

        if next_ins:
            arg_inputs[next_ins] = arg
            next_ins = None
            continue

        if arg == "--functions_definition":
            next_ins = "functions_definition"
        elif arg == "--input":
            next_ins = "input"
        elif arg == "--output":
            next_ins = "output"

        elif arg.startswith("--"):
            print(f"Error: Unknown Parameter: {arg}")
            fail = True
        else:
            print("Error: Unknown Argument")
            fail = True

    for arg, file in arg_inputs.items():
        if not file.endswith(".json"):
            print(f"{arg} must be a json file. {file}")
            fail = True

    if fail:
        raise ValueError("\nProgram Stopped")

    return arg_inputs


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
