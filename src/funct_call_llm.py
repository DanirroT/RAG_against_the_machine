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
                 OtherHolder, FunctHolder, ClassHolder, DefFunctException
                 )
# from llm_sdk import Small_LLM_Model


class RAGCodeBaseLLM():

    dataset: dict[str, Any]

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

        if arg_inputs.mode == "index":
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

        elif arg_inputs.mode == "answer":
            query = arg_inputs.question
            output_dir_str = ""
            self._str_answer(query, output_dir_path)

        elif arg_inputs.mode == "answer_dataset":
            query = arg_inputs.question
            output_dir_str = ""
            self._file_answer(query, output_dir_path)

        elif arg_inputs.mode == "search":
            lookup = arg_inputs.question
            output_dir_str = ""
            self._str_search(lookup, output_dir_path)

        elif arg_inputs.mode == "search_dataset":
            lookup = arg_inputs.question
            output_dir_str = ""
            self._file_search(lookup, output_dir_path)

        elif arg_inputs.mode == "evaluate":
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
            if path.is_dir() or str(path).startswith(".") or "/." in str(path):
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
                                    item.module + "." +
                                    file_import.name +
                                    ((" as " + file_import.asname)
                                     if file_import.asname else ""))

                        if isinstance(item, ast.FunctionDef):
                            # print(item.name, item.args.defaults[0].__dict__ if item.args.defaults else "")
                            # print(list(zip(item.args.args, item.args.defaults)))
                            file_out_lists.functs.append(
                                FunctHolder(
                                    item.name,
                                    item.lineno,
                                    item.end_lineno,
                                    [arg.arg + ((" = " + str(defaults.value))
                                                if str(defaults) == str(None)
                                                else "")
                                     for arg, defaults in zip(
                                         item.args.args, item.args.defaults)],
                                    str(ast.unparse(item.returns)),
                                    ast.get_source_segment(file_str, item),
                                    ast.get_docstring(item))
                            )

                        if isinstance(item, ast.ClassDef):
                            class_object = ClassHolder(
                                item.name,
                                item.lineno,
                                item.end_lineno,
                                ast.get_docstring(item),
                                list(map(ast.unparse, item.bases)))
                            for class_item in item.body:
                                if isinstance(class_item, ast.FunctionDef):
                                    # print(class_item.name, type(class_object.methods))
                                    # print(len(class_item.args.args), len(class_item.args.defaults))
                                    # group = list(zip(class_item.args.args, class_item.args.defaults))
                                    # for arg, const in group:
                                    #     print(arg.arg, const.value)
                                    # print(list(zip(class_item.args.args, class_item.args.defaults)))
                                    class_object.methods.append(
                                        FunctHolder(
                                            class_item.name,
                                            item.lineno,
                                            item.end_lineno,
                                            [arg.arg + ((
                                                " = " + str(defaults.value))
                                                if str(defaults) == str(None)
                                                else "")
                                             for arg, defaults in zip(
                                                class_item.args.args, class_item.args.defaults)],
                                            str(ast.unparse(class_item.returns)),
                                            ast.get_source_segment(file_str, class_item),
                                            str(ast.get_docstring(class_item)))
                                    )
                                if isinstance(class_item, ast.AnnAssign):
                                    class_object.var_annotations.append(
                                        ast.unparse(class_item.target) + ": " +
                                        ast.unparse(class_item.annotation) +
                                        ((" = " + ast.unparse(class_item.value))
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
                                    tag, int(tag[1]), token.content, token.map[0], token.map[1]
                                )
                            elif len(token.map) == 1:
                                section = MDSections(
                                    tag, int(tag[1]), token.content, token.map[0], token.map[0]
                                )
                            else:
                                section = MDSections(
                                    tag, int(tag[1]), token.content, -1, -1
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
                                    tag, int(tag), "introduction", token.map[0], token.map[1], token.content,
                                )
                            elif len(token.map) == 1:
                                section = MDSections(
                                    tag, int(tag), "introduction", token.map[0], token.map[0], token.content,
                                )
                            else:
                                section = MDSections(
                                    tag, int(tag), "introduction", -1, -1, token.content
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

    def _str_answer(self, query: str, output_dir_path: Path) -> None:
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
        self._llm = Small_LLM_Model()

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

    def _post_gen_exceptions(self, max_val_ind: int,
                             last_added_token: int) -> int:

        return_val = max_val_ind

        if (max_val_ind in [self.vocab_text_int["}\""],
                            self.vocab_text_int["}\"Ċ"],
                            self.vocab_text_int["}\"ĊĊ"]]):
            return_val = self.vocab_text_int["}"]

        elif (max_val_ind in [self.vocab_text_int["\\"]]):
            return_val = self.vocab_text_int["\\\\"]

        elif (max_val_ind in [self.vocab_text_int["]\""],
                              self.vocab_text_int["]\"Ċ"]]):
            return_val = self.vocab_text_int["]"]

        elif (max_val_ind in [self.vocab_text_int["}ĊĊ"]]):
            return_val = self.vocab_text_int["}Ċ"]

        elif (max_val_ind in [self.vocab_text_int[")\""],
                              self.vocab_text_int[")\"Ċ"]]):
            return_val = self.vocab_text_int[")"]

        elif (max_val_ind in [self.vocab_text_int["Ġ\""]] and
              last_added_token in [self.vocab_text_int["ĠĠĠĠ"],
                                   self.vocab_text_int["ĠĠĠĠĠĠĠĠ"]]):
            return_val = self.vocab_text_int["\""]

        elif max_val_ind == self.vocab_text_int["ĉ"]:
            return_val = self.vocab_text_int["ĠĠĠĠ"]

        return (return_val)

    def _container_management(self, container_log: list[str],
                              last_added_token: int) -> list[str]:

        if (last_added_token in [self.vocab_text_int["{"],
                                 self.vocab_text_int["}"],
                                 self.vocab_text_int["}Ċ"],
                                 self.vocab_text_int["["],
                                 self.vocab_text_int["]"],
                                 self.vocab_text_int["]Ċ"],
                                 self.vocab_text_int["\""],
                                 self.vocab_text_int["\"Ċ"],
                                 self.vocab_text_int['ĠĠĠĠ'],
                                 self.vocab_text_int['ĠĠĠĠĠĠĠĠ'],
                                 self.vocab_text_int['Ċ'],
                                 self.vocab_text_int[","],
                                 self.vocab_text_int[":"],
                                 self.vocab_text_int["Ġ{Ċ"],
                                 self.vocab_text_int[")\",Ċ"],
                                 self.vocab_text_int["Ġ}Ċ"],
                                 self.vocab_text_int["\",Ċ"],
                                 self.vocab_text_int["\","],
                                 self.vocab_text_int["Ġ\""],
                                 self.vocab_text_int["\":"]]):

            if (last_added_token in [self.vocab_text_int["\""],
                                     self.vocab_text_int["\"Ċ"],
                                     self.vocab_text_int["\",Ċ"],
                                     self.vocab_text_int["\","],
                                     self.vocab_text_int[")\",Ċ"],
                                     self.vocab_text_int["\":"]]
                    and container_log[-1] == "\""):
                container_log.pop()

            elif last_added_token in [self.vocab_text_int["Ġ{Ċ"],
                                      self.vocab_text_int["{"],
                                      self.vocab_text_int["["],
                                      self.vocab_text_int["\""],
                                      self.vocab_text_int["Ġ\""]]:
                to_add = last_added_token

                if to_add == self.vocab_text_int["Ġ{Ċ"]:
                    to_add = self.vocab_text_int["{"]
                if to_add == self.vocab_text_int["Ġ\""]:
                    to_add = self.vocab_text_int["\""]

                container_log.append(self.vocab_int_text[to_add])

            elif last_added_token in [self.vocab_text_int["}"],
                                      self.vocab_text_int["}Ċ"],
                                      self.vocab_text_int["Ġ}Ċ"],
                                      self.vocab_text_int["]"],
                                      self.vocab_text_int["]Ċ"]]:

                if ((last_added_token in [self.vocab_text_int["}"],
                                          self.vocab_text_int["}Ċ"],
                                          self.vocab_text_int["Ġ}Ċ"]]
                    and container_log[-1] == "{") or
                    (last_added_token in [self.vocab_text_int["]"],
                                          self.vocab_text_int["]Ċ"]]
                        and container_log[-1] == "[")):
                    container_log.pop()

                else:
                    print("ERROR in container generation", container_log[-1],
                          self.vocab_int_text[last_added_token])
                    if (last_added_token == self.vocab_text_int["}"]):
                        return []

        return (container_log)

    def export_to_file(self, file_path: str | None = None) -> None:

        exp_str: str

        if not file_path:
            file_path = self.output_path

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
            with open(file_path, "w") as output_file:
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


# FunctionDef(name='val_args',
#             args=arguments(posonlyargs=[],
#                            args=[arg(arg='args',
#                                      annotation=Subscript(...),
#                                      type_comment=None)],
#                                      vararg=None,
#                                      kwonlyargs=[],
#                                      kw_defaults=[],
#                                      kwarg=None,
#                                      defaults=[]),
#             body=[If(test=Compare(left=Subscript(...),
#                                 ops=[In(...)],
#                                 comparators=[List(...)]),
#                                 body=[Assign(targets=[Name(...)],
#                                 value=ast.Subscript(...),
#                                 type_comment=None)],
#                                 orelse=[ast.Raise(exc=ast.Call(...), cause=None)]),
#             ...,
#             Return(value=Call(func=Name(...),
#                                     args=[], keywords=[keyword(...)]))],
#                                     decorator_list=[],
#                                     returns=Name(id='InputHolder',
#                                                 ctx=Load()),
#                                                 type_comment=None,
#                                                 type_params=[]),
# FunctionDef(name='get_from_json_file',
#             args=arguments(posonlyargs=[],
#                            args=[arg(arg='file_path',
#                                      annotation=Name(...),
#                                      type_comment=None)],
#                                      vararg=None,
#                                      kwonlyargs=[],
#                                      kw_defaults=[],
#                                      kwarg=None,
#                                      defaults=[]),
#             body=[With(items=[withitem(context_expr=Call(...),
#                                        optional_vars=Name(...))],
#                         body=[Assign(targets=[Name(...)],
#                                      value=Call(...), type_comment=None)],
#                         type_comment=None),
#                         Return(value=Name(id='output', ctx=Load(...)))], decorator_list=[], returns=Name(id='Any', ctx=Load()), type_comment=None, type_params=[]),

# FunctionDef(name='create_file', args=arguments(posonlyargs=[], args=[arg(arg='file_name', annotation=Name(...), type_comment=None), arg(arg='force', annotation=Name(...), type_comment=None)], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[Constant(value=False, kind=None)]), body=[Assign(targets=[Name(id='file_path', ctx=Store(...))], value=Call(func=Name(...), args=[Name(...)], keywords=[]), type_comment=None), ..., Return(value=Name(id='file_path', ctx=Load(...)))], decorator_list=[], returns=Name(id='Path', ctx=Load()), type_comment=None, type_params=[]), FunctionDef(name='create_dir', args=arguments(posonlyargs=[], args=[arg(arg='dir_name', annotation=Name(...), type_comment=None), arg(arg='force', annotation=Name(...), type_comment=None)], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[Constant(value=False, kind=None)]), body=[Assign(targets=[Name(id='dir_path', ctx=Store(...))], value=Call(func=Name(...), args=[Name(...)], keywords=[]), type_comment=None), ..., Return(value=Name(id='dir_path', ctx=Load(...)))], decorator_list=[], returns=Name(id='Path', ctx=Load()), type_comment=None, type_params=[]), FunctionDef(name='ft_repr', args=arguments(posonlyargs=[], args=[arg(arg='s', annotation=Name(...), type_comment=None)], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]), body=[AnnAssign(target=Name(id='out', ctx=Store(...)), annotation=Name(id='str', ctx=Load(...)), value=Constant(value='', kind=None), simple=1), ..., Return(value=Name(id='out', ctx=Load(...)))], decorator_list=[], returns=Name(id='str', ctx=Load()), type_comment=None, type_params=[])


# functs: [{'name': 'val_args', 'args': ['args'], 'returns': 'InputHolder', 'docstring': None,
#           'body':
#             'if args[1] in [\'index\', \'search\', \'search_dataset\', \'answer\', \'answer_dataset\', \'evaluate\']:\n    mode = args[1]\nelse:\n    raise ValueError(f"Unknown First Argument: {args[1]}\\nMust be: \'ingest\', \'search\', \'answer\' or \'evaluate\'")\ninputs: dict[str, str] = {\'mode\': mode, \'max_chunk_size\': \'2000\', \'dataset_path\': \'data/datasets/UnansweredQuestions/dataset_docs_public.json\', \'k\': \'10\', \'save_directory\': \'data/output/search_results\', \'student_answer_path\': \'data/output/search_results/dataset_docs_public.json\', \'max_context_length\': \'2000\', \'student_search_results_path\': \'data/output/search_results/dataset_docs_public.json\', \'question\': \'\'}\nfail: bool = False\nnext_ins: None | str = None\nfor arg in args[1:]:\n    if next_ins:\n        inputs[next_ins] = arg\n        next_ins = None\n        continue\n    elif arg is args[2] and inputs[\'mode\'] == \'answer\':\n        inputs[\'question\'] = arg\n    elif arg in [\'--max_chunk_size\', \'--dataset_path\', \'--k\', \'--save_directory\', \'--student_answer_path\', \'--max_context_length\', \'--student_search_results_path\']:\n        next_ins = arg[2:]\n    elif arg.startswith(\'--\'):\n        print(f\'Error: Unknown Parameter: {arg}\')\n        fail = True\n        break\n    else:\n        print(\'Error: Unknown Argument\')\n        fail = True\n        break\nif fail:\n    raise ValueError(\'\\nProgram Stopped\')\nreturn InputHolder(**inputs)'},
#          {'name': 'get_from_json_file', 'args': ['file_path'], 'returns': 'Any', 'docstring': None, 'body': 'with open(file_path) as file_obj:\n    output = json.load(file_obj)\nreturn output'}, {'name': 'create_file', 'args': ['file_name', 'force'], 'returns': 'Path', 'docstring': None, 'body': 'file_path = Path(file_name)\nif file_path.exists():\n    if not force:\n        print(f"File \'{file_name}\' already exists, do you wish to replace it?")\n        answer = input("Y for \'yes\', any for \'no\': ").strip().lower()\n        if answer != \'y\':\n            print(\'Stopping Program\')\n            raise FileExistsError(file_name)\n        print(\'Continuing...\')\n    if file_path.is_file():\n        file_path.unlink()\n    elif file_path.is_dir():\n        if not force:\n            print(f"\'{file_name}\' is a directory are you SURE you wish to replace it?")\n            answer = input("Y for \'yes\', any for \'no\': ").strip().lower()\n            if answer != \'y\':\n                print(\'Stopping Program\')\n                raise IsADirectoryError(file_path)\n        rmtree(file_path)\n    else:\n        raise ValueError(\'Unsupported path type\')\nfile_path.parent.mkdir(parents=True, exist_ok=True)\nwith file_path.open(\'x\'):\n    pass\nreturn file_path'}, {'name': 'create_dir', 'args': ['dir_name', 'force'], 'returns': 'Path', 'docstring': None, 'body': 'dir_path = Path(dir_name)\nif dir_path.exists():\n    if not force:\n        print(f"Directory \'{dir_name}\' already exists, do you wish to replace it?")\n        answer = input("Y for \'yes\', any for \'no\': ").strip().lower()\n        if answer != \'y\':\n            print(\'Stopping Program\')\n            raise FileExistsError(dir_name)\n        print(\'Continuing...\')\n    if dir_path.is_file():\n        if not force:\n            print(f"\'{dir_name}\' is a file are you SURE you wish to replace it?")\n            answer = input("Y for \'yes\', any for \'no\': ").strip().lower()\n            if answer != \'y\':\n                print(\'Stopping Program\')\n                raise FileExistsError(dir_path)\n        dir_path.unlink()\n    elif dir_path.is_dir():\n        if not force:\n            print(f"\'{dir_name}\' is a directory are you SURE you wish to replace it?")\n            answer = input("Y for \'yes\', any for \'no\': ").strip().lower()\n            if answer != \'y\':\n                print(\'Stopping Program\')\n                raise IsADirectoryError(dir_path)\n        rmtree(dir_path)\n    else:\n        raise ValueError(\'Unsupported path type\')\ndir_path.mkdir(parents=True)\nreturn dir_path'}, {'name': 'ft_repr', 'args': ['s'], 'returns': 'str', 'docstring': None, 'body': 'out: str = \'\'\nfor char in s:\n    if char in [\'"\', \'\\\\\']:\n        out += \'\\\\\' + char\n    elif char == \'\\n\':\n        out += \'\\n\'\n    elif char == \'\\t\':\n        out += \'\\t\'\n    elif char == \'\\x00\':\n        out += \'\\x00\'\n    elif char == \'\\x0b\':\n        out += \'\\x0b\'\n    else:\n        out += char\nreturn out'}]


# [{'name': 'val_args', 'args': ['args'], 'returns': 'InputHolder', 'docstring': None, 'body': 'def val_args(args: list[str]) -> InputHolder:\n\n    # argc = len(args)\n\n    if (args[1] in [\'index\',  # Index the repository\n                    \'search\',  # Search for a single query\n                    \'search_dataset\',\n                    # Process multiple questions and output search results\n                    \'answer\',  # Answer a single question with context\n                    \'answer_dataset\',  # Generate answers from search results\n                    \'evaluate\',  # Evaluate search results against ground truth\n                    ]):\n        mode = args[1]\n    else:\n        raise ValueError(f"Unknown First Argument: {args[1]}\\n"\n                         "Must be: \'ingest\', \'search\', \'answer\' or \'evaluate\'")\n\n    inputs: dict[str, str] = {\n        "mode": mode,\n        "max_chunk_size": "2000",\n        "dataset_path": ("data/datasets/UnansweredQuestions/"\n                         "dataset_docs_public.json"),\n        "k": "10",\n        "save_directory": "data/output/search_results",\n        "student_answer_path": ("data/output/search_results/"\n                                "dataset_docs_public.json"),\n        "max_context_length": "2000",\n        "student_search_results_path": ("data/output/search_results/"\n                                        "dataset_docs_public.json"),\n        "question": ""\n    }\n    fail: bool = False\n    next_ins: None | str = None\n\n    for arg in args[1:]:\n\n        if next_ins:\n            inputs[next_ins] = arg\n            next_ins = None\n            continue\n\n        elif arg is args[2] and inputs["mode"] == "answer":\n            inputs["question"] = arg\n\n        elif arg in ["--max_chunk_size", "--dataset_path", "--k",\n                     "--save_directory", "--student_answer_path",\n                     "--max_context_length", "--student_search_results_path"]:\n\n            next_ins = arg[2:]\n\n        elif arg.startswith("--"):\n            print(f"Error: Unknown Parameter: {arg}")\n            fail = True\n            break\n        else:\n            print("Error: Unknown Argument")\n            fail = True\n            break\n\n    if fail:\n        raise ValueError("\\nProgram Stopped")\n\n    return InputHolder(**inputs)'}, {'name': 'get_from_json_file', 'args': ['file_path'], 'returns': 'Any', 'docstring': None, 'body': 'def get_from_json_file(file_path: str) -> Any:\n\n    with open(file_path) as file_obj:\n        output = json.load(file_obj)\n\n    return output'},
#  {'name': 'create_file', 'args': ['file_name', 'force'], 'returns': 'Path', 'docstring': None, 'body': 'def create_file(file_name: str, force: bool = False) -> Path:\n\n    file_path = Path(file_name)\n\n    if file_path.exists():\n        if not force:\n            print(f"File \'{file_name}\' "\n                  "already exists, do you wish to replace it?")\n            answer = input("Y for \'yes\', any for \'no\': ").strip().lower()\n            if answer != "y":\n                print("Stopping Program")\n                raise FileExistsError(file_name)\n            print("Continuing...")\n        if file_path.is_file():\n            file_path.unlink()\n        elif file_path.is_dir():\n            if not force:\n                print(f"\'{file_name}\' "\n                      "is a directory are you SURE you wish to replace it?")\n                answer = input("Y for \'yes\', any for \'no\': ").strip().lower()\n                if answer != "y":\n                    print("Stopping Program")\n                    raise IsADirectoryError(file_path)\n            rmtree(file_path)\n        else:\n            raise ValueError("Unsupported path type")\n\n    file_path.parent.mkdir(parents=True, exist_ok=True)\n    with file_path.open("x"):\n        pass\n\n    return file_path'},
#  {'name': 'create_dir', 'args': ['dir_name', 'force'], 'returns': 'Path', 'docstring': None, 'body': 'def create_dir(dir_name: str, force: bool = False) -> Path:\n\n    dir_path = Path(dir_name)\n\n    if dir_path.exists():\n        if not force:\n            print(f"Directory \'{dir_name}\' "\n                  "already exists, do you wish to replace it?")\n            answer = input("Y for \'yes\', any for \'no\': ").strip().lower()\n            if answer != "y":\n                print("Stopping Program")\n                raise FileExistsError(dir_name)\n            print("Continuing...")\n        if dir_path.is_file():\n            if not force:\n                print(f"\'{dir_name}\' "\n                      "is a file are you SURE you wish to replace it?")\n                answer = input("Y for \'yes\', any for \'no\': ").strip().lower()\n                if answer != "y":\n                    print("Stopping Program")\n                    raise FileExistsError(dir_path)\n            dir_path.unlink()\n        elif dir_path.is_dir():\n            if not force:\n                print(f"\'{dir_name}\' "\n                      "is a directory are you SURE you wish to replace it?")\n                answer = input("Y for \'yes\', any for \'no\': ").strip().lower()\n                if answer != "y":\n                    print("Stopping Program")\n                    raise IsADirectoryError(dir_path)\n            rmtree(dir_path)\n        else:\n            raise ValueError("Unsupported path type")\n    dir_path.mkdir(parents=True)\n\n    return dir_path'},
#  {'name': 'ft_repr', 'args': ['s'], 'returns': 'str', 'docstring': None, 'body': 'def ft_repr(s: str) -> str:\n    out: str = ""\n    for char in s:\n        if char in ["\\"", "\\\\"]:\n            out += "\\\\" + char\n        elif char == "\\n":\n            out += "\\n"\n        elif char == "\\t":\n            out += "\\t"\n        elif char == "\\0":\n            out += "\\0"\n        elif char == "\\v":\n            out += "\\v"\n        else:\n            out += char\n    return out'}]
