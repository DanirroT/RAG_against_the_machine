import sys
import os
# from dotenv import load_dotenv
from tqdm import tqdm
from pathlib import Path
from shutil import rmtree
import httpcore
from typing import Any, cast
import json
import ast
from markdown_it import MarkdownIt
from src import (get_from_json_file, create_file, create_dir, ft_repr,
                 InputHolder
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
            else:
                output_dir_path.mkdir(parents=True)

            self._ingest(input_dir_path, output_dir_path)
            print(f"Ingestion complete! Indices saved under {output_dir_str}")
            return

        elif arg_inputs.mode == "answer":
            output_dir_str = ""
            self._str_answer(input_dir_path, output_dir_path)

        elif arg_inputs.mode == "answer_dataset":
            output_dir_str = ""
            self._file_answer(input_dir_path, output_dir_path)

        elif arg_inputs.mode == "search":
            output_dir_str = ""
            self._str_search(input_dir_path, output_dir_path)

        elif arg_inputs.mode == "search_dataset":
            output_dir_str = ""
            self._file_search(input_dir_path, output_dir_path)

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

        ingest_out: dict[str, dict[str, str | list[Any]]] = {}

        print("\n\n")
        for path in input_dir_path.rglob("*"):
            print(path)
            if path.is_dir():
                continue
            if path.is_file():
                with path.open("r") as file:
                    file_str = file.read()
                if str(path).endswith(".py"):
                    file_out_lists: dict[str, str | list[Any]] = {"type": "Python",
                                                                  "name": str(path),
                                                                  "imports": [],
                                                                  "functs": [],
                                                                  "classes": []}
                    parsed = ast.parse(file_str)
                    print(ast.dump(parsed, indent=4), end="\n\n\n")
                    for item in parsed.body:
                        print(item)
                        if isinstance(item, ast.Import):
                            file_out_lists["imports"].append(item.names[0].name)
                        if isinstance(item, ast.FunctionDef):
                            file_out_lists["functs"].append({"name": item.name,
                                                             "args": [arg.arg for arg in item.args.args],
                                                             "returns": ast.unparse(item.returns) if item.returns else None,
                                                             "docstring": ast.get_docstring(item),
                                                             "body": item.body})
                        if isinstance(item, ast.ClassDef):
                            file_out_lists["classes"].append({"name": item.name,
                                                              "docstring": ast.get_docstring(item),
                                                              "body": ast.unparse(item.body)})

                elif str(path).endswith(".md"):
                    file_out_lists = {"Type": "MarkDown", "name": str(path),
                                      "Introduction": [], "Sections": []}
                    print(md_parse.parse(file_str))
                else:
                    file_out_lists = {"Type": "Other", "name": str(path),
                                      "Sections": []}
                    print(file_str)
            print("\n\n")
            ingest_out[str(path)] = file_out_lists

        print("\n\n".join(k + ":\n" + "\n".join(f"  {k1}: {v2}" for k1, v2 in v.items()) for k, v in ingest_out.items()))

        print("output:", output_dir_path)

    def _load_llm(self, mode: bool = True) -> None:

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


functs: [{'name': 'val_args', 'args': ['args'], 'returns': 'InputHolder', 'docstring': None,
          'body':
            'if args[1] in [\'index\', \'search\', \'search_dataset\', \'answer\', \'answer_dataset\', \'evaluate\']:\n    mode = args[1]\nelse:\n    raise ValueError(f"Unknown First Argument: {args[1]}\\nMust be: \'ingest\', \'search\', \'answer\' or \'evaluate\'")\ninputs: dict[str, str] = {\'mode\': mode, \'max_chunk_size\': \'2000\', \'dataset_path\': \'data/datasets/UnansweredQuestions/dataset_docs_public.json\', \'k\': \'10\', \'save_directory\': \'data/output/search_results\', \'student_answer_path\': \'data/output/search_results/dataset_docs_public.json\', \'max_context_length\': \'2000\', \'student_search_results_path\': \'data/output/search_results/dataset_docs_public.json\', \'question\': \'\'}\nfail: bool = False\nnext_ins: None | str = None\nfor arg in args[1:]:\n    if next_ins:\n        inputs[next_ins] = arg\n        next_ins = None\n        continue\n    elif arg is args[2] and inputs[\'mode\'] == \'answer\':\n        inputs[\'question\'] = arg\n    elif arg in [\'--max_chunk_size\', \'--dataset_path\', \'--k\', \'--save_directory\', \'--student_answer_path\', \'--max_context_length\', \'--student_search_results_path\']:\n        next_ins = arg[2:]\n    elif arg.startswith(\'--\'):\n        print(f\'Error: Unknown Parameter: {arg}\')\n        fail = True\n        break\n    else:\n        print(\'Error: Unknown Argument\')\n        fail = True\n        break\nif fail:\n    raise ValueError(\'\\nProgram Stopped\')\nreturn InputHolder(**inputs)'},
         {'name': 'get_from_json_file', 'args': ['file_path'], 'returns': 'Any', 'docstring': None, 'body': 'with open(file_path) as file_obj:\n    output = json.load(file_obj)\nreturn output'}, {'name': 'create_file', 'args': ['file_name', 'force'], 'returns': 'Path', 'docstring': None, 'body': 'file_path = Path(file_name)\nif file_path.exists():\n    if not force:\n        print(f"File \'{file_name}\' already exists, do you wish to replace it?")\n        answer = input("Y for \'yes\', any for \'no\': ").strip().lower()\n        if answer != \'y\':\n            print(\'Stopping Program\')\n            raise FileExistsError(file_name)\n        print(\'Continuing...\')\n    if file_path.is_file():\n        file_path.unlink()\n    elif file_path.is_dir():\n        if not force:\n            print(f"\'{file_name}\' is a directory are you SURE you wish to replace it?")\n            answer = input("Y for \'yes\', any for \'no\': ").strip().lower()\n            if answer != \'y\':\n                print(\'Stopping Program\')\n                raise IsADirectoryError(file_path)\n        rmtree(file_path)\n    else:\n        raise ValueError(\'Unsupported path type\')\nfile_path.parent.mkdir(parents=True, exist_ok=True)\nwith file_path.open(\'x\'):\n    pass\nreturn file_path'}, {'name': 'create_dir', 'args': ['dir_name', 'force'], 'returns': 'Path', 'docstring': None, 'body': 'dir_path = Path(dir_name)\nif dir_path.exists():\n    if not force:\n        print(f"Directory \'{dir_name}\' already exists, do you wish to replace it?")\n        answer = input("Y for \'yes\', any for \'no\': ").strip().lower()\n        if answer != \'y\':\n            print(\'Stopping Program\')\n            raise FileExistsError(dir_name)\n        print(\'Continuing...\')\n    if dir_path.is_file():\n        if not force:\n            print(f"\'{dir_name}\' is a file are you SURE you wish to replace it?")\n            answer = input("Y for \'yes\', any for \'no\': ").strip().lower()\n            if answer != \'y\':\n                print(\'Stopping Program\')\n                raise FileExistsError(dir_path)\n        dir_path.unlink()\n    elif dir_path.is_dir():\n        if not force:\n            print(f"\'{dir_name}\' is a directory are you SURE you wish to replace it?")\n            answer = input("Y for \'yes\', any for \'no\': ").strip().lower()\n            if answer != \'y\':\n                print(\'Stopping Program\')\n                raise IsADirectoryError(dir_path)\n        rmtree(dir_path)\n    else:\n        raise ValueError(\'Unsupported path type\')\ndir_path.mkdir(parents=True)\nreturn dir_path'}, {'name': 'ft_repr', 'args': ['s'], 'returns': 'str', 'docstring': None, 'body': 'out: str = \'\'\nfor char in s:\n    if char in [\'"\', \'\\\\\']:\n        out += \'\\\\\' + char\n    elif char == \'\\n\':\n        out += \'\\n\'\n    elif char == \'\\t\':\n        out += \'\\t\'\n    elif char == \'\\x00\':\n        out += \'\\x00\'\n    elif char == \'\\x0b\':\n        out += \'\\x0b\'\n    else:\n        out += char\nreturn out'}]
