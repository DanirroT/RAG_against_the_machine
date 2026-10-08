from __future__ import annotations
from pathlib import Path
# import json
from typing import Any, TYPE_CHECKING
from src import (InputHolder, ChunkScorePair, Chunk,
                 get_from_json_file,
                 UnansweredQuestion, AnsweredQuestion)
from math import log, e, sqrt
from tqdm import tqdm
import json

if TYPE_CHECKING:
    from .llm_sdk import Small_LLM_Model


class StrAnswer():

    database: list[ChunkScorePair]
    k_database: list[ChunkScorePair]
    arg_inputs: InputHolder

    _llm: Small_LLM_Model
    llm_files: dict[str, Path]

    vocab_text_int: dict[str, int]
    vocab_int_text: dict[int, str]

    def __init__(self, ingest_database_path: Path, output_file_path: Path,
                 arg_inputs: InputHolder, to_print: bool = True) -> None:

        self.arg_inputs = arg_inputs

        self.output_file_path = output_file_path
        self.database = self._load_ingest_files(ingest_database_path)

        self.gen_k_database()

        # print(f"\nTop {self.arg_inputs.k} results for query: "
        #       f"'{self.arg_inputs.question}'\n")
        # print("\n".join(f"Chunk ID: {chunk.chunk.id}, Score: {chunk.score}"
        #                 for chunk in self.k_database))
        # print()

        self.gen_answer()

        if to_print:
            self.print()

    def _load_ingest_files(self, ingest_database_path: Path
                           ) -> list[ChunkScorePair]:

        database_ingest_out: list[ChunkScorePair] = []

        files: list[Path] | tqdm[Path] = list(ingest_database_path.rglob("*"))

        if len(files) > 50:
            files = tqdm(files)

        print("\nLoading Ingested Database from:", ingest_database_path)
        for path in files:
            # print()
            # print(path)
            new_file: list[dict[str, Any]] = (
                get_from_json_file(path))
            add_chunks: list[ChunkScorePair] = []
            for chunk in new_file:
                # print()
                # print(chunk)
                # print()
                id: str = chunk["id"]
                chunk_path: str = chunk["path"]
                type: str = chunk["type"]
                parent: str = chunk["parent"]
                start_char: int = chunk["start_char"]
                end_char: int = chunk["end_char"]
                content: str = chunk["content"]
                vector: list[int] = chunk["vector"]
                add_chunks.append(ChunkScorePair(id=id, chunk=Chunk(
                    id=id, path=chunk_path, type=type, parent=parent,
                    start_char=start_char, end_char=end_char,
                    content=content, content_vector=vector), score=0))
                # print()
                # print(add_chunks[-1])
                # print()

            database_ingest_out += add_chunks

        print()

        return database_ingest_out

    def gen_k_database(self, question: str | None = None) -> None:

        if question is None:
            if self.arg_inputs.question is None:  # pyright: ignore
                raise ValueError("no question has been "
                                 "passed by arg_inputs.")
            question = self.arg_inputs.question

        # print()
        # print(question)
        # print()

        database_len = len(self.database)
        if not database_len:
            print("No database found. Please run the 'index' mode first.")
            return
        avg_chunk_len = (sum(len(chunk.chunk.content)
                             for chunk in self.database) / database_len)
        bm25_k1 = 1.4
        bm25_b = 0.75
        title_weight = 3.0

        complex_query = self.complex_split(question)

        # for chunk in self.database:
        #     print(chunk.chunk.id.replace(".", " ").lower(),
        #           chunk.chunk.content.lower(), sep="\n---\n")

        # input()

        values: list[set[str]] | tqdm[set[str]] = list(complex_query.values())

        if len(values) > 1000:
            values = tqdm(values)

        print("\nGathering Chunks for:", question, "\n")
        for variants in values:

            chunks_containing_q = sum(
                1 for chunk in self.database
                if any(
                    variant in chunk.chunk.content.lower()
                    for variant in variants
                )
            )

            idf_result = log(
                1 + ((database_len - chunks_containing_q + 0.5) /
                     (chunks_containing_q + 0.5)), e)

            for chunk in self.database:

                word_frequency = max(
                    chunk.chunk.content.lower().count(variant)
                    for variant in variants
                )

                bm25_component = (
                    (idf_result * ((bm25_k1 + 1) * word_frequency)) /
                    (bm25_k1 * (1 - bm25_b + (bm25_b * (
                        len(chunk.chunk.content) / avg_chunk_len)))
                        + word_frequency))

                title_score_list = [0]

                for id_variants in (self.complex_split(
                        chunk.chunk.id).values()):
                    title_score_list.append(
                        sum(1 for q_var in variants
                            if q_var in id_variants)
                    )

                title_score = max(title_score_list) * title_weight

                chunk.score += title_score + bm25_component

        # for chunk in self.database:
        #     print(f"Chunk ID: {chunk.chunk.id}, Score: {chunk.score}")

        self.database.sort(key=lambda x: x.score, reverse=True)

        most_relevant = self.database[:int(sqrt(self.arg_inputs.k))+1]

        most_relevants_path_weights: dict[str, float] = {}

        for checking in most_relevant:
            i = 0
            for chunk in self.database:
                if chunk.chunk.path == checking.chunk.path:
                    i += 1
            most_relevants_path_weights[checking.chunk.path] = (
                1 + (1 / (i + 1)))

        for chunk in self.database:
            for checking in most_relevant:
                if chunk == checking:
                    continue
                if chunk.chunk.path == checking.chunk.path:
                    chunk.score *= most_relevants_path_weights[
                        checking.chunk.path]
                if (checking.chunk.parent and
                        checking.chunk.parent in chunk.chunk.id):
                    chunk.score *= 1.3

        self.k_database = self.database[:self.arg_inputs.k]

        min_relevance_score = (max(chunk.score for chunk in self.k_database)
                               * 0.01)
        self.k_database = [c for c in self.k_database
                           if c.score > min_relevance_score]

        self.k_database.sort(key=lambda x: x.score, reverse=True)

    def complex_split(self, text: str) -> dict[str, set[str]]:

        split_text: dict[str, set[str]] = {}

        for w in text.lower().split():
            split_text[w] = {w}
            if "." in w and "_" in w:
                split_text[w].update(w.replace(".", "_").split("_"))
                split_text[w].update(w.replace("_", ".").split("."))
            if "_" in w:
                split_text[w].update(w.split("_"))
            if "." in w:
                split_text[w].update(w.split("."))
            split_text[w].difference_update(
                {"", "the", "a", "an", "of", "to", "in", "on", "for"})

            if not split_text[w]:
                del split_text[w]

        return split_text

    def gen_answer(self) -> None:

        self._load_llm()

        # input("\aLLM Loaded. Press Enter to Continue...")

        chunk_context = self._llm.encode("Context to answer:\n")

        context_separator = self._llm.encode("\n\n")

        context_prompt_separator = self._llm.encode(
            "According to the context, Answer the following question:\n")

        self.instructions = chunk_context

        for chunk in self.k_database:
            self.instructions += chunk.chunk.content_vector
            self.instructions += context_separator

        self.instructions += context_prompt_separator

        self.instructions += self._llm.encode(self.arg_inputs.question
                                              + "\n\n")

        instructions_len = len(self.instructions)

        print(f"\aInstructions:\n\n{self._llm.decode(self.instructions)}\")
        print(f"\nInstructions Length: {instructions_len}\n")

        added_tokens = self.instructions

        answer_str = ""

        while True:

            logit_results = self._llm.get_logits_from_input_ids(added_tokens)

            added_tokens.append(logit_results.index(max(logit_results)))

            answer_str += self._llm.decode([added_tokens[-1]])

            print(f"\nCurrent Answer:\n{repr(answer_str)}\n")

            if len(added_tokens) - instructions_len > 100:
                # Stop if the answer is too long
                self.final_answer = (answer_str +
                                     "... [Answer truncated due to length]")
                break

            if ".\n" in answer_str:
                end_str = answer_str.find(".\n") + 1
                self.final_answer = answer_str[:end_str]
                break

        print(f"\nFinal Answer:\n{repr(self.final_answer)}\n")

    def print(self, question: str | None = None) -> None:

        if question is None:
            if self.arg_inputs.question is None:  # pyright: ignore
                raise ValueError("no question has been "
                                 "passed by arg_inputs.")
            question = self.arg_inputs.question

        # json.dump([chunk.chunk.__dict__
        #            for chunk in self.k_database],
        #           search_file, indent=4)
        # for chunk in self.k_database:
        #     to_print = (f"{chunk.chunk.path} "
        #                 f"[{chunk.chunk.start_char}:"
        #                 f"{chunk.chunk.end_char}]")
        #     search_file.write(to_print + f"\tID: {chunk.chunk.id} - "
        #                       f"Score: {chunk.score}\n")
        #     print(to_print)
        retrieved_sources: list[dict[str, str | int]] = []
        for chunk in self.k_database:
            retrieved_sources.append({
                "file_path": chunk.chunk.path,
                "first_character_index": chunk.chunk.start_char,
                "last_character_index": chunk.chunk.end_char

            })

        print(f"The Answer to '{question}' is:")
        print(self.final_answer)
        print()

        try:

            with ((self.output_file_path).open("w") as search_file):
                json.dump({
                    "search_results": [
                        {
                            "question_id": (
                                f"Q{hash(question)}"),
                            "question": question,
                            "retrieved_sources": retrieved_sources,
                            "answer": self.final_answer
                        }
                    ],
                    "k": self.arg_inputs.k
                }, search_file, indent=4)

        except FileNotFoundError:
            print(f"Output file '{self.output_file_path}' not found. "
                  "Please create the file and try again.")

    def _load_llm(self) -> None:

        from .llm_sdk import Small_LLM_Model
        self._llm = Small_LLM_Model(device="cpu")

        self.llm_files = self._llm.get_path_to_model_files()

        with self.llm_files["vocab"].open() as vocab_file:
            self.vocab_text_int: dict[str, int] = json.load(vocab_file)

        self.vocab_int_text = {}

        for k, v in self.vocab_text_int.items():
            self.vocab_int_text[v] = k


class FileAnswer():

    arg_inputs: InputHolder

    all_questions: list[UnansweredQuestion]
    database: list[ChunkScorePair]
    k_database_list: list[AnsweredQuestion]
    output_file_path: Path

    vocab_text_int: dict[str, int]
    vocab_int_text: dict[int, str]
    questions_list: list[UnansweredQuestion]

    def get_all_questions(self, questions_file: Path) -> None:
        self.all_questions = []

        all_questions_json: list[dict[str, str]] = (
            get_from_json_file(questions_file)["rag_questions"]
        )

        for q in all_questions_json:
            self.all_questions.append(UnansweredQuestion(
                question=q["question"],
                question_id=q["id"]
            ))

    def print(self) -> None:

        return_list: list[dict[str, str | list[dict[str, str | int]]]] = []
        for search_result in self.k_database_list:

            return_list.append({
                "question_id": search_result.question_id,
                "question": search_result.question,
                "retrieved_sources": list(map(lambda x: x.to_simple_dict(),
                                              search_result.sources)),
                "answer": search_result.answer
            })

        try:

            with ((self.output_file_path).open("w") as search_file):
                json.dump({
                    "search_results": return_list,
                    "k": self.arg_inputs.k
                }, search_file, indent=4)

        except FileNotFoundError:
            print(f"Output file '{self.output_file_path}' not found. "
                  "Please create the file and try again.")
