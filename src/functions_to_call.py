# from math import sqrt


# def fn_add_numbers(a: int | float, b: int | float) -> int | float:
#     """Add two numbers together and return their sum."""
#     return (a + b)


# def fn_greet(name: str) -> str:
#     """Generate a greeting message for a person by name."""
#     return f"Hello {name}"


# def fn_reverse_string(s: str) -> str:
#     """Reverse a string and return the reversed result."""
#     return s[::-1]


# def fn_get_square_root(a: int | float) -> int | float:
#     """description": "Calculate the square root of a number."""
#     return sqrt(a)


# def fn_substitute_string_with_regex(
#         source_string: str, regex: str, replacement: str) -> str:
#     """Replace all occurrences matching a regex pattern in a string."""
#     return source_string.replace(regex, replacement)

# import time

# print("Starting prompt processing")

# start_time = time.time()

# time.sleep(1)  # Simulate some processing time

# print(f"Prompt finished at {time.time() - start_time:.2f} seconds")

# print("Ending prompt processing")

# import json


# with open((
#     "/home/dmota-ri/.cache/huggingface/hub/"
#     "models--Qwen--Qwen3-0.6B/snapshots/"
#         "c1899de289a04d12100db370d81485cdf75e47ca/vocab.json")) as vocab_file:
#     vocab_text_int = json.load(vocab_file)

# vocab_text_int["\\\\"]


out_str = "This is a test string with a backslash: \\\\ and a quote: \" and a lonely \\ "

print(out_str)

str_copy: str = "" + out_str

out_str: str = ""

for i, char in enumerate(str_copy):
    if char == "\\":
        if i == 0:
            out_str += "\\\\"
        elif str_copy[i - 1] == "\\":
            out_str += char
        elif i + 1 >= len(str_copy):
            out_str += "\\\\"
        elif str_copy[i + 1] not in "\\\"":
            out_str += "\\\\"
        else:
            out_str += char
    else:
        out_str += char

print(out_str)
