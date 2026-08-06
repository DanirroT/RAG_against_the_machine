_This project has been created as part of the 42 curriculum by dmota-ri._

# Description

CallMeMaybe is designed to teach students how to perform function calling with Small Language Models (LLMs) using Python.

The goal is to create an algorithm that uses the provided `Small_LLM_Model` class, a wrapper around the `Qwen/Qwen3-0.6B` Small Language Model, to generate structured Function Calling dictionaries from natural language prompts.

The model takes in two input files:

- `input` (default: data/input/function_calling_tests.json)
  - list of Prompt Dictionaries
  - Structure:
    ```json
    [
      {
        "prompt": "prompt1"
      },
      {
        "prompt": "prompt2"
      },
      <...>
    ]
    ```

- `functions_definition` (default: data/input/functions_definition.json)
  - list of Functions Dictionaries
  - Defines the functions available to the model, together with their descriptions, parameters, and return types.
  - Structure:
    ```json
    [
      {
          "name": "fn_name1",
          "description": "description_str",
          "parameters": {
            "param1": {
              "type": param1_type
            },
            "param2": {
              "type": param1_type
            },
            <...>
          },
          "return": {
            "type": return_type
          }
      },
      {
          "name": "fn_name2",
          "description": "description_str",
          "parameters": {
            "param1": {
              "type": param1_type
            },
            "param2": {
              "type": param1_type
            },
            <...>
          },
          "return": {
            "type": return_type
          }
      },
      <...>
    ]
    ```

After loading and preprocessing both input files, each prompt is, independently, tokenized and processed by the LLM, producing exactly one Function Calling Dictionary. The generated responses are then written to an output file.

- `output` (default: data/output/function_calls.json)
  - list of Function Calling Dictionaries
  - Contains the original prompt, the selected function, and the extracted arguments for that function.
  - Structure:
    ```json
    [
      {
          "prompt": "given prompt1",
          "name": "fn_name1",
          "parameters": {
              "param1": param1_val,
              "param2": param2_val
              <...>
          }
      },
      {
          "prompt": "given prompt2",
          "name": "fn_name2",
          "parameters": {
              "param1": param1_val,
              "param2": param2_val
              <...>
          }
      },
      <...>
    ]
    ```

## Model Inner Workings - Algorithm Explanation

This section describes the complete processing pipeline, from loading the input files to generating the final Function Calling dictionaries.

### Arguments and Input Parsing

The first stage of the program is to parse and validate the console arguments. These determine the input files containing the prompts and function definitions, as well as the location of the output file.

Before the model is initialized, every file is validated:
- Input files must exist and be readable.
- If the output path contains directories, they are created automatically when necessary.
- If the output file already exists, the user is asked for confirmation before it is overwritten.

Once the files have been validated, both JSON documents are loaded and converted into Python data structures. The prompt file is stored as a `list[str]`, while the function definitions are converted into a list of custom `FunctDef` objects that provide a more convenient interface than repeatedly accessing raw dictionaries.

If any validation or parsing step fails, the program terminates immediately with an informative error message describing the problem and, when appropriate, how to resolve it.

#### Design decision:
- All validation is performed using the json package to read input files and the pydantic library to validate all inputs before converting them into my custom classes.
- This process happens before the `Small_LLM_Model` is initialized. Loading the language model is the most time-consuming part of the program startup, so detecting invalid arguments or malformed input files early avoids unnecessary initialization and significantly reduces the time spent on failed executions.

### Prompt construction and Tokenization

After the input files have been parsed, the `Small_LLM_Model` is initialized together with a set of helper objects, most notably the vocabularies used to translate between text tokens and token IDs.

Before processing any user prompt, the program constructs a common instruction prefix shared by every generation. This prefix contains a compact description of every available function, including its name, description, parameters, and return type.
```json
JSON Function:
{"name":"fn_name1","description":"description_str","parameters":{"param1":{"type":param1_type},"param2":{"type":param2_type},<...>},"return":{"type":return_type}}
JSON Function:
{"name":"fn_name1","description":"description_str","parameters":{"param1":{"type":param1_type},"param2":{"type":param2_type},<...>},"return":{"type":return_type}}
JSON Function:
<...>
```
After all available functions have been listed, the desired output format is appended to the instruction prefix.
```json
JSON Format:
{
    "prompt": "given prompt",
    "name": "fn_name",
    "parameters": {
        "param1": param1_val,
        "param2": param2_val
        <...>
    }
}

```

Providing the expected JSON structure encourages the model to continue in the demonstrated format, significantly improving the consistency of the generated output.

Finally, the current prompt is appended to the shared instruction prefix using the following partial JSON object:

```json
{
    "prompt": "prompt1",
    "name": "
```

This effectively turns generation into a constrained continuation of the required JSON structure rather than asking the model to create the complete object from scratch. The complete prompt is then tokenized, converted into token IDs, and passed to the language model for inference.

