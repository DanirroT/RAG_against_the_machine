from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING
import json
import ast
from markdown_it import MarkdownIt
from src import (InputHolder, Chunk, ChunkRaw, ChunkType,
                 PyHolder, FunctHolder, ClassHolder, MiscHolder,
                 MDHolder, MDSections, OtherHolder, FileHolder)
from tqdm import tqdm

if TYPE_CHECKING:
    from .tokenizer_sdk import Small_Tokenizer


class Ingestor():

    _tokenizer: Small_Tokenizer
    arg_inputs: InputHolder

    llm_files: dict[str, Path]

    vocab_text_int: dict[str, int]
    vocab_int_text: dict[int, str]

    def __init__(self, input_dir_path: Path, output_dir_path: Path,
                 arg_inputs: InputHolder) -> None:

        self.arg_inputs = arg_inputs

        self._load_llm()

        print("\nLLm loaded\n")

        files: list[Path] | tqdm[Path] = list(input_dir_path.rglob("*"))

        print("\nLoading Files from:", input_dir_path)

        if len(files) > 500:
            files = tqdm(files)

        for path in files:
            # print()
            # print(path, end=" ", flush=True)
            if (path.is_dir() or any(
                part.startswith(".") for part in path.relative_to(
                    input_dir_path).parts if part != "..")):
                # if path.is_dir():
                # print("skip", flush=True)
                continue
            if path.is_file():
                if path.suffix.lower() in [
                    ".png", ".ico", ".jpg", ".jpeg", ".obj",
                    ".stl", ".mp4", ".mp3", ".wav", ".so",
                        ".gif", ".bmp", ".tiff", ".o", ".bin"]:
                    # print("skip", flush=True)
                    continue
                # if not (path.suffix.lower() in [
                #   ".py", ".md", ".txt", "", ".json"]):
                #     # print("skip", flush=True)
                #     continue

                output_path = (
                    output_dir_path / Path(path).relative_to(input_dir_path)
                    ).with_suffix(Path(path).suffix + ".json")
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with output_path.open("w", encoding="utf-8") as f:
                    json.dump([chunk.to_dict()
                               for chunk in self.get_raw_chunks(path)], f)

            else:
                continue
        print()

    def get_raw_chunks(self, path: Path) -> list[Chunk]:

        chunk_list: list[ChunkRaw] = []
        file_str, line_char_dict = self.get_line_char_dict(path)
        file_holder: FileHolder

        if str(path).lower().endswith(".py"):
            file_holder = self.parse_py(path, file_str)
            chunk_list = self.flatten_py(
                file_holder, line_char_dict)
        elif str(path).lower().endswith(".md"):
            file_holder = self.parse_md(path, file_str)
            if (file_holder.introduction and
                    file_holder.introduction.content.strip()):
                # print(file_holder.introduction)

                # print(
                #     f"id={file_holder.path.stem}.introduction,\n"
                #     f"path={file_holder.path},\n"
                #     "start_char="
                #     f"{line_char_dict[file_holder.introduction.start_line]},\n"
                #     "end_char="
                #     f"{line_char_dict[file_holder.introduction.end_line+1]-1}"
                #     f",\ncontent={file_holder.introduction.content}"
                #     )
                chunk_list.append(
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

            chunk_list += self.flatten_md(file_holder.sections,
                                          line_char_dict)
        else:
            file_holder = OtherHolder(path)
            file_sections = file_str.split("\n\n")

            file_holder.sections = ([
                line + "\n\n"
                for line in file_sections[:-1]] +
                [file_sections[-1]])

            counter = 0
            start_char = 0
            for section in file_holder.sections:

                if not section.strip():
                    continue

                end_char = (start_char + len(section) - 1)
                # print(
                #     f"id=other.{file_holder.path.stem}.section.{counter},\n"
                #     f"path={file_holder.path},\n"
                #     f"start_char={start_char},\n"
                #     f"end_char={end_char},\n"
                #     f"content={section}\n"
                # )
                chunk_list.append(
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

        return self.split_chunks(chunk_list)

    def parse_py(self, path: Path, file_str: str) -> PyHolder:

        out_file = PyHolder(path)
        parsed = ast.parse(file_str)
        misc_holder: MiscHolder | None = None
        # print(ast.dump(parsed, indent=4), end="\n\n\n")
        for item in parsed.body:
            # print(item)

            if (isinstance(item, ast.Import)):
                if misc_holder:
                    misc_holder.append("pre_Imports")
                    out_file.misc.append(misc_holder)
                    misc_holder = None

                for file_import in item.names:
                    out_file.imports.append(
                        file_import.name +
                        ((" as " + file_import.asname)
                            if file_import.asname else ""))
                if out_file.imports_start == -1:
                    out_file.imports_start = item.lineno
                out_file.imports_end = (item.end_lineno if item.end_lineno
                                        else item.lineno)

            elif (isinstance(item, ast.ImportFrom)):
                if misc_holder:
                    misc_holder.append("pre_Imports")
                    out_file.misc.append(misc_holder)
                    misc_holder = None

                for file_import in item.names:
                    out_file.imports.append(
                        (((item.level * ".") + item.module + ".")
                         if item.module else "") + file_import.name
                        + ((" as " + file_import.asname)
                           if file_import.asname else ""))
                if out_file.imports_start == -1:
                    out_file.imports_start = item.lineno
                out_file.imports_end = (item.end_lineno if item.end_lineno
                                        else item.lineno)

            elif (isinstance(item, ast.FunctionDef) or
                    isinstance(item, ast.AsyncFunctionDef)):
                # print(item.name, item.args.defaults[0].__dict__
                #       if item.args.defaults else "")
                # print(list(zip(item.args.args,
                #       item.args.defaults)))
                if misc_holder:
                    misc_holder.append(f"pre_{item.name}")
                    out_file.misc.append(misc_holder)
                    misc_holder = None

                args = item.args.posonlyargs + item.args.args
                defaults: list[ast.expr | None] = (
                    [None] * (len(args) - len(item.args.defaults))
                    + item.args.defaults
                )
                kw_args = item.args.kwonlyargs
                kw_defaults = item.args.kw_defaults

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
                        in zip(args + kw_args, defaults + kw_defaults)
                    ], str(ast.unparse(item.returns))
                    if item.returns else "Undefined",
                    str(ast.get_source_segment(file_str, item)),
                    ast.get_docstring(item)
                )
                if item.args.vararg:
                    funct.args.append("*" + item.args.vararg.arg)
                if item.args.kwarg:
                    funct.args.append("**" + item.args.kwarg.arg)

                out_file.functs.append(funct)

            elif isinstance(item, ast.ClassDef):
                if misc_holder:
                    misc_holder.append(f"pre_{item.name}")
                    out_file.misc.append(misc_holder)
                    misc_holder = None
                class_object = ClassHolder(
                    path, item.name, item.lineno, item.end_lineno
                    if item.end_lineno else item.lineno,
                    list(map(ast.unparse, item.bases)),
                    ast.get_docstring(item))
                for class_item in item.body:
                    if (isinstance(class_item, ast.FunctionDef) or
                            isinstance(class_item, ast.AsyncFunctionDef)):
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
                                str(ast.unparse(class_item.returns))
                                if class_item.returns else "Undefined",
                                str(ast.get_source_segment(file_str,
                                                           class_item)),
                                ast.get_docstring(class_item)
                            )
                        )
                        if class_item.args.vararg:
                            class_object.methods[-1].args.append(
                                "*" + class_item.args.vararg.arg)
                        if class_item.args.kwarg:
                            class_object.methods[-1].args.append(
                                "**" + class_item.args.kwarg.arg)

                    elif isinstance(class_item, ast.AnnAssign):
                        class_object.var_annotations.append(
                            ast.unparse(class_item.target) + ": " +
                            ast.unparse(class_item.annotation) +
                            ((" = " + ast.unparse(
                                class_item.value))
                                if class_item.value else "")
                        )
                    elif isinstance(class_item, ast.Assign):
                        class_object.var_annotations.append(
                            ast.unparse(class_item.targets[0]) +
                            " = " + ast.unparse(class_item.value)
                            if class_item.value else ""
                        )
                out_file.classes.append(class_object)

            else:
                if (isinstance(item, ast.If) and
                    isinstance(item.test, ast.Compare) and
                    isinstance(item.test.left, ast.Name) and
                    item.test.left.id == "__name__" and
                    len(item.test.ops) == 1 and
                    len(item.test.comparators) == 1 and
                    isinstance(item.test.ops[0], ast.Eq) and
                    isinstance(item.test.comparators[0], ast.Constant) and
                        item.test.comparators[0].value == "__main__"):
                    if misc_holder:
                        misc_holder.append("pre_MAIN_IF")
                        out_file.misc.append(misc_holder)
                        misc_holder = None
                    out_file.misc.append(MiscHolder(
                        path, "MAIN_IF", item.lineno,
                        item.end_lineno
                        if item.end_lineno
                        else item.lineno,
                        str(ast.get_source_segment(file_str, item)),
                    ))
                else:
                    if not misc_holder:
                        misc_holder = MiscHolder(path, None, item.lineno)
                    misc_holder.append(
                        end_line=(item.end_lineno
                                  if item.end_lineno else item.lineno),
                        body=str(ast.get_source_segment(file_str, item))
                    )
        if misc_holder:
            misc_holder.append("post_ALL")
            out_file.misc.append(misc_holder)
        return out_file

    def parse_md(self, path: Path, file_str: str) -> MDHolder:

        md_parse = MarkdownIt()

        out_file = MDHolder(path)
        out_file.introduction = MDSections(
            path, "introduction", 1, 1, 0, "",
        )
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
            if (token.type in ["paragraph_open"] or
                    token.map is None):
                continue

            if waiting_heading:
                if len(token.map) == 2:
                    section = MDSections(
                        path, token.content,
                        token.map[0]+1, token.map[1],
                        int(tag[1])
                    )
                elif len(token.map) == 1:
                    section = MDSections(
                        path, token.content,
                        token.map[0]+1, token.map[0]+1,
                        int(tag[0])
                    )
                else:
                    section = MDSections(
                        path, token.content,
                        -1, -1, int(tag)
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
                    stack[-1].end_line = (token.map[1]
                                          if len(token.map) == 2
                                          else token.map[0] + 1)

            else:
                # Text before the first heading
                out_file.introduction.content += token.content
                if len(token.map) == 2:
                    out_file.introduction.end_line = token.map[1]
                elif len(token.map) == 1:
                    out_file.introduction.end_line = token.map[0] + 1
                else:
                    out_file.introduction.end_line = -1

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

    # def flatten_file_holders(self) -> list[Chunk]:

    #     flattened_chunks: list[ChunkRaw] = []

    #     last_path: Path = Path("")
    #     line_char_dict: dict[int, int] = {}

    #     holders: list[FileHolder] | tqdm[FileHolder] = self.ingest_out.copy()

    #     print("\nFlattening Files...")

    #     if len(holders) > 500:
    #         holders = tqdm(holders)

    #     for file_holder in holders:

    #         # print(f"\nFlattening: {file_holder}", end="\n\n")

    #         if file_holder.path != last_path:
    #             line_char_dict = self.get_line_char_dict(file_holder.path)
    #             last_path = file_holder.path

    #             # print(file_holder.path)
    #             # print(line_char_dict)
    #             # print()

    #         if isinstance(file_holder, PyHolder):

    #             # print(file_holder)

    #             flattened_chunks += self.flatten_py(file_holder,
    #                                                 line_char_dict)

    #         elif isinstance(file_holder, MDHolder):

    #             # print(file_holder)
    #             # print(line_char_dict)
    #             # print()

    #             if (file_holder.introduction and
    #                     file_holder.introduction.content.strip()):
    #                 # print(file_holder.introduction)

    #                 # print(
    #                 #     f"id={file_holder.path.stem}.introduction,\n"
    #                 #     f"path={file_holder.path},\n"
    #                 #     "start_char="
    #                 #     f"{line_char_dict[
    #                 #         file_holder.introduction.start_line]},\n"
    #                 #     "end_char="
    #                 #     f"{line_char_dict[
    #                 #         file_holder.introduction.end_line+1]-1}"
    #                 #     f",\ncontent={file_holder.introduction.content}"
    #                 #     )
    #                 flattened_chunks.append(
    #                     ChunkRaw(
    #                         id=f"{file_holder.path.stem}.introduction",
    #                         path=file_holder.path,
    #                         type=ChunkType.INTRODUCTION,
    #                         parent=None,
    #                         start_char=line_char_dict[
    #                             file_holder.introduction.start_line],
    #                         end_char=line_char_dict[
    #                             file_holder.introduction.end_line + 1] - 1,
    #                         content=file_holder.introduction.content
    #                     )
    #                 )

    #             flattened_chunks += self.flatten_md(file_holder.sections,
    #                                                 line_char_dict)

    #         else:
    #             file_holder = cast(OtherHolder, file_holder)
    #             counter = 0
    #             start_char = 0
    #             for section in file_holder.sections:

    #                 if not section.strip():
    #                     continue

    #                 end_char = (start_char + len(section) - 1)
    #                 # print(
    #                 #     f"id=other.{file_holder.path.stem}"
    #                 #     f".section.{counter},\n"
    #                 #     f"path={file_holder.path},\n"
    #                 #     f"start_char={start_char},\n"
    #                 #     f"end_char={end_char},\n"
    #                 #     f"content={section}\n"
    #                 # )
    #                 flattened_chunks.append(
    #                     ChunkRaw(
    #                         id=(f"other.{file_holder.path.stem}."
    #                             f"section.{counter}"),
    #                         path=file_holder.path,
    #                         parent=None,
    #                         type=ChunkType.OTHER,
    #                         start_char=start_char,
    #                         end_char=end_char,
    #                         content=section
    #                     )
    #                 )
    #                 start_char = end_char + 1
    #                 counter += 1
    #     print()
    #     return self.split_chunks(flattened_chunks)

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
                    parent=", ".join(cls.inherits),
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
            # print(section)

            # print(f"id={section.path.stem}.section."
            #       f"{section.name.replace(' ', '_')},\n"
            #       f"path={section.path},\n"
            #       f"start_char={line_char_dict[section.start_line]},\n"
            #       f"end_char={line_char_dict[section.end_line + 1] - 1},\n"
            #       f"content={section.content}"
            #       )
            if section.children:
                section.content += ("\n\nChildren Sections: " + " ".join(
                    [child.name for child in section.children]))
            if not section.content.strip():
                continue
            flattened_chunks.append(
                ChunkRaw(
                    id=f"{section.path.stem}.section.{
                        section.name.replace(' ', '_')}",
                    path=section.path,
                    type=ChunkType.SECTION,
                    parent=None,
                    start_char=line_char_dict[section.start_line],
                    end_char=line_char_dict[section.end_line + 1] - 1,
                    content=section.content.strip()
                )
            )
            if section.children:
                flattened_chunks += self.flatten_md(section.children,
                                                    line_char_dict)

        return flattened_chunks

    def get_line_char_dict(self, file_path: Path
                           ) -> tuple[str, dict[int, int]]:
        line_char_dict: dict[int, int] = {}
        file_str = ""
        char_count = 0
        with file_path.open("r", encoding="utf-8") as f:
            for line_number, line in enumerate(f):
                file_str += line
                line_char_dict[line_number+1] = char_count
                char_count += len(line)

            line_char_dict[len(line_char_dict)+1] = char_count + 1
            line_char_dict[len(line_char_dict)+1] = char_count + 1
        return (file_str, line_char_dict)

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
