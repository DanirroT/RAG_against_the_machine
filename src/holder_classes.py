from enum import Enum
from pydantic import BaseModel, Field, model_validator
from abc import ABC, abstractmethod
from pathlib import Path
# from enum import Enum
from typing import Any
from src import (Small_Tokenizer)


class InputHolder(BaseModel):

    mode: str = Field()
    max_chunk_size: int = Field(gt=0)
    dataset_path: str = Field(min_length=1)
    k: int = Field(gt=0)
    save_directory: str = Field(min_length=1)
    student_answer_path: str = Field(min_length=1)
    max_context_length: int = Field(gt=0)
    student_search_results_path: str = Field(min_length=1)
    question: str = Field()

    @model_validator(mode="after")
    def validate_inputs(self) -> "InputHolder":
        if self.mode == "index" and not self.max_chunk_size:
            raise ValueError(f"When calling the '{self.mode}' mode, option"
                             " max_chunk_size must be provided.")
        if self.mode == "search" and not self.k:
            raise ValueError(f"When calling the '{self.mode}' mode, option"
                             " k must be provided.")
        if (self.mode == "search_dataset" and
                (not self.save_directory or not self.dataset_path)):
            raise ValueError(f"When calling the '{self.mode}' mode, option"
                             " save_directory and dataset_path"
                             " must be provided.")
        if self.mode == "answer" and not self.k:
            raise ValueError(f"When calling the '{self.mode}' mode, option"
                             " k must be provided.")
        if (self.mode == "answer_dataset" and
                (not self.student_search_results_path
                 or not self.save_directory)):
            raise ValueError(f"When calling the '{self.mode}' mode, option"
                             " student_search_results_path and save_directory"
                             " must be provided.")
        if (self.mode == "evaluate" and
                (not self.student_search_results_path
                 or not self.dataset_path)):
            raise ValueError(f"When calling the '{self.mode}' mode, option"
                             " student_search_results_path and dataset_path"
                             " must be provided.")

        try:
            with open(self.dataset_path):
                pass
        except FileNotFoundError:
            raise ValueError("File set as dataset_path does not exist:"
                             f" {self.dataset_path}")

        return (self)

    def __str__(self) -> str:
        return super().__str__()


class FileHolder(ABC):

    path: Path

    @abstractmethod
    def __init__(self, path: Path) -> None:
        self.path = path

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        return {}


class SectionHolder(ABC):

    name: str
    start_line: int
    end_line: int

    @abstractmethod
    def __init__(self, name: str, start_line: int, end_line: int) -> None:
        self.name = name
        self.start_line = start_line
        self.end_line = end_line

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        return {}

    @abstractmethod
    def extract(self) -> str:
        return ""


class FunctHolder(SectionHolder):

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
        super().__init__(name, start_line, end_line)
        self.args = args
        self.returns = returns
        self.docstring = docstring
        self.body = body

    def to_dict(self) -> dict[str, Any]:
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

    def extract(self) -> str:
        return (
            f"funct_name: {self.name}\n"
            f"\"args\":\t({' '.join(self.args)})\t"
            f"\"returns\":\t{self.returns}\n" +
            ((f"\"docstring\":\t{self.docstring}\n")
             if self.docstring else "") +
            f"start={self.start_line}, end={self.end_line}\n"
            f"\"body\":\n{self.body}\n"
            f"{self.name}"
        )


class ClassHolder(SectionHolder):

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
        super().__init__(name, start_line, end_line)
        self.docstring = docstring
        self.inherits = inherits
        self.var_annotations = (var_annotations
                                if var_annotations is not None else [])
        self.methods = methods if methods is not None else []

    def to_dict(self) -> dict[str, Any]:
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

    def extract(self) -> str:
        return (
            f"class_name: {self.name}\n" +
            ((f"\"inherits\":\t{self.inherits}") if self.inherits else "") +
            f"\n\"vars\":\n{', '.join(self.var_annotations)}" +
            ((f"\"docstring\":\t{self.docstring}\n")
             if self.docstring else "") +
            f"\n\n\"methods\":\n{'\n\n'.join(map(str, self.methods))}\n"
            f"start={self.start_line}, end={self.end_line}\n"
            f"{self.name}"
        )


class PyHolder(FileHolder):
    imports: list[str]
    imports_start: int
    imports_end: int
    functs: list[FunctHolder]
    classes: list[ClassHolder]
    start_line: int
    end_line: int

    def __init__(self, path: Path,
                 start_line: int | None = None,
                 end_line: int | None = None,
                 imports: list[str] | None = None,
                 imports_start: int | None = None,
                 imports_end: int | None = None,
                 functs: list[FunctHolder] | None = None,
                 classes: list[ClassHolder] | None = None) -> None:
        super().__init__(path)
        self.start_line = start_line if start_line is not None else -1
        self.end_line = end_line if end_line is not None else -1
        self.imports = imports if imports is not None else []
        self.imports_start = imports_start if imports_start is not None else -1
        self.imports_end = imports_end if imports_end is not None else -1
        self.functs = functs if functs is not None else []
        self.classes = classes if classes is not None else []

    def to_dict(self) -> dict[str, Any]:
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


