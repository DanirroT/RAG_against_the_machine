from pydantic import BaseModel, Field, model_validator  # , field_validator
from abc import ABC, abstractmethod
from pathlib import Path
# from enum import Enum
from typing import Any


class InputHolder(BaseModel):

    mode: str = Field()
    max_chunk_size: int = Field(gt=0)
    dataset_path: str = Field(min_length=1)
    k: float = Field(gt=0)
    save_directory: str = Field(min_length=1)
    student_answer_path: str = Field(min_length=1)
    max_context_length: int = Field(gt=0)
    student_search_results_path: str = Field(min_length=1)
    question: str = Field()

    @model_validator(mode="after")
    def validate_inputs(self) -> "InputHolder":
        if self.mode == "answer" and not self.question:
            raise ValueError(f"When calling the '{self.mode}' mode, a question"
                             " must be provided as the second argument.")

        try:
            with open(self.dataset_path):
                pass
        except FileNotFoundError:
            raise ValueError("File set as dataset_path does not exist:"
                             f" {self.dataset_path}")

        return (self)


class FileHolder(ABC):

    path: Path

    @abstractmethod
    def __init__(self, path: Path) -> None:
        self.path = path

    @abstractmethod
    def to_dict(self) -> dict:
        return {}


class FunctHolder():

    name: str
    start_line: int
    end_line: int
    args: list[str]
    returns: str
    docstring: str | None
    body: str

    def __init__(self, name: str,
                 start_line: int,
                 end_line: int,
                 args: list[str],
                 returns: str,
                 body: str,
                 docstring: str | None = None) -> None:
        self.name = name
        self.start_line = start_line
        self.end_line = end_line
        self.args = args
        self.returns = returns
        self.docstring = docstring
        self.body = body

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "args": self.args,
            "returns": self.returns,
            "docstring": self.docstring,
            "body": self.body,
        }

    def __str__(self) -> str:
        return (
            f"\"name\": {self.name}\t"
            f"\"args\":\t({' '.join(self.args)})\n" +
            ((f"\"docstring\":\t{self.docstring}\n")
             if self.docstring else "") +
            f"start in {self.start_line}, end at {self.end_line}\n"
            f"\"returns\":\t{self.returns}\n"
            f"\"body\":\n{self.body}\n"
        )


class ClassHolder():

    name: str
    start_line: int
    end_line: int
    inherits: list[str]
    docstring: str
    var_annotations: list[str]
    methods: list[FunctHolder]

    def __init__(self, name: str,
                 start_line: int,
                 end_line: int,
                 docstring: str,
                 inherits: list[str],
                 var_annotations: list[str] | None = None,
                 methods: list[FunctHolder] | None = None) -> None:
        self.name = name
        self.start_line = start_line
        self.end_line = end_line
        self.docstring = docstring
        self.inherits = inherits
        self.var_annotations = (var_annotations
                                if var_annotations is not None else [])
        self.methods = methods if methods is not None else []

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "inherits": self.inherits,
            "docstring": self.docstring,
            "variable_annotations": self.var_annotations,
            "methods": [method.to_dict() for method in self.methods],
        }

    def __str__(self) -> str:
        return (
            f"\"name\": {self.name}" +
            ((f"\t\"inherits\":\t{self.inherits}") if self.inherits else "") +
            ((f"\n\"docstring\":\t{self.docstring}")
             if self.docstring else "") +
            f"\tstart in {self.start_line}, end at {self.end_line}"
            f"\n\"vars\":\n{', '.join(self.var_annotations)}"
            f"\n\n\"methods\":\n{'\n\n'.join(map(str, self.methods))}\n"
        )


class PyHolder(FileHolder):
    imports: list[str]
    functs: list[FunctHolder]
    classes: list[ClassHolder]

    def __init__(self, path: Path,
                 imports: list[str] | None = None,
                 functs: list[FunctHolder] | None = None,
                 classes: list[ClassHolder] | None = None) -> None:
        super().__init__(path)
        self.imports = imports if imports is not None else []
        self.functs = functs if functs is not None else []
        self.classes = classes if classes is not None else []

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "imports": self.imports,
            "functs": [funct.to_dict() for funct in self.functs],
            "classes": [class_.to_dict() for class_ in self.classes],
        }

    def __str__(self) -> str:
        return (
            f"\"path\": {self.path}\n"
            f"\"imports\":\t{'\n\t\t'.join(self.imports)}\n"
            f"\"functs\":\n{'\n\n'.join(map(str, self.functs))}\n\n"
            f"\"classes\":\n{'\n\n\n'.join(map(str, self.classes))}\n"
        )


