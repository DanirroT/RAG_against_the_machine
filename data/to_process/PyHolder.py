from pathlib import Path
from .input import FileHolder, FunctHolder, ClassHolder


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
