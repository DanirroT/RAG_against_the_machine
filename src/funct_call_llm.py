import sys
from dotenv import load_dotenv
# from tqdm import tqdm
from pathlib import Path
from shutil import rmtree
# import httpcore
from typing import Any, cast
import json
import ast
from markdown_it import MarkdownIt
from src import (get_from_json_file, create_file, create_dir,
                 InputHolder, FileHolder, PyHolder, MDHolder, MDSections,
                 OtherHolder, FunctHolder, ClassHolder, DefFunctException,
                 Chunk, ChunkScorePair, ChunkType
                 )
# from llm_sdk import Small_LLM_Model


class RAGCodeBaseLLM():

    dataset: dict[str, Any]

    arg_inputs: InputHolder

    save_directory: Path
    student_answer_path: Path
    student_search_results_path: Path

    # raw_prompts: list[str]
    # funct_defs: list[FunctDef]

    # _llm: Small_LLM_Model
    # llm_files: dict[str, str]

    # vocab_text_int: dict[str, int]
    # vocab_int_text: dict[int, str]

    # tokenized_int_funct_list: list[list[int]]
    # instructions: list[int]
    # universal_start: list[int]
    # universal_post_prompt: list[int]

    # to_export: (str |
    #             dict[str, str | dict[str, Any]] |
    #             list[str | dict[str, str | dict[str, Any]]])

    # mode: str = Field()
    # max_chunk_size: int = Field(gt=0)
    # dataset_path: str = Field(min_length=1)
    # k: float = Field(gt=0, lt=1)
    # save_directory: str = Field(min_length=1)
    # student_answer_path: str = Field(min_length=1)
    # max_context_length: int = Field(gt=0)
    # student_search_results_path: str = Field(min_length=1)
    # question: str = Field()

    def __init__(self, arg_inputs: InputHolder, mode: bool = True) -> None:

        force = True

        if arg_inputs:
            print("arg_inputs Exists")

            self.save_directory = create_dir(
                arg_inputs.save_directory, force)
            print(f"{self.save_directory} Created")

            if arg_inputs.mode == "answer":
                self.student_answer_path = create_file(
                    arg_inputs.student_answer_path, force)
                print(f"{self.student_answer_path} Created")

            if arg_inputs.mode == "search":
                self.student_search_results_path = create_file(
                    arg_inputs.student_search_results_path, force)
                print(f"{self.student_search_results_path} Created")

            self.dataset = get_from_json_file(arg_inputs.dataset_path)
            print(f"{arg_inputs.dataset_path} Loaded")
        else:
            raise ValueError("No Arguments were passed to the Class")

        self.arg_inputs = arg_inputs

        if self.arg_inputs.mode == "index":
            input_dir_str = "data/to_process/"
            output_dir_str = "data/processed/"

            input_dir_path = Path(input_dir_str)
            if not input_dir_path.exists():
                raise ValueError(f"Path '{input_dir_str}' does not exist")
            if not input_dir_path.is_dir():
                raise ValueError(f"Path '{input_dir_str}' is not a Directory")

            output_dir_path = Path(output_dir_str)
            if output_dir_path.exists():
                # if not output_dir_path.is_dir():
                #     answer = input(
                #         f"'{output_dir_str}' exists but is not a directory."
                #         "\nReplace it with a directory? [y/N]: "
                #     ).strip().lower()
                # else:
                #     answer = input(
                #         f"Directory '{output_dir_str}' already exists.\n"
                #         "Overwrite its contents? [y/N]: "
                #     ).strip().lower()

                # if answer != "y":
                #     print("Operation cancelled.")
                #     raise FileExistsError
                # else:
                if output_dir_path.is_file():
                    output_dir_path.unlink()
                else:
                    rmtree(output_dir_path)
            output_dir_path.mkdir(parents=True)

            self._ingest(input_dir_path, output_dir_path)
            print(f"Ingestion complete! Indices saved under {output_dir_str}")
            return

        elif self.arg_inputs.mode == "answer":
            input_dir_str = "data/processed/"
            output_dir_str = "data/answer/"
            output_dir_path = Path(output_dir_str)
            if output_dir_path.exists():
                if output_dir_path.is_file():
                    output_dir_path.unlink()
                else:
                    rmtree(output_dir_path)
            output_dir_path.mkdir(parents=True)
            query = self.arg_inputs.question
            output_dir_str = ""
            self._str_answer(query, output_dir_path, self.arg_inputs.k)

        elif self.arg_inputs.mode == "answer_dataset":
            input_dir_str = "data/processed/"
            output_dir_str = "data/answers/"
            output_dir_path = Path(output_dir_str)
            if output_dir_path.exists():
                if output_dir_path.is_file():
                    output_dir_path.unlink()
                else:
                    rmtree(output_dir_path)
            output_dir_path.mkdir(parents=True)
            query = self.arg_inputs.question
            output_dir_str = ""
            self._file_answer(query, output_dir_path)

        elif self.arg_inputs.mode == "search":
            input_dir_str = "data/processed/"
            output_dir_str = "data/result/"
            output_dir_path = Path(output_dir_str)
            if output_dir_path.exists():
                if output_dir_path.is_file():
                    output_dir_path.unlink()
                else:
                    rmtree(output_dir_path)
            output_dir_path.mkdir(parents=True)
            lookup = self.arg_inputs.question
            output_dir_str = ""
            self._str_search(lookup, output_dir_path)

        elif self.arg_inputs.mode == "search_dataset":
            input_dir_str = "data/processed/"
            output_dir_str = "data/results/"
            output_dir_path = Path(output_dir_str)
            if output_dir_path.exists():
                if output_dir_path.is_file():
                    output_dir_path.unlink()
                else:
                    rmtree(output_dir_path)
            output_dir_path.mkdir(parents=True)
            lookup = self.arg_inputs.question
            output_dir_str = ""
            self._file_search(lookup, output_dir_path)

        elif self.arg_inputs.mode == "evaluate":
            code_questions_file_str = ("data/datasets/UnansweredQuestions/"
                                       "dataset_code_public.json")
            docs_questions_file_str = ("data/datasets/UnansweredQuestions/"
                                       "dataset_docs_public.json")
            code_answers_file_str = ("data/datasets/AnsweredQuestions/"
                                     "dataset_code_public.json")
            docs_answers_file_str = ("data/datasets/AnsweredQuestions/"
                                     "dataset_docs_public.json")

            code_questions_file = Path(code_questions_file_str)
            docs_questions_file = Path(docs_questions_file_str)
            code_answers_file = Path(code_answers_file_str)
            docs_answers_file = Path(docs_answers_file_str)

            output_dir_str = "data/eval_results/"
            output_dir_path = Path(output_dir_str)
            if output_dir_path.exists():
                if output_dir_path.is_file():
                    output_dir_path.unlink()
                else:
                    rmtree(output_dir_path)
            output_dir_path.mkdir(parents=True)
            output_dir_str = ""
            self._evaluate(input_dir_path, output_dir_path)

        # try:
        #     self._load_llm(mode)
        # except ModuleNotFoundError as e:
        #     raise ModuleNotFoundError(
        #         f"Module Dependencies were not met:\n{e}")
        # except httpcore.ConnectError as e:
        #     raise httpcore.ConnectError(
        #         "Small_LLM_Model was unable to Connect. "
        #         f"Check Connection and Try again another time\n{e}")

        # except Exception as e:
        #     raise Exception("An unexpected error has occurred during "
        #                     f"LLM Class Creation:\n{e}")

        # try:

        #     self._make_deffunct_ids()

        # except DefFunctException as e:
        #     error_len = e.e_len
        #     del e.e_len
        #     raise ValueError("An error has occurred in the Processing of "
        #                      f"Callable Function number {error_len}: "
        #                      f"{self.funct_defs[error_len]}:\n\n{e}")

    def redefine_inputs(self, arg_inputs: InputHolder) -> None:

        if arg_inputs:
            print("arg_inputs Exists")

            self.save_directory = create_dir(
                arg_inputs.save_directory)
            print(f"{self.save_directory} Created")
            self.student_answer_path = create_file(
                arg_inputs.student_answer_path)
            print(f"{self.student_answer_path} Created")
            self.student_search_results_path = create_file(
                arg_inputs.student_search_results_path)
            print(f"{self.student_search_results_path} Created")

            self.dataset = get_from_json_file(arg_inputs.dataset_path)
            print(f"{self.dataset} Loaded")

        else:
            raise ValueError("No Arguments were passed to the Class")

        try:

            self._make_deffunct_ids()

        except DefFunctException as e:
            error_len = e.e_len
            del e.e_len
            raise ValueError("An error has occurred in the Processing of "
                             f"Callable Function number {error_len}: "
                             f"{self.funct_defs[error_len]}:\n\n{e}")

    def _ingest(self, input_dir_path: Path, output_dir_path: Path) -> None:

        print("input:", input_dir_path)

        md_parse = MarkdownIt()

        ingest_out: list[FileHolder] = []

        print("\n\n")
        for path in input_dir_path.rglob("*"):
            print(path)
            if path.is_dir() or any(part.startswith(".")
                                    for part in path.parts):
                print()
                continue
            file_out_lists: FileHolder
            if path.is_file():
                with path.open("r") as file:
                    file_str = file.read()
                if str(path).endswith(".py"):
                    file_out_lists = PyHolder(path)
                    parsed = ast.parse(file_str)
                    # print(ast.dump(parsed, indent=4), end="\n\n\n")
                    for item in parsed.body:
                        # print(item)

                        if (isinstance(item, ast.Import)):
                            for file_import in item.names:
                                file_out_lists.imports.append(
                                    file_import.name +
                                    ((" as " + file_import.asname)
                                     if file_import.asname else ""))

                        if (isinstance(item, ast.ImportFrom)):

                            for file_import in item.names:
                                file_out_lists.imports.append(
                                    ((item.module + ".")
                                     if item.module else "")
                                    + file_import.name +
                                    ((" as " + file_import.asname)
                                     if file_import.asname else ""))

                        if isinstance(item, ast.FunctionDef):
                            # print(item.name, item.args.defaults[0].__dict__
                            #       if item.args.defaults else "")
                            # print(list(zip(item.args.args,
                            #       item.args.defaults)))
                            funct = FunctHolder(
                                item.name, item.lineno,
                                item.end_lineno if item.end_lineno
                                else item.lineno,
                                [arg.arg + ((" = " + str(defaults.value))
                                            if defaults is not None
                                            else "")
                                    for arg, defaults in zip(
                                    item.args.args,
                                    item.args.defaults)],
                                str(ast.unparse(item.returns)
                                    if item.returns else None),
                                ast.get_source_segment(file_str, item),
                                ast.get_docstring(item))

                            if (funct.body.count("\n") >
                                    self.arg_inputs.max_chunk_size):
                                raise ValueError(
                                    f"Function '{funct.name}' is too large"
                                )

                            file_out_lists.functs.append(funct)

                        if isinstance(item, ast.ClassDef):
                            class_object = ClassHolder(
                                item.name,
                                item.lineno,
                                item.end_lineno,
                                ast.get_docstring(item),
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
                                    class_object.methods.append(
                                        FunctHolder(
                                            class_item.name,
                                            class_item.lineno,
                                            class_item.end_lineno
                                            if class_item.end_lineno
                                            else class_item.lineno,
                                            [arg.arg + ((
                                                " = " + str(defaults.value))
                                                if str(defaults) == str(None)
                                                else "")
                                             for arg, defaults in zip(
                                                class_item.args.args,
                                                class_item.args.defaults)],
                                            str(ast.unparse(
                                                class_item.returns)),
                                            ast.get_source_segment(
                                                file_str, class_item),
                                            str(ast.get_docstring(class_item)))
                                    )
                                if isinstance(class_item, ast.AnnAssign):
                                    class_object.var_annotations.append(
                                        ast.unparse(class_item.target) + ": " +
                                        ast.unparse(class_item.annotation) +
                                        ((" = " + ast.unparse(
                                            class_item.value))
                                         if class_item.value else "")
                                    )
                            file_out_lists.classes.append(class_object)

                elif str(path).endswith(".md"):
                    file_out_lists = MDHolder(path)
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
                                file_out_lists.sections.append(section)

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
                                section = MDSections(
                                    tag, int(tag), "introduction",
                                    -1, -1, token.content
                                )
                            file_out_lists.introduction = section

                    # file_sections = file_str.split("\n#")

                    # file_out_lists["Introduction"] = repr(file_sections[0]
                    #                                       + "\n")
                    # file_out_lists["Sections"] = ([
                    #     ("#" + line + "\n")
                    #     for line in file_sections[1:-1]] +
                    #     ["#" + file_sections[-1]])

                else:
                    file_out_lists = OtherHolder(path)
                    print(file_str)
                    file_sections = file_str.split("\n\n")

                    file_out_lists.sections = ([
                        line + "\n\n"
                        for line in file_sections[:-1]] +
                        [file_sections[-1]])

            else:
                continue

            print("\n\n")
            ingest_out.append(file_out_lists)

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

        with last_path.open("a") as file:
            file.write("\n]")
        print("files created")

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
                            id=f"{file_holder.path.stem}_introduction",
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
                counter = 0
                for section in file_holder.sections:
                    flattened_chunks.append(
                        Chunk(
                            id=(f"other_{file_holder.path.stem}_"
                                f"section_{counter}"),
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

        for funct in py_holder.functs:
            flattened_chunks.append(
                Chunk(
                    id=f"{py_holder.path.stem}_function_{funct.name}",
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
                    id=f"{py_holder.path.stem}_class_{cls.name}",
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
                    id=(f"{py_holder.path.stem}_class_{cls.name}"
                        f"_method_{method.name}"),
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
                    id=f"{path.stem}_section_{section.name}",
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

    def _str_answer(self, query: str, output_dir_path: Path, k: int) -> None:
        pass

    def _file_answer(self, query: str, output_dir_path: Path) -> None:
        pass

    def _str_search(self, lookup: str, output_dir_path: Path) -> None:
        pass

    def _file_search(self, lookup: str, output_dir_path: Path) -> None:
        pass

    def _evaluate(self, input_dir_path: Path, output_dir_path: Path) -> None:
        pass

    def _load_llm(self, mode: bool = True) -> None:

        if self._llm:
            return

        self.llm_files = {}
        print()

        load_dotenv()
        # self._llm = Small_LLM_Model()

        self.llm_files["vocab"] = self._llm.get_path_to_vocab_file()
        self.llm_files["merges"] = self._llm.get_path_to_merges_file()
        self.llm_files["tokenizer"] = (
            self._llm.get_path_to_tokenizer_file())

        with open(self.llm_files["vocab"]) as vocab_file:
            self.vocab_text_int: dict[str, int] = json.load(vocab_file)

        self.vocab_int_text = {}

        for k, v in self.vocab_text_int.items():
            self.vocab_int_text[v] = k

    def _make_deffunct_ids(self) -> None:

        self.tokenized_int_funct_list = []

        for funct in self.funct_defs:

            tokenized_tensor_funct = self._llm.encode(str(funct))

            to_add: list[int] = (  # pyright: ignore
                tokenized_tensor_funct[0].tolist())  # pyright: ignore

            self.tokenized_int_funct_list.append(
                [self.vocab_text_int["ĠĠĠĠ"]
                 if x == self.vocab_text_int['ĉ']
                 else x for x in to_add]
            )

        self.instructions = []

        json_prompt: list[int] = (  # pyright: ignore
            self._llm.encode(
                "JSON Function:\n")[0].tolist())  # pyright: ignore
        format_request: list[int] = (  # pyright: ignore
            self._llm.encode(
                "JSON Format:\n"
                "{\n"
                "    \"prompt\": \"given prompt\",\n"
                "    \"name\": \"fn_name\",\n"
                "    \"parameters\": {\n"
                "        \"param1\": param1_val,\n"
                "        \"param2\": param2_val\n"
                "        <...>\n"
                "    }\n"
                "}\n\n"
            )[0].tolist())  # pyright: ignore

        self.universal_start = self._llm.encode(  # pyright: ignore
            "{\n"
            "    \"prompt\": \""
        )[0].tolist()  # pyright: ignore
        self.universal_post_prompt = self._llm.encode(  # pyright: ignore
            "\",\n"
            "    \"name\": \""
        )[0].tolist()  # pyright: ignore

        for t_funct in self.tokenized_int_funct_list:
            self.instructions += json_prompt + t_funct

        self.instructions += format_request

    def run_model(self) -> None:

        self.to_export = []

        for prompt in self.raw_prompts:

            prompt_id = self.prompt_to_id(prompt)

            starting = (self.universal_start + prompt_id
                        + self.universal_post_prompt)

            added_token = self.instructions + starting
            answer_len: int = len(starting)
            instruct_len: int = len(self.instructions)

            container_log: list[str] = ["{", "\""]

            while True:

                if ((answer_len >= 120)):
                    print("Response too long, Cutting", container_log,
                          sep="\t")
                    logits_funct = [float(1) for _ in range(151643)]
                    if container_log[-1] == "{":
                        logits_funct[self.vocab_text_int["}"]] = sys.maxsize
                    if container_log[-1] == "[":
                        logits_funct[self.vocab_text_int["]"]] = sys.maxsize
                    if container_log[-1] == "\"":
                        logits_funct[self.vocab_text_int["\""]] = sys.maxsize

                else:
                    logits_funct = (self._llm.get_logits_from_input_ids(
                        added_token))

                max_val = max(logits_funct)

                max_val_ind = logits_funct.index(max_val)

                max_val_ind = self._post_gen_exceptions(
                    max_val_ind, added_token[-1])

                added_token.append(max_val_ind)

                container_log = self._container_management(container_log,
                                                           added_token[-1])

                if not container_log:
                    break

                answer_len += 1

            str_response = self.id_decode(added_token[instruct_len:])

            self.to_export.append(str_response)

    def prompt_to_id(self, prompt: str) -> list[int]:

        tokenized_prompt = self._llm.encode(prompt)

        tokenized_int_prompt: list[int] = (  # pyright: ignore
            tokenized_prompt[0].tolist())  # pyright: ignore

        return (tokenized_int_prompt)

    def export_to_file(self, file_path: Path) -> None:

        exp_str: str

        if isinstance(self.to_export, str):
            exp_str = self.to_export
        elif isinstance(self.to_export, dict):
            exp_str = json.dumps([self.to_export], indent=4)
        elif isinstance(self.to_export, list):  # pyright: ignore
            if isinstance(self.to_export[0], str):

                to_export: str = cast(str, self.to_export)
                out_list: list[str] = []

                for out in to_export:
                    in_list = [x for x in out.split("\n") if x]
                    out_list.append("\n    ".join(in_list))
                exp_str = "[\n    " + ",\n    ".join(out_list) + "\n]"

            elif isinstance(self.to_export[0], dict):  # pyright: ignore
                exp_str = json.dumps(self.to_export, indent=4)

            else:
                raise TypeError(
                    "'self.to_export' is an unknown type:\n\n---\n\n"
                    f"{self.to_export}\n\n---\n\nType: {type(self.to_export)}")
        else:
            raise TypeError(
                "'self.to_export' is an unknown type:\n\n---\n\n"
                f"{self.to_export}\n\n---\n\nType: {type(self.to_export)}")

        out_str: str = ""

        for i, char in enumerate(exp_str):
            if char == "\\":
                if i == 0:
                    out_str += "\\\\"
                elif exp_str[i - 1] == "\\":
                    out_str += char
                elif i + 1 >= len(exp_str):
                    out_str += "\\\\"
                elif exp_str[i + 1] not in "\\\"":
                    out_str += "\\\\"
                else:
                    out_str += char
            else:
                out_str += char

        try:
            with file_path.open("w") as output_file:
                output_file.write(out_str)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Output File \"{file_path}\" "
                                    f"not found {e}")

    def id_decode(self, ids: list[int]) -> str:

        if self._llm:
            return self._llm.decode(ids)
        else:
            return "".join([self.vocab_int_text[i] for i in ids]
                           ).replace("Ċ", "\n").replace("Ġ", " ")