class MDSections:
    name: str
    start_line: int
    end_line: int
    tag: str
    level: int
    content: str
    children: list["MDSections"]

    def __init__(self, tag: str,
                 level: int,
                 name: str,
                 start_line: int,
                 end_line: int,
                 content: str | None = None,
                 children: list["MDSections"] | None = None) -> None:
        self.tag = tag
        self.level = level
        self.name = name
        self.start_line = start_line
        self.end_line = end_line
        self.content = content if content is not None else ""
        self.children = children if children is not None else []

    def __str__(self) -> str:
        return (
            f"\"tag\":\t{self.tag}\t"
            f"\"lvl\":\t{self.level}\t"
            f"\"name\": {self.name}\t"
            f"start {self.start_line}\t"
            f"end {self.end_line}\n"
            f"{'\t\t' * self.level}\"content\": {self.content}\n" +
            (("\t\t\"children\":\t"
              f"{('\t\t\t\t').join(map(str, self.children))}\n")
             if len(self.children) else "")
        )

    def to_dict(self) -> dict[str, Any]:
        return ({
            "tag": self.tag,
            "level": self.level,
            "content": self.content,
            "children": self.children,
        })


class MDHolder(FileHolder):
    introduction: MDSections | None
    sections: list[MDSections]

    def __init__(self, path: Path,
                 introduction: MDSections | None = None,
                 sections: list[MDSections] | None = None) -> None:
        super().__init__(path)
        self.introduction = introduction
        self.sections = sections if sections is not None else []

    def to_dict(self) -> dict[str, Any]:

        return {
            "path": str(self.path),
            "introduction": (self.introduction.to_dict()
                             if self.introduction else None),
            "sections": [section.to_dict() for section in self.sections],
        }

    def __str__(self) -> str:
        return (
            f"\"path\": {self.path}\n"
            f"\"introduction\": {self.introduction}\n"
            f"\"sections\":\t{'\t\t'.join(map(str, self.sections))}\n"
        )


class OtherHolder(FileHolder):
    sections: list[str]

    def __init__(self, path: Path,
                 sections: list[str] | None = None) -> None:
        super().__init__(path)
        self.sections = sections if sections is not None else []

    def __str__(self) -> str:
        return (
            f"\"path\": {self.path}\n"
            f"\"sections\":\t{'\n\t\t'.join(self.sections)}\n"
        )

    def to_dict(self) -> dict[str, Any]:
        return ({
            "path": self.path,
            "sections": self.sections
        })


class DefFunctException(Exception):

    e_len: int

    def __init__(self, e_len: int, *args: object) -> None:
        super().__init__(*args)
        self.e_len = e_len


"""
class Parameter(BaseModel):
    p_name: str = Field(min_length=1)
    p_type: str = Field(min_length=1)

    # p_name: str
    # p_type: str

    # def __str__(self) -> str:
    #     return (
    #         f"{self.p_name} t: {self.p_type}"
    #     )

    # def __str__(self) -> str:
    #     return (
    #         f"\n\t\t\t\"{self.p_name}\": " "{"
    #         f"\n\t\t\t\t\"type\": \"{self.p_type}\"" "\n\t\t\t}"
    #     )

    def __str__(self) -> str:
        return (
            f"\"{self.p_name}\":" "{"
            f"\"type\":\"{self.p_type}\"" "}"
        )


# class Returns(BaseModel):
#     # pass
#     p_type: str = Field(min_length=1)


class FunctDef(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(default="")
    parameters: list[Parameter] = Field()
    returns: str = Field(min_length=1)

    # name: str
    # description: str
    # parameters: list[Parameter]
    # returns: str

    # def __str__(self) -> str:
    #     return (
    #         f"Name: {self.name}\n"
    #         f"Description: {self.description}\n"
    #         f"Params: {''.join(map(str, self.parameters))}\n"
    #         f"Return: {self.returns}"
    #     )

    # def __str__(self) -> str:
    #     return (
    #         "\t{\n"
    #         f"\t\t\"name\": \"{self.name}\",\n"
    #         f"\t\t\"description\": \"{self.description}\",\n"
    #         "\t\t\"parameters\": {"
    #         f"{','.join(map(str, self.parameters))}\n"
    #         "\t\t},\n"
    #         "\t\t\"return\": {"
    #         f"\n\t\t\t\"type\": \"{self.returns}\""
    #         "\n\t}\n"
    #     )

    # def __str__(self) -> str:
    #     return (
    #         "{"
    #         f"\"name\":\"{self.name}\","
    #         f"\"description\":\"{self.description}\","
    #         "\"parameters\":{"
    #         f"{','.join(map(str, self.parameters))}"
    #         "},"
    #         "\"return\":{"
    #         f"\"type\":\"{self.returns}\""
    #         "}}\n"
    #     )

    def __str__(self) -> str:
        return (
            f"\"name\":\"{self.name}\","
            f"\"description\":\"{self.description}\","
            "\"parameters\":"
            f"{','.join(map(str, self.parameters))}"
            f",\"return type\":\"{self.returns}\"\n"
        )


# print(FunctDef(name="n", description="desc",
#                parameters=[Parameter(p_name="a", p_type="number")],
#                returns="number"))
"""