class MDSections(SectionHolder):
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
        super().__init__(name, start_line, end_line)
        self.tag = tag
        self.level = level
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

    def extract(self) -> str:
        return (
            f"section_name: {self.name}\n" +
            f"tag:\t{self.tag}\t"
            f"lvl:\t{self.level}"
            f"\n\n\"children\":\n{'\n\n'.join(map(str, self.children))}\n"
            f"start={self.start_line}, end={self.end_line}\n"
            f"{self.name}"
        )


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
            "path": str(self.path),
            "sections": self.sections
        })


class DefFunctException(Exception):

    e_len: int

    def __init__(self, e_len: int, *args: object) -> None:
        super().__init__(*args)
        self.e_len = e_len


class ChunkType(Enum):
    IMPORT = "python_imports"
    FUNCTION = "python_function"
    CLASS = "python_class_header"
    METHOD = "python_method"

    INTRODUCTION = "markdown_introduction"
    SECTION = "markdown_section"

    OTHER = "other_section"

    def __str__(self) -> str:
        return self.value


class ChunkRaw(BaseModel):
    id: str = Field(min_length=1)
    path: Path
    type: ChunkType
    parent: str | None = Field(default=None)
    start_line: int = Field(ge=-1)
    end_line: int = Field(ge=-1)
    content: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_inputs(self) -> "ChunkRaw":

        if self.type == ChunkType.METHOD and not self.parent:
            raise ValueError("A method chunk must have a parent class.")

        return (self)

    def __str__(self) -> str:

        return (
            f"\"id\": {self.id},\n"
            f"\"path\": {str(self.path)},\n"
            f"\"type\": {str(self.type)},\n"
            f"\"parent\": {self.parent},\n"
            f"\"start_line\": {self.start_line}, - "
            f"\"end_line\": {self.end_line},\n"
            f"\"content\":\n{self.content}"
        )

    def to_dict(self) -> dict[str, Any]:

        return {
            "id": self.id,
            "path": str(self.path),
            "type": str(self.type),
            "parent": self.parent,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "content": self.content,
        }

    def to_vector(self, llm: Small_Tokenizer, mode: str = "c"
                  ) -> list[int]:
        if mode == "h":
            return llm.encode(f"id: {self.id}\n"
                              f"path: {self.path}\nparent: {self.parent}\n"
                              f"start_line: {self.start_line} "
                              f"end_line: {self.end_line}\n"
                              "content:\n")
        if mode == "a":
            return llm.encode(f"id: {self.id}\n"
                              f"path: {self.path}\nparent: {self.parent}\n"
                              f"start_line: {self.start_line} "
                              f"end_line: {self.end_line}\n"
                              f"content:\n{self.content}")
        if mode == "c":
            return llm.encode(self.content)
        else:
            raise ValueError(f"'{mode}' is not a valid mode of "
                             "'ChunkRaw.to_vector()'. Must be one of: "
                             "'C' 'h' 'a'")


class Chunk(BaseModel):
    id: str = Field(min_length=1)
    path: str = Field(min_length=1)
    type: str
    parent: str | None = Field(default=None)
    start_line: int = Field(ge=-1)
    end_line: int = Field(ge=-1)
    content: str = Field(min_length=1)
    content_vector: list[int] = Field(min_length=1)

    # @model_validator(mode="after")
    # def validate_inputs(self) -> "Chunk":

    #     if self.type == ChunkType.METHOD and not self.parent:
    #         raise ValueError("A method chunk must have a parent class.")

    #     return (self)

    def to_dict(self) -> dict[str, Any]:

        return {
            "id": self.id,
            "path": str(self.path),
            "type": str(self.type),
            "parent": self.parent,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "content": self.content,
            "vector": self.content_vector
        }

    def __str__(self) -> str:

        return (
            f"\"id\": {self.id},\n"
            f"\"path\": {str(self.path)},\n"
            f"\"type\": {str(self.type)},\n"
            f"\"parent\": {self.parent},\n"
            f"\"start_line\": {self.start_line}, "
            f"\"end_line\": {self.end_line},\n"
            f"\"content\":\n{self.content}"
        )

        # "vector": self.content_vector


class ChunkScorePair(BaseModel):
    id: str = Field(min_length=1)
    chunk: Chunk
    score: float = Field(ge=0)

    def __str__(self) -> str:

        return (
            f"\"id\": {self.id},\n"
            f"\"path\": {str(self.chunk.path)},\n"
            f"\"type\": {str(self.chunk.type)},\n"
            f"\"parent\": {self.chunk.parent},\n"
            f"\"start_line\": {self.chunk.start_line}, "
            f"\"end_line\": {self.chunk.end_line},\n"
            f"\"content\":\n{self.chunk.content}" +
            (f"score: {self.score}" if self.score else "")
        )
