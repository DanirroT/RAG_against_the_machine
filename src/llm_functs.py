# import json
# from typing import Any

# parsed_inputs = ["123", "\\123", "\"123"]

# for x in parsed_inputs:
#     print(x)
# print()
# print(parsed_inputs)
# print()

to_export = ["""{
    "prompt": "What is the sum of 2 and 3?",
    "name": "fn_add_numbers",
    "parameters": {
        "a": 2,
        "b": 3
    }
}""",
             """{
    "prompt": "What is the sum of 265 and 345?",
    "name": "fn_add_numbers",
    "parameters": {
        "a": 265,
        "b": 345
    }
}""",
             """{
    "prompt": "Greet shrek",
    "name": "fn_greet",
    "parameters": {
        "name": "shrek"
    }
}""",
             """{
    "prompt": "Greet john",
    "name": "fn_greet",
    "parameters": {
        "name": "john"
    }
}""",
             """{
    "prompt": "Reverse the string 'hello'",
    "name": "fn_reverse_string",
    "parameters": {
        "s": "hello"
    }
}""",
             """{
    "prompt": "Reverse the string 'world'",
    "name": "fn_reverse_string",
    "parameters": {
        "s": "world"
    }
}""",
             """{
    "prompt": "What is the square root of 16?",
    "name": "fn_get_square_root",
    "parameters": {
        "a": 16
    }
}""",
             """{
    "prompt": "Calculate the square root of 144",
    "name": "fn_get_square_root",
    "parameters": {
        "a": 144
    }
}""",
             """{
    "prompt": "Replace all numbers in \"Hello 34 I'm 233 years old\" with NUMBERS",
    "name": "fn_substitute_string_with_regex",
    "parameters": {
        "source_string": "Hello 34 I'm 233 years old",
        "regex": "34|233",
        "replacement": "NUMBERS"
    }
}""",
             """{
    "prompt": "Replace all vowels in 'Programming is fun' with asterisks",
    "name": "fn_substitute_string_with_regex",
    "parameters": {
        "source_string": "Programming is fun",
        "regex": "([aeiouAEIOU])",
        "replacement": "*"
    }
}""",
             """{
    "prompt": "Substitute the word 'cat' with 'dog' in 'The cat sat on the mat with another cat'",
    "name": "fn_substitute_string_with_regex",
    "parameters": {
        "source_string": "The cat sat on the mat with another cat",
        "regex": "cat",
        "replacement": "dog"
    }
}"""
             ]

out_list = []

for out in to_export:
    # print()
    # print()
    # print(out)
    in_list = out.split("\n")
    out_list.append("\n    ".join(in_list))
    # print()out_list
    # print()
    # print(out_list)
out_str = "[\n    " + ",\n    ".join(out_list) + "\n]"

print()
print()
print(out_str)
print()

# raw_prompts = [repr(obj)[1:-1]
#                for obj in parsed_inputs]
# for x in raw_prompts:
#     print(x)
# print()
# print(raw_prompts)
# print()

# file_path = "123_test.txt"

# to_export: str | list[str | dict[str, Any]] | dict[str, Any]

# to_export = """{
#     "prompt": "What is the sum of 2 and 3?",
#     "name": "fn_add_numbers",
#     "parameters": {
#         "a": 2,
#         "b": 3
#     }
# }"""

# to_export = ["""{
#     "prompt": "What is the sum of 2 and 3?",
#     "name": "fn_add_numbers",
#     "parameters": {
#         "a": 2,
#         "b": 3
#     }
# }""", """{
#     "prompt": "What is the sum of 123 and 456?",
#     "name": "fn_add_numbers",
#     "parameters": {
#         "a": 123,
#         "b": 456
#     }
# }"""]

# to_export = {
#     "prompt": "What is the sum of 2 and 3?",
#     "name": "fn_add_numbers",
#     "parameters": {
#         "a": 2,
#         "b": 3
#     }
# }

# out_str: str

# if not file_path:
#     file_path = output_path
# if not _llm:
#     file_path = file_path[:-5] + "TEST" + file_path[-5:]

# if isinstance(to_export, str):
#     out_str = to_export
# elif isinstance(to_export, dict):  # pyright: ignore
#     out_str = json.dumps([to_export], indent=4)
# elif isinstance(to_export, list):  # pyright: ignore
#     if isinstance(to_export[1], str):
#         converted: list[dict[str, Any]] = []
#         for out in to_export:
#             converted.append(json.loads(out))
#         out_str = json.dumps(converted, indent=4)
#     elif isinstance(to_export[1], dict):
#         out_str = json.dumps(to_export, indent=4)

#     else:
#         raise TypeError("'to_export' is an unknown type:\n\n---\n\n"
#                         f"{to_export}\n\n---\n\nType: {type(to_export)}")
# else:
#     raise TypeError("'to_export' is an unknown type:\n\n---\n\n"
#                     f"{to_export}\n\n---\n\nType: {type(to_export)}")

# print(out_str)

# try:
#     with open(file_path, "w") as output_file:
#         # inputs = input_file.read()
#         output_file.write(out_str)
# except FileNotFoundError as e:
#     raise FileNotFoundError(f"Output File \"{file_path}\" "
#                             f"not found {e}")
