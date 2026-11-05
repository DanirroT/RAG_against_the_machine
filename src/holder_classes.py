from enum import Enum
import uuid
from pydantic import BaseModel, Field, model_validator
from abc import ABC, abstractmethod
from pathlib import Path
# from enum import Enum
from typing import Any
from src import (Small_LLM_ModelBaseProtocol)


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

        if ((self.mode == "search" or self.mode == "answer")
                and not self.question):
            raise ValueError(f"When calling the '{self.mode}' mode, a question"
                             " must be provided as the second argument.")

        if ((self.mode == "index" or self.mode == "search_dataset" or
             self.mode == "answer_dataset" or self.mode == "evaluate")
                and self.question):
            raise ValueError(f"The '{self.mode}' mode does not accept "
                             "a question as the second argument.")

        if (self.mode == "search_dataset" and
                (not self.save_directory or not self.dataset_path)):
            raise ValueError(f"When calling the '{self.mode}' mode, option"
                             " save_directory and dataset_path"
                             " must be provided.")

        if self.mode == "answer" and not self.k:
            raise ValueError(f"When calling the '{self.mode}' mode, option"
                             " k must be provided.")

        if self.mode == "answer" and not self.question:
            raise ValueError(f"When calling the '{self.mode}' mode, a question"
                             " must be provided as the second argument.")

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
        return (
            f"mode: {self.mode}\n"
            f"max_chunk_size: {self.max_chunk_size}\n"
            f"dataset_path: {self.dataset_path}\n"
            f"k: {self.k}\n"
            f"save_directory: {self.save_directory}\n"
            f"student_answer_path: {self.student_answer_path}\n"
            f"max_context_length: {self.max_context_length}\n"
            "student_search_results_path: "
            f"{self.student_search_results_path}\n"
            f"question: {self.question}\n"
        )


class FileHolder(ABC):

    path: Path

    @abstractmethod
    def __init__(self, path: Path) -> None:
        self.path = path

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        return {}


class SectionHolder(ABC):

    path: Path
    name: str
    start_line: int
    end_line: int

    @abstractmethod
    def __init__(self, path: Path, name: str,
                 start_line: int, end_line: int) -> None:
        self.path = path
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

    args: list[str]
    returns: str
    docstring: str | None
    body: str

    def __init__(self, path: Path,
                 name: str,
                 start_line: int,
                 end_line: int,
                 args: list[str],
                 returns: str,
                 body: str,
                 docstring: str | None = None) -> None:
        super().__init__(path, name, start_line, end_line)
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

    inherits: list[str]
    docstring: str | None
    var_annotations: list[str]
    methods: list[FunctHolder]

    def __init__(self, path: Path,
                 name: str,
                 start_line: int,
                 end_line: int,
                 inherits: list[str],
                 docstring: str | None = None,
                 var_annotations: list[str] | None = None,
                 methods: list[FunctHolder] | None = None) -> None:
        super().__init__(path, name, start_line, end_line)
        self.inherits = inherits
        self.docstring = docstring
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


class MiscHolder(SectionHolder):

    body: str

    def __init__(self, path: Path,
                 name: str | None = None,
                 start_line: int = -1,
                 end_line: int = -1,
                 body: str = "") -> None:
        if name is None:
            name = f"misc_{start_line}_{end_line}"
        super().__init__(path, name, start_line, end_line)
        self.body = body

    def append(self, name: str | None = None,
               end_line: int = -1,
               body: str = "") -> None:
        if name is not None:
            self.name = name
        if end_line != -1:
            self.end_line = end_line
        if body != "":
            self.body += "\n" + body

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "body": self.body,
        }

    def __str__(self) -> str:
        return (
            f"\"name\": {self.name}\t"
            f"start in {self.start_line}, end at {self.end_line}\n"
            f"\"body\":\n{self.body}\n"
        )

    def extract(self) -> str:
        return (
            f"funct_name: {self.name}\n"
            f"start={self.start_line}, end={self.end_line}\n"
            f"\"body\":\n{self.body}\n"
            f"{self.name}"
        )


