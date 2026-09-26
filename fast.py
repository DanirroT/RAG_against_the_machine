print(len("""_This project has been created as part of the 42 curriculum by dmota-ri._

# Description

CallMeMaybe is designed to teach students how to perform function calling with Small Language Models (LLMs) using Python.

The goal is to create an algorithm that uses the provided `Small_LLM_Model` class, a wrapper around the `Qwen/Qwen3-0.6B` Small Language Model, to generate structured Function Calling dictionaries from natural language prompts.
"""))


# print(len("Hello\n1\n\n"))
# print(len("2\n3\n"))
# print(len("src.InputHolder\njson\ntyping.Any\npathlib.Path\nshutil.rmtree"))

print(len("""from pathlib import Path
from .input import FileHolder, FunctHolder, ClassHolder

a = 1


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


print(a)
"""))


print(len(r"""from pathlib import Path
from .input import FileHolder, FunctHolder, ClassHolder

a = 1


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


print(a)"""))
