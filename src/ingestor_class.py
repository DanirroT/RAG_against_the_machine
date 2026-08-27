from pathlib import Path
from typing import cast
import json
import ast
from markdown_it import MarkdownIt
from src import (InputHolder, FileHolder, PyHolder, MDHolder, MDSections,
                 OtherHolder, FunctHolder, ClassHolder, Chunk, ChunkType
                 )


class IngestorClass():

    arg_inputs: InputHolder

    def __init__(self, input_dir_path: Path, output_dir_path: Path,
                 arg_inputs: InputHolder) -> None:

        self.arg_inputs = arg_inputs

        ingest_out: list[FileHolder] = self._load_all_files(input_dir_path)

        print("current output\n\n")

        print("\n".join(map(str, ingest_out)))

        print("output:", output_dir_path)

        # input("starting creation")
        # for obj in ingest_out:
        #     json_path = (output_dir_path /
        #                  obj.path.relative_to(input_dir_path))
        #     json_path = json_path.with_suffix(json_path.suffix + ".json")
        #     json_path.parent.mkdir(parents=True, exist_ok=True)
        #     print("folder created")
        #     with json_path.open("w") as file:
        #         json.dump(obj.to_dict(), file, indent=4, ensure_ascii=False)

        ingest_out_flattened = self.flatten_file_holders(ingest_out)

        print("flattened output:", "\n\n".join(map(str, ingest_out_flattened)))

        input()

        last_path: Path | None = None

        for obj in ingest_out_flattened:
            current_path = (output_dir_path /
                            Path(obj.path).relative_to(
                                input_dir_path)).with_suffix(
                                    Path(obj.path).suffix + ".json")

            # print("path:\t", current_path,
            #       "\npath:\t", str(last_path), "\n\n")

            if not last_path or str(current_path) != str(last_path):
                # print("\t New", str(current_path), str(last_path),
                #       str(current_path) != str(last_path))
                current_path.parent.mkdir(parents=True, exist_ok=True)
                if last_path:
                    with last_path.open("a") as file:
                        file.write("\n]\n")
                with current_path.open("x") as file:
                    file.write("[\n")
            else:
                # print("\t Same")
                with current_path.open("a") as file:
                    file.write(",\n")
            with current_path.open("a") as file:
                json.dump(obj.to_dict(), file, indent=4, ensure_ascii=False)
            last_path = current_path
            # input()

        if last_path:
            with last_path.open("a") as file:
                file.write("\n]")
        print("files created")

    def _load_all_files(self, input_dir_path: Path) -> list[FileHolder]:

        ingest_out: list[FileHolder] = []

        print("\n\n")
        for path in input_dir_path.rglob("*"):
            print(path)
            if path.is_dir() or any(part.startswith(".")
                                    for part in path.parts):
                print()
                continue
            out_file: FileHolder
            if path.is_file():
                with path.open("r") as file:
                    file_str = file.read()
                if str(path).endswith(".py"):
                    out_file = self.parse_py(path, file_str)
                elif str(path).endswith(".md"):
                    out_file = self.parse_md(path, file_str)
                else:
                    out_file = OtherHolder(path)
                    print(file_str)
                    file_sections = file_str.split("\n\n")

                    out_file.sections = ([
                        line + "\n\n"
                        for line in file_sections[:-1]] +
                        [file_sections[-1]])

            else:
                continue

            print("\n\n")
            ingest_out.append(out_file)

        return ingest_out

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

            if (isinstance(item, ast.ImportFrom)):

                for file_import in item.names:
                    out_file.imports.append(
                        ((item.module + ".") if item.module else "")
                        + file_import.name +
                        ((" as " + file_import.asname)
                         if file_import.asname else ""))

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
                    item.name, item.lineno,
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
                    item.name, item.lineno, item.end_lineno
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
                                class_item.name, class_item.lineno,
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

        for token in md_parsed:
            print(token)
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
                        tag, int(tag[1]), token.content,
                        token.map[0], token.map[1]
                    )
                elif len(token.map) == 1:
                    section = MDSections(
                        tag, int(tag[0]), token.content,
                        token.map[0], token.map[0]
                    )
                else:
                    section = MDSections(
                        tag, int(tag), token.content, -1, -1
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

            else:
                # Text before the first heading
                if len(token.map) == 2:
                    section = MDSections(
                        tag, int(tag), "introduction",
                        token.map[0], token.map[1], token.content,
                    )
                elif len(token.map) == 1:
                    section = MDSections(
                        tag, int(tag), "introduction",
                        token.map[0], token.map[0], token.content,
                    )
                else:
                    section = MDSections(tag, int(tag), "introduction",
                                         -1, -1, token.content)
                out_file.introduction = section

        # file_sections = file_str.split("\n#")

        # out_file["Introduction"] = repr(file_sections[0]
        #                                       + "\n")
        # out_file["Sections"] = ([
        #     ("#" + line + "\n")
        #     for line in file_sections[1:-1]] +
        #     ["#" + file_sections[-1]])

        return out_file

    def flatten_file_holders(self, file_holders: list[FileHolder]
                             ) -> list[Chunk]:

        flattened_chunks: list[Chunk] = []

        for file_holder in file_holders:
            if isinstance(file_holder, PyHolder):

                flattened_chunks += self.flatten_py(file_holder)

            elif isinstance(file_holder, MDHolder):

                if file_holder.introduction:
                    flattened_chunks.append(
                        Chunk(
                            id=f"{file_holder.path.stem}.introduction",
                            path=str(file_holder.path),
                            type=ChunkType.INTRODUCTION,
                            parent=None,
                            start_line=file_holder.introduction.start_line,
                            end_line=file_holder.introduction.end_line,
                            content=file_holder.introduction.content
                        )
                    )

                flattened_chunks += self.flatten_md(
                    file_holder.sections, file_holder.path)

            else:
                file_holder = cast(OtherHolder, file_holder)
                counter = 0
                for section in file_holder.sections:
                    flattened_chunks.append(
                        Chunk(
                            id=(f"other.{file_holder.path.stem}."
                                f"section.{counter}"),
                            path=str(file_holder.path),
                            parent=None,
                            type=ChunkType.OTHER,
                            start_line=-1,
                            end_line=-1,
                            content=section
                        )
                    )
                    counter += 1

        return flattened_chunks

    def flatten_py(self, py_holder: PyHolder) -> list[Chunk]:

        flattened_chunks: list[Chunk] = []

        if py_holder.imports:
            flattened_chunks.append(
                Chunk(
                    id=f"{py_holder.path.stem}.import_imports",
                    path=str(py_holder.path),
                    type=ChunkType.IMPORT,
                    parent=None,
                    start_line=0,
                    end_line=-1,
                    content="\n".join([imp for imp in py_holder.imports])
                )
            )

        for funct in py_holder.functs:
            flattened_chunks.append(
                Chunk(
                    id=f"{py_holder.path.stem}.function.{funct.name}",
                    path=str(py_holder.path),
                    type=ChunkType.FUNCTION,
                    parent=None,
                    start_line=funct.start_line,
                    end_line=funct.end_line,
                    content=funct.body
                )
            )
        for cls in py_holder.classes:
            flattened_chunks.append(
                Chunk(
                    id=f"{py_holder.path.stem}.class.{cls.name}",
                    path=str(py_holder.path),
                    type=ChunkType.CLASS,
                    parent=None,
                    start_line=cls.start_line,
                    end_line=cls.end_line,
                    content=(cls.docstring if cls.docstring else ""
                             + "\n".join(cls.var_annotations))
                )
            )

            flattened_chunks += [
                Chunk(
                    id=(f"{py_holder.path.stem}.class.{cls.name}"
                        f".method.{method.name}"),
                    path=str(py_holder.path),
                    type=ChunkType.METHOD,
                    parent=cls.name,
                    start_line=method.start_line,
                    end_line=method.end_line,
                    content=method.body
                )
                for method in cls.methods
            ]

        return flattened_chunks

    def flatten_md(self, md_holder: list[MDSections], path: Path
                   ) -> list[Chunk]:

        flattened_chunks: list[Chunk] = []

        for section in md_holder:
            flattened_chunks.append(
                Chunk(
                    id=f"{path.stem}.section.{section.name}",
                    path=str(path),
                    type=ChunkType.SECTION,
                    parent=None,
                    start_line=section.start_line,
                    end_line=section.end_line,
                    content=section.content
                )
            )
            if section.children:
                flattened_chunks += self.flatten_md(section.children, path)

        return flattened_chunks