#### Design decision
- The description of every available function is assembled only once into a common instruction prefix and reused for every prompt. This avoids repeatedly rebuilding identical instructions while ensuring every inference receives exactly the same context.
- Function definitions are serialized as compact JSON without unnecessary whitespace. Since language models operate on tokens rather than characters, reducing formatting overhead leaves more of the context window available for meaningful information.
- Instead of asking the model to generate an entire JSON object from scratch, generation begins immediately after the `"name"` key. This constrains the first prediction to selecting a function name and naturally guides the remainder of the generation toward the required output format.


### Response Generation

Once the prompt has been converted into token IDs, it is passed to the `Small_LLM_Model` for *autoregressive generation*.

At each iteration, the model evaluates the current sequence and produces a list of logits, one score for every token in the vocabulary. The token with the highest logit is selected as the next output token. Before being appended to the generated sequence, the token is checked against a small set of common formatting mistakes observed during development. When necessary, it is replaced with the corrected token. The updated sequence is then fed back into the model, repeating the process one token at a time.

Generation continues until a complete Function Calling dictionary has been produced. Rather than relying on a fixed number of generated tokens, the program tracks the opening and closing of JSON containers. Since generation always begins with the opening `{` and the initial `"` already provided in the prompt, the response is considered complete once every opened container has been properly closed.

As a fail-safe, generation is also limited to a maximum of 120 tokens. If this limit is reached before the JSON object has been closed, the remaining closing braces are generated manually, ensuring that the output remains syntactically valid JSON even in cases where generation reaches the token limit.

#### Design Decisions

- The implementation always selects the token with the highest logit instead of sampling from the distribution (Greedy decoding). Since the objective is to produce deterministic Function Calling dictionaries rather than creative text, greedy decoding provides consistent and repeatable results.
- A lightweight post-processing step corrects a small set of recurring formatting mistakes before each token is appended to the generated sequence. Although the model generally produces the expected structure, these corrections improve formatting consistency and reduce malformed JSON output without affecting the generated content.

### Finalization and Outputs

After all prompts have been processed, the generated token sequences are decoded back into UTF-8 strings.

Each decoded response is combined into a single list of Function Calling dictionaries, which is then serialized as formatted JSON and written to the output file selected during argument parsing.

At this point, all requested prompts have been processed, and the program exits normally.


After the LLM has run it's corse, all the responses are decoded back into strings and then joined into the final content of the output file.

### Performance Analysis

The implementation prioritizes deterministic and reliable generation over raw throughput.

Since greedy decoding is used, every prompt always produces the same output for the same inputs, making the program easy to debug and evaluate.

The largest performance cost is loading the language model into memory. For this reason, all command-line arguments and input files are validated before model initialization, avoiding expensive startup when execution would fail due to invalid inputs.

During generation, function definitions are assembled into a single reusable instruction prefix and reused for every prompt, avoiding unnecessary reconstruction of identical prompt content.


## Challenges Faced

Although the provided language model is straightforward to use, producing reliable results still required solving several practical problems.

### Prompt construction

The model requires enough information to understand the available functions while keeping the prompt compact enough to avoid wasting context.

To address this, all function definitions are serialized into a compact JSON representation that is generated once and reused for every prompt, reducing unnecessary prompt size while keeping the information available to the model.

### Deterministic function selection

Unlike conversational applications, function calling benefits from predictable outputs.

For this reason, greedy decoding was chosen over probabilistic sampling, ensuring identical inputs always produce identical outputs.

### Producing valid JSON

Large language models, especially smaller ones such as the one used, do not always generate syntactically correct JSON reliably. During development, occasional formatting inconsistencies, unfinished objects, and misplaced whitespace were observed.

To improve reliability, the implementation combines prompt engineering, token correction, bracket tracking and a maximum generation length with automatic JSON closure. Together, these measures greatly improve the reliability of the generated JSON output.

# Instructions

The project is managed through the provided Makefile, which offers the following rules:
- install: Creates the project's `Python Virtual Environment` (if it does not already exist) and installs all required dependencies using `uv sync`.
- run: Execute the main script of the project.
  - If you wish to include non-default input or output files, you must add them like so:
    ```bash
    make run [--functions_definition <function_definition_file>] [--input <input_file>] [--output <output_file>]
    ```
- run_time: Behaves identically to `run`, but also displays the total execution time measured using Bash's `time` command after execution in the format: `Total Run Time: <run_time>`
- debug: Run the main script in debug mode using Python’s built-in debugger using pdb.
- clean: Removes temporary files and caches to keep the project environment clean.
- lint: Executes the commands `flake8 .` and `mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs` to check for formatting and type hint errors
- lint-strict: Executes the commands `flake8 .` and `mypy . --strict` to check for formatting and type hint errors more strictly

In the case that the Output file already exists, the following message will appear:
  ```
  File "<output_file>" already exists. Do you wish to replace it?
  Y for 'yes', any for 'no':
  ```
Use 'y' to continue, or any other input to abort

# Resources

Most of the core concepts I learned from previous projects and through pure experimentation with the tokens and vocabularies.

For further explanation of specific aspects of internal small inconsistencies or new errors I was not familiar with, I sometimes checked in with AI, with mixed results. I also used it as a tool to sift through particularly lengthy outputs and check for any inconsistencies I might have missed.

## Sources:
https://huggingface.co/
https://www.geeksforgeeks.org/python/tensors-in-pytorch/