class PyHolder(FileHolder):
    imports: list[str]
    imports_start: int
    imports_end: int
    functs: list[FunctHolder]
    classes: list[ClassHolder]

    def __init__(self, path: Path,
                 imports: list[str] | None = None,
                 imports_start: int | None = None,
                 imports_end: int | None = None,
                 functs: list[FunctHolder] | None = None,
                 classes: list[ClassHolder] | None = None,
                 misc: list[MiscHolder] | None = None) -> None:
        super().__init__(path)
        self.imports = imports if imports is not None else []
        self.imports_start = imports_start if imports_start is not None else -1
        self.imports_end = imports_end if imports_end is not None else -1
        self.functs = functs if functs is not None else []
        self.classes = classes if classes is not None else []
        self.misc = misc if misc is not None else []

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

    level: int
    content: str
    children: list["MDSections"]

    def __init__(self, path: Path,
                 name: str,
                 start_line: int,
                 end_line: int,
                 level: int,
                 content: str | None = None,
                 children: list["MDSections"] | None = None) -> None:
        super().__init__(path, name, start_line, end_line)
        self.level = level
        self.content = content if content is not None else ""
        self.children = children if children is not None else []

    def __str__(self) -> str:
        return (
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
            "level": self.level,
            "content": self.content,
            "children": self.children,
        })

    def extract(self) -> str:
        return (
            f"section_name: {self.name}\n" +
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
    start_char: int = Field(ge=-1)
    end_char: int = Field(ge=-1)
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
            f"\"start_char\": {self.start_char}, - "
            f"\"end_char\": {self.end_char},\n"
            f"\"content\":\n{self.content}"
        )

    def to_dict(self) -> dict[str, Any]:

        return {
            "id": self.id,
            "path": str(self.path),
            "type": str(self.type),
            "parent": self.parent,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "content": self.content,
        }

    def to_vector(self, llm: Small_LLM_ModelBaseProtocol, mode: str = "c"
                  ) -> list[int]:
        if mode == "h":
            return llm.encode(f"id: {self.id}\n"
                              f"path: {self.path}\nparent: {self.parent}\n"
                              f"start_char: {self.start_char} "
                              f"end_char: {self.end_char}\n"
                              "content:\n")
        if mode == "a":
            return llm.encode(f"id: {self.id}\n"
                              f"path: {self.path}\nparent: {self.parent}\n"
                              f"start_char: {self.start_char} "
                              f"end_char: {self.end_char}\n"
                              f"content:\n{self.content}")
        if mode == "c":
            return llm.encode(self.content)
        else:
            raise ValueError(f"'{mode}' is not a valid mode of "
                             "'ChunkRaw.to_vector()'. Must be one of: "
                             "'C' 'h' 'a'")


class MinimalSource(BaseModel):
    path: str = Field(min_length=1)
    start_char: int = Field(ge=-1)
    end_char: int = Field(ge=-1)

    def to_simple_dict(self) -> dict[str, str | int]:
        return {
            "file_path": str(self.path),
            "first_character_index": self.start_char,
            "last_character_index": self.end_char
        }


class Chunk(MinimalSource):  # Equivalent to MinimalSource
    id: str = Field(min_length=1)
    type: str
    parent: str | None = Field(default=None)
    content: str = Field(min_length=1)
    content_vector: list[int] = Field(min_length=1)

    def to_dict(self) -> dict[str, Any]:

        return {
            "id": self.id,
            "path": str(self.path),
            "type": str(self.type),
            "parent": self.parent,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "content": self.content,
            "vector": self.content_vector
        }

    def __str__(self) -> str:

        return (
            f"\"id\": {self.id},\n"
            f"\"path\": {str(self.path)},\n"
            f"\"type\": {str(self.type)},\n"
            f"\"parent\": {self.parent},\n"
            f"\"start_char\": {self.start_char}, "
            f"\"end_char\": {self.end_char},\n"
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
            f"\"start_char\": {self.chunk.start_char}, "
            f"\"end_char\": {self.chunk.end_char},\n"
            f"\"content\":\n{self.chunk.content}" +
            (f"score: {self.score}" if self.score else "")
        )

    def to_simple_dict(self) -> dict[str, str | int]:
        return self.chunk.to_simple_dict()


class UnansweredQuestion(BaseModel):
    question_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()))
    question: str = Field(min_length=1)


class AnsweredQuestion(UnansweredQuestion):
    sources: list[MinimalSource] = Field(default=[])
    answer: str = Field(min_length=1)


class RagDataset(BaseModel):
    rag_questions: list[AnsweredQuestion | UnansweredQuestion] = (
        Field(min_length=1))


class MinimalSearchResults(BaseModel):
    question_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()))
    question: str = Field(min_length=1)
    retrieved_sources: list[MinimalSource] = Field(default=[])

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "question": self.question,
            "retrieved_sources": [source.to_simple_dict()
                                  for source in self.retrieved_sources]
        }


class MinimalAnswer(MinimalSearchResults):
    answer: str = Field(min_length=1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "question": self.question,
            "retrieved_sources": [source.to_simple_dict()
                                  for source in self.retrieved_sources],
            "answer": self.answer
        }


class StudentSearchResults(BaseModel):
    search_results: list[MinimalSearchResults] = Field(default=[])
    k: int = Field(ge=0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "search_results": [result.to_dict()
                               for result in self.search_results],
            "k": self.k
        }


class StudentSearchResultsAndAnswer(BaseModel):
    search_results: list[MinimalAnswer] = Field(default=[])
    k: int = Field(ge=0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "search_results": [result.to_dict()
                               for result in self.search_results],
            "k": self.k
        }
