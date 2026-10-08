from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, cast
import json
import ast
from markdown_it import MarkdownIt
from src import (InputHolder, FileHolder, PyHolder, MDHolder, MDSections,
                 OtherHolder, FunctHolder, ClassHolder, Chunk, ChunkRaw,
                 ChunkType)
from tqdm import tqdm

if TYPE_CHECKING:
    from .tokenizer_sdk import Small_Tokenizer


class Ingestor():

    _tokenizer: Small_Tokenizer
    arg_inputs: InputHolder

    llm_files: dict[str, Path]

    vocab_text_int: dict[str, int]
    vocab_int_text: dict[int, str]

    ingest_out: list[FileHolder]

    def __init__(self, input_dir_path: Path, output_dir_path: Path,
                 arg_inputs: InputHolder) -> None:

        self.arg_inputs = arg_inputs
        self.input_dir_path = input_dir_path
        self.output_dir_path = output_dir_path

        self._load_all_files(self.input_dir_path)

        # print("current output\n\n")

        # print("\n".join(map(str, self.ingest_out)))

        # def process(self) -> None:

        self._load_llm()

        self.ingest_out_flattened = self.flatten_file_holders()

        # print("flattened output:")

        # for output in self.ingest_out_flattened:
        #     print("\n\n", output)

        # def print(self) -> None:

        last_path: Path | None = None

        for obj in self.ingest_out_flattened:
            current_path = (self.output_dir_path /
                            Path(obj.path).relative_to(
                                self.input_dir_path)).with_suffix(
                                    Path(obj.path).suffix + ".json")

            # print("path:\t", current_path,
            #       "\npath:\t", str(last_path), "\n\n")

            if not last_path or str(current_path) != str(last_path):
                # print("\t New", str(current_path), str(last_path),
                #       str(current_path) != str(last_path))
                current_path.parent.mkdir(parents=True, exist_ok=True)
                if last_path:
                    with last_path.open("a") as file:  # pyright: ignore
                        file.write("\n]\n")
                with current_path.open("x") as file:
                    file.write("[\n")
            else:
                # print("\t Same")
                with current_path.open("a") as file:
                    file.write(",\n")
            with current_path.open("a") as file:
                json.dump(obj.to_dict(), file, indent=4,
                          ensure_ascii=False)
            last_path = current_path

        if last_path:
            with last_path.open("a") as file:
                file.write("\n]")
        # print("files created")

    def _load_all_files(self, input_dir_path: Path) -> None:

        self.ingest_out = []

        files: list[Path] | tqdm[Path] = list(input_dir_path.rglob("*"))

        if len(files) > 50:
            files = tqdm(files)

        print("\nLoading Files from:", input_dir_path)
        for path in files:
            # print()
            # print(path)
            if path.is_dir() or any(part.startswith(".")
                                    for part in path.parts):
                continue
            out_file: FileHolder
            if path.is_file():
                with path.open("r", encoding="utf-8") as file:
                    file_str = file.read()
                if str(path).endswith(".py"):
                    out_file = self.parse_py(path, file_str)
                elif str(path).endswith(".md"):
                    out_file = self.parse_md(path, file_str)
                else:
                    out_file = OtherHolder(path)
                    file_sections = file_str.split("\n\n")

                    out_file.sections = ([
                        line + "\n\n"
                        for line in file_sections[:-1]] +
                        [file_sections[-1]])

            else:
                continue

            self.ingest_out.append(out_file)
        print()

    def parse_py(self, path: Path, file_str: str) -> PyHolder:

        out_file = PyHolder(path)
        parsed = ast.parse(file_str)
        # print(ast.dump(parsed, indent=4), end="\n\n\n")
        for item in parsed.body:
            # print(item)

            if (isinstance(item, ast.Import)):
                for file_import in item.names:
                    out_file.imports.append(
                        file_import.name +
                        ((" as " + file_import.asname)
                            if file_import.asname else ""))
                if out_file.imports_start == -1:
                    out_file.imports_start = item.lineno
                out_file.imports_end = (item.end_lineno if item.end_lineno
                                        else item.lineno)

            if (isinstance(item, ast.ImportFrom)):

                for file_import in item.names:
                    out_file.imports.append(
                        ((item.module + ".") if item.module else "")
                        + file_import.name +
                        ((" as " + file_import.asname)
                         if file_import.asname else ""))
                if out_file.imports_start == -1:
                    out_file.imports_start = item.lineno
                out_file.imports_end = (item.end_lineno if item.end_lineno
                                        else item.lineno)

            if isinstance(item, ast.FunctionDef):
                # print(item.name, item.args.defaults[0].__dict__
                #       if item.args.defaults else "")
                # print(list(zip(item.args.args,
                #       item.args.defaults)))
                args = item.args.args
                defaults: list[ast.expr | None] = (
                    [None] * (len(args) - len(item.args.defaults))
                    + item.args.defaults
                )

                item.returns = cast(ast.expr, item.returns)

                funct = FunctHolder(
                    path, item.name, item.lineno,
                    item.end_lineno
                    if item.end_lineno
                    else item.lineno,
                    [
                        arg.arg + (
                            " = " + ast.unparse(default)
                            if default is not None
                            else ""
                        )
                        for arg, default
                        in zip(args, defaults)
                    ], str(ast.unparse(item.returns)),
                    str(ast.get_source_segment(file_str, item)),
                    str(ast.get_docstring(item))
                )

                out_file.functs.append(funct)

            if isinstance(item, ast.ClassDef):
                class_object = ClassHolder(
                    path, item.name, item.lineno, item.end_lineno
                    if item.end_lineno else item.lineno,
                    str(ast.get_docstring(item)),
                    list(map(ast.unparse, item.bases)))
                for class_item in item.body:
                    if isinstance(class_item, ast.FunctionDef):
                        # print(class_item.name, type(
                        #   class_object.methods))
                        # print(len(class_item.args.args),
                        #       len(class_item.args.defaults))
                        # group = list(zip(class_item.args.args,
                        #                  class_item.args.defaults))
                        # for arg, const in group:
                        #     print(arg.arg, const.value)
                        # print(list(zip(class_item.args.args,
                        #            class_item.args.defaults)))
                        args = class_item.args.args
                        defaults = (
                            [None] * (len(args) -
                                      len(class_item.args.defaults))
                            + class_item.args.defaults
                        )

                        class_item.returns = cast(ast.expr, class_item.returns)

                        class_object.methods.append(
                            FunctHolder(
                                path, class_item.name, class_item.lineno,
                                class_item.end_lineno
                                if class_item.end_lineno
                                else class_item.lineno,
                                [
                                    arg.arg + (
                                        " = " + ast.unparse(default)
                                        if default is not None
                                        else ""
                                    )
                                    for arg, default
                                    in zip(args, defaults)
                                ],
                                str(ast.unparse(class_item.returns)),
                                str(ast.get_source_segment(file_str,
                                                           class_item)),
                                str(ast.get_docstring(class_item))
                            )
                        )
                    if isinstance(class_item, ast.AnnAssign):
                        class_object.var_annotations.append(
                            ast.unparse(class_item.target) + ": " +
                            ast.unparse(class_item.annotation) +
                            ((" = " + ast.unparse(
                                class_item.value))
                                if class_item.value else "")
                        )
                out_file.classes.append(class_object)

        return out_file

    def parse_md(self, path: Path, file_str: str) -> MDHolder:

        md_parse = MarkdownIt()

        out_file = MDHolder(path)
        md_parsed = md_parse.parse(file_str)

        waiting_heading: bool = False
        stack: list[MDSections] = []
        tag: str = "0"

        # print()
        for token in md_parsed:
            # print(token)
            # print()
            # print()
            if token.type == "heading_open":
                waiting_heading = True
                tag = token.tag
                continue
            if token.type in ["paragraph_close",
                              "paragraph_open",
                              "heading_close"]:
                continue

            token.map = cast(list[int], token.map)

            if waiting_heading:
                if len(token.map) == 2:
                    section = MDSections(
                        path, token.content,
                        token.map[0]+1, token.map[1]+1,
                        tag, int(tag[1])
                    )
                elif len(token.map) == 1:
                    section = MDSections(
                        path, token.content,
                        token.map[0]+1, token.map[0]+1,
                        tag, int(tag[0])
                    )
                else:
                    section = MDSections(
                        path, token.content,
                        -1, -1, tag, int(tag)
                    )
                while stack and stack[-1].level >= section.level:
                    stack.pop()
                if stack:
                    stack[-1].children.append(section)
                else:
                    out_file.sections.append(section)

                stack.append(section)

                waiting_heading = False
                continue

            if stack:
                stack[-1].content += token.content + "\n"
                if token.map:
                    stack[-1].end_line = (token.map[1] + 1
                                          if len(token.map) == 2
                                          else token.map[0] + 1)

            else:
                # Text before the first heading
                if len(token.map) == 2:
                    section = MDSections(
                        path, "introduction",
                        token.map[0]+1, token.map[1]+1,
                        tag, int(tag), token.content,
                    )
                elif len(token.map) == 1:
                    section = MDSections(
                        path, "introduction",
                        token.map[0]+1, token.map[0]+1,
                        tag, int(tag), token.content,
                    )
                else:
                    section = MDSections(path, "introduction",
                                         -1, -1, tag, int(tag), token.content)
                out_file.introduction = section

            # input(out_file)
            # print()
            # print()

        # file_sections = file_str.split("\n#")

        # out_file["Introduction"] = repr(file_sections[0]
        #                                       + "\n")
        # out_file["Sections"] = ([
        #     ("#" + line + "\n")
        #     for line in file_sections[1:-1]] +
        #     ["#" + file_sections[-1]])

        return out_file

    def flatten_file_holders(self) -> list[Chunk]:

        file_holders = self.ingest_out.copy()

        flattened_chunks: list[ChunkRaw] = []

        last_path: Path = Path("")
        line_char_dict: dict[int, int] = {}

        holders: list[FileHolder] | tqdm[FileHolder] = list(file_holders)

        if len(holders) > 100:
            holders = tqdm(holders)

        print("\nFlattening Files...")
        for file_holder in holders:

            if file_holder.path != last_path:
                line_char_dict = self.get_line_char_dict(file_holder.path)
                last_path = file_holder.path

                # print(file_holder.path)
                # print(line_char_dict)
                # print()

            if isinstance(file_holder, PyHolder):

                # print(file_holder)

                flattened_chunks += self.flatten_py(file_holder,
                                                    line_char_dict)

            elif isinstance(file_holder, MDHolder):

                # print()
                # print(line_char_dict)
                # print()

                # input(file_holder)

                if file_holder.introduction:
                    flattened_chunks.append(
                        ChunkRaw(
                            id=f"{file_holder.path.stem}.introduction",
                            path=file_holder.path,
                            type=ChunkType.INTRODUCTION,
                            parent=None,
                            start_char=line_char_dict[
                                file_holder.introduction.start_line],
                            end_char=line_char_dict[
                                file_holder.introduction.end_line + 1] - 1,
                            content=file_holder.introduction.content
                        )
                    )

                flattened_chunks += self.flatten_md(file_holder.sections,
                                                    line_char_dict)

            else:
                file_holder = cast(OtherHolder, file_holder)
                counter = 0
                start_char = 0
                for section in file_holder.sections:
                    end_char = (start_char + len(section) - 1)
                    flattened_chunks.append(
                        ChunkRaw(
                            id=(f"other.{file_holder.path.stem}."
                                f"section.{counter}"),
                            path=file_holder.path,
                            parent=None,
                            type=ChunkType.OTHER,
                            start_char=start_char,
                            end_char=end_char,
                            content=section
                        )
                    )
                    start_char = end_char + 1
                    counter += 1
        print()
        return self.split_chunks(flattened_chunks)

    def flatten_py(self, py_holder: PyHolder,
                   line_char_dict: dict[int, int]
                   ) -> list[ChunkRaw]:

        flattened_chunks: list[ChunkRaw] = []

        if py_holder.imports:
            flattened_chunks.append(
                ChunkRaw(
                    id=f"{py_holder.path.stem}.imports",
                    path=py_holder.path,
                    type=ChunkType.IMPORT,
                    parent=None,
                    start_char=line_char_dict[py_holder.imports_start],
                    end_char=line_char_dict[py_holder.imports_end + 1] - 1,
                    content="\n".join([imp for imp in py_holder.imports])
                )
            )

        for funct in py_holder.functs:
            flattened_chunks.append(
                ChunkRaw(
                    id=f"{py_holder.path.stem}.function.{funct.name}",
                    path=py_holder.path,
                    type=ChunkType.FUNCTION,
                    parent=None,
                    start_char=line_char_dict[funct.start_line],
                    end_char=line_char_dict[funct.end_line + 1] - 1,
                    content=funct.body
                )
            )
        for cls in py_holder.classes:
            # print()
            # print()
            # print(cls)
            # print()
            # print("var_annotations", cls.var_annotations)
            # print()
            # print()
            # print("docstring:", cls.docstring if cls.docstring else "")
            # print()
            # print("var_annotations join:", "\n".join(cls.var_annotations))
            # print()
            # print()
            # print(("docstring: " + cls.docstring + "\n" +
            #       ("\n".join(cls.var_annotations))))

            flattened_chunks.append(
                ChunkRaw(
                    id=f"{py_holder.path.stem}.class.{cls.name}",
                    path=py_holder.path,
                    type=ChunkType.CLASS,
                    parent=str(cls.inherits)[1:-1],
                    start_char=line_char_dict[cls.start_line],
                    end_char=line_char_dict[cls.end_line + 1] - 1,
                    content=(("docstring: " + cls.docstring + "\n" +
                              ("\n".join(cls.var_annotations))))
                )
            )

            # print()
            # print()
            # print(flattened_chunks[-1])
            # print()
            # print()
            # print()
            # print()

            flattened_chunks += [
                ChunkRaw(
                    id=(f"{py_holder.path.stem}.class.{cls.name}"
                        f".method.{method.name}"),
                    path=py_holder.path,
                    type=ChunkType.METHOD,
                    parent=cls.name,
                    start_char=line_char_dict[method.start_line],
                    end_char=line_char_dict[method.end_line + 1] - 1,
                    content=method.body
                )
                for method in cls.methods
            ]

        return flattened_chunks

    def flatten_md(self, md_holder: list[MDSections],
                   line_char_dict: dict[int, int]
                   ) -> list[ChunkRaw]:

        flattened_chunks: list[ChunkRaw] = []

        for section in md_holder:
            flattened_chunks.append(
                ChunkRaw(
                    id=f"{section.path.stem}.section.{section.name}",
                    path=section.path,
                    type=ChunkType.SECTION,
                    parent=None,
                    start_char=line_char_dict[section.start_line],
                    end_char=line_char_dict[section.end_line + 1] - 1,
                    content=section.content
                )
            )
            if section.children:
                flattened_chunks += self.flatten_md(section.children,
                                                    line_char_dict)

        return flattened_chunks

    def get_line_char_dict(self, file_path: Path) -> dict[int, int]:
        line_char_dict: dict[int, int] = {}
        char_count = 0
        with file_path.open("r", encoding="utf-8") as f:
            for line_number, line in enumerate(f):
                line_char_dict[line_number+1] = char_count
                char_count += len(line)

            line_char_dict[len(line_char_dict)+1] = char_count + 1
            line_char_dict[len(line_char_dict)+1] = char_count + 1
        return line_char_dict

    def split_chunks(self, chunks: list[ChunkRaw]) -> list[Chunk]:

        split_chunks: list[Chunk] = []

        # self.arg_inputs.max_context_length = 60
        overlap = 5

        # last_path = Path("")

        # print(f"max_context_length = {self.arg_inputs.max_context_length}")

        for chunk in chunks:
            chuck_header = chunk.to_vector(self._tokenizer, "h")
            # print("---", self._tokenizer.decode(chuck_header),
            #       "---", sep="\n")
            chunk_vector = chunk.to_vector(self._tokenizer, "c")
            # print()
            # print("---", self._tokenizer.decode(chunk_vector),
            #       "---", sep="\n")
            # input()
            chunk_header_len = len(chuck_header)
            vector_len = len(chunk_vector)
            whole_vector_len = chunk_header_len + vector_len
            i = 1
            if (whole_vector_len > self.arg_inputs.max_context_length):
                max_content_size = (self.arg_inputs.max_context_length
                                    - overlap - chunk_header_len)

                # if chunk.path != last_path:
                #     line_char_dict = self.get_line_char_dict(chunk.path)
                #     last_path = chunk.path

                # print(f"({chunk_header_len} + {vector_len}) - Splitting "
                #       f"into sub-chunks of size {max_content_size}")
                start = 0
                end = 0
                start_char = chunk.start_char
                end_char = chunk.end_char
                while end != vector_len:
                    end = min(start + max_content_size, vector_len)
                    split = chunk_vector[start:end]
                    split_decode = self._tokenizer.decode(split)
                    end_char = chunk.start_char + len(split_decode)
                    # print(f"sub-chunk {i}: ", start, "-", end, sep="")
                    i += 1
                    new_chunk = Chunk(
                        id=f"{chunk.id}.sub{i}",
                        path=str(chunk.path),
                        type=str(chunk.type),
                        parent=chunk.parent,
                        start_char=start_char,
                        end_char=end_char,
                        content=split_decode,
                        content_vector=(chuck_header + split)
                    )
                    split_chunks.append(new_chunk)
                    start = end - overlap
                    overlap_str = self._tokenizer.decode(
                        chunk_vector[start:end])
                    start_char = end_char - len(overlap_str)
                    start = end - overlap
            else:
                # print(f"(({chunk_header_len} + {vector_len})) - "
                #       f"Not Splitting")
                split_chunks.append(Chunk(
                    id=chunk.id,
                    path=str(chunk.path),
                    type=str(chunk.type),
                    parent=chunk.parent,
                    start_char=chunk.start_char,
                    end_char=chunk.end_char,
                    content=self._tokenizer.decode(chunk_vector),
                    content_vector=(chuck_header + chunk_vector)
                ))

            for sub_chunk in split_chunks[-i:]:
                # print("final len:", len(sub_chunk.content_vector))
                # print("final out:", self._tokenizer.decode(
                #     sub_chunk.content_vector), "\n", sep="\n")
                if (len(sub_chunk.content_vector) >
                        self.arg_inputs.max_context_length):
                    raise ValueError(f"Chunk {sub_chunk.id} is too long")

            # print("\n\n")

        return split_chunks
        """
        for chunk in chunks:
            nb_splits = 1
         -   input("\n\n")
            chuck_header = chunk.to_vector(self._tokenizer, "h")
            chunk_vector = self._tokenizer.encode(chunk.content)
            chunk_header_len = len(chuck_header)
            vector_len = len(chunk_vector)
            whole_vector_len = chunk_header_len + vector_len
            if (whole_vector_len > self.arg_inputs.max_context_length):
                safe_space = (self.arg_inputs.max_context_length
                              - 10 - chunk_header_len)
                nb_splits = ((vector_len // safe_space) + 1)
                split_size = (vector_len // nb_splits)
                print("last chunk size",
                      (vector_len % split_size) + overlap // 2
                      + split_size + chunk_header_len)
                if (((vector_len % split_size) + overlap // 2 + split_size)
                        > safe_space):
                    split_size = safe_space
                    nb_splits = (vector_len // split_size +
                                 (1 if vector_len % nb_splits else 0))
                    print("last chunk size re",
                          (vector_len % split_size) + overlap // 2
                          + split_size + chunk_header_len)

                print(f"({chunk_header_len} + {vector_len}) - Splitting "
                      f"into {nb_splits} sub-chunks of size {split_size}")
                for i in range(nb_splits):
                    start = ((i * split_size - overlap // 2) if i != 0 else 0)
                    end = (((i+1) * split_size + overlap // 2)
                           if i != nb_splits - 1 else vector_len)
                    print(f"sub-chunk {i+1}: ",
                          start, "-", end, sep="")
                    new_chunk = Chunk(
                        id=f"{chunk.id}.sub{i}",
                        path=str(chunk.path),
                        type=chunk.type,
                        parent=chunk.parent,
                        start_char=chunk.start_char,
                        end_char=chunk.end_char,
                        content_vector=(chuck_header +
                                        chunk_vector[start:end])
                    )
                    split_chunks.append(new_chunk)
        """

    def _load_llm(self) -> None:

        from .tokenizer_sdk import Small_Tokenizer
        self._tokenizer = Small_Tokenizer()

        self.llm_files = self._tokenizer.get_path_to_model_files()

        with self.llm_files["vocab"].open() as vocab_file:
            self.vocab_text_int: dict[str, int] = json.load(vocab_file)

        self.vocab_int_text = {}

        for k, v in self.vocab_text_int.items():
            self.vocab_int_text[v] = k
