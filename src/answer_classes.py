from __future__ import annotations
from pathlib import Path
# import json
from typing import Any, TYPE_CHECKING
from src import (InputHolder, ChunkScorePair, Chunk,
                 get_from_json_file,
                 UnansweredQuestion, MinimalSource,
                 MinimalAnswer, StudentSearchResults,
                 StudentSearchResultsAndAnswer)
from math import log, e, sqrt
from tqdm import tqdm
import json

if TYPE_CHECKING:
    from .llm_sdk import Small_LLM_Model


class StrAnswer():

    database: list[ChunkScorePair]
    k_database: list[Chunk]
    arg_inputs: InputHolder

    _llm: Small_LLM_Model
    llm_files: dict[str, Path]

    vocab_text_int: dict[str, int]
    vocab_int_text: dict[int, str]

    def __init__(self, ingest_database_path: Path, output_file_path: Path,
                 arg_inputs: InputHolder, to_print: bool = True) -> None:

        self.arg_inputs = arg_inputs

        self.output_file_path = output_file_path

        self.gen_k_database(ingest_database_path)

        # print(f"\nTop {self.arg_inputs.k} results for query: "
        #       f"'{self.arg_inputs.question}'\n")
        # print("\n".join(f"Chunk ID: {chunk.id}, Score: {chunk.score}"
        #                 for chunk in self.k_database))
        # print()

        self.gen_answer()

        if to_print:
            self.print()

    def _load_ingest_files(self, ingest_database_path: Path
                           ) -> list[ChunkScorePair]:

        database_ingest_out: list[ChunkScorePair] = []

        files: list[Path] | tqdm[Path] = list(ingest_database_path.rglob("*"))

        print("\nLoading Ingested Database from:", ingest_database_path)
        if len(files) > 5000:
            files = tqdm(files)

        for path in files:
            # print()
            # print(path)
            if path.is_dir():
                # print("skip", flush=True)
                continue
            elif path.is_file():
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
            else:
                continue

            database_ingest_out += add_chunks

        print()

        return database_ingest_out

    def search_cache(self, question: str,
                     chunk_lookup: dict[tuple[str, int, int], Chunk]
                     ) -> list[Chunk]:
        try:
            cache = StudentSearchResults(**get_from_json_file(
                self.arg_inputs.student_search_results_path))
        except FileNotFoundError:
            return []

        if not (cache.k == self.arg_inputs.k and
                cache.search_results[0].question == question):
            return []

        minimal_sources = cache.search_results[0].retrieved_sources

        k_database: list[Chunk | None] = [
            chunk_lookup.get((
                source.path,
                source.start_char,
                source.end_char
            )) for source in minimal_sources]

        if None in k_database:
            return []

        return [chunk for chunk in k_database if chunk is not None]

    def gen_k_database(self, ingest_database_path: Path,
                       question: str | None = None) -> None:

        if question is None:
            if self.arg_inputs.question is None:  # pyright: ignore
                raise ValueError("no question has been "
                                 "passed by arg_inputs.")
            question = self.arg_inputs.question

        self.database = self._load_ingest_files(ingest_database_path)

        chunk_lookup = {
            (chunk.chunk.path,
             chunk.chunk.start_char,
             chunk.chunk.end_char): chunk.chunk
            for chunk in self.database
        }

        self.k_database = self.search_cache(question, chunk_lookup)

        if self.k_database:
            return

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

        print("\nGathering Chunks for:", question, "\n")
        if len(values) > 1000:
            values = tqdm(values)

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

        k_database = self.database[:self.arg_inputs.k]

        min_relevance_score = (max(chunk.score for chunk in k_database)
                               * 0.01)
        k_database = [c for c in k_database
                      if c.score > min_relevance_score]

        self.k_database = [c.chunk for c in sorted(
            k_database, key=lambda x: x.score, reverse=True)]

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

        chunk_context = self._llm.encode(
            "You are a question-answering assistant. "
            "Answer the user's question using only the provided context."
            "\nRelevant context to answer:\n")

        context_separator = self._llm.encode("\n\n")

        context_prompt_separator = self._llm.encode(
            "Extra instruction:\n"
            "- Write the answer as plain, natural-language prose.\n"
            "- Do not use square brackets, lists, or placeholders."
            "- When asked for multiple items, name the actual items separated"
            " by commas, using 'and' before the final item."
            "- Never describe what the answer should contain,"
            " provide the actual answer."
            "- The answer should be short and concise. "
            "Do not repeat or rephrase the question.\n"
            "- Terminate your answer with a '.\\n'.\n\n"
            "According to the context above, Answer the following question:\n")

        post_question_prompt = self._llm.encode(
            "\n\nFinal Answer: "
        )

        self.instructions = chunk_context

        for chunk in self.k_database:
            self.instructions += chunk.content_vector
            self.instructions += context_separator

        self.instructions += context_prompt_separator

        self.instructions += (self._llm.encode(
            self.arg_inputs.question) + post_question_prompt)

        instructions_len = len(self.instructions)

        print(f"\aInstructions:\n\n{self._llm.decode(self.instructions)}")
        print(f"\n\nInstructions Length: {instructions_len}\n")

        added_tokens = self.instructions

        answer_str = ""

        while True:

            logit_results = self._llm.get_logits_from_input_ids(added_tokens)

            # logit_results[25] -= 2  # ':'
            logit_results[2509] -= 3  # " ['"
            logit_results[508] -= 3  # ' ['
            logit_results[364] -= 3  # " '"

            added_tokens.append(logit_results.index(max(logit_results)))

            answer_str += self._llm.decode([added_tokens[-1]])

            print(f"\nCurrent Answer:\n{repr(answer_str)}\n")

            for i in range(5):
                max_ = max(logit_results)
                index_ = logit_results.index(max_)
                print(f"Logit n{i+1}: {index_:6} -> "
                      f"{repr(self._llm.decode([index_]))},\tval: {max_}")
                logit_results[index_] = float("-inf")
            print()

            if len(added_tokens) - instructions_len > 100:
                # Stop if the answer is too long
                self.final_answer = (answer_str +
                                     "... [Answer truncated due to length]")
                break

            finisher = ".\n"

            if finisher in answer_str:
                end_str = answer_str.find(finisher) + len(finisher)
                self.final_answer = answer_str[:end_str].strip()
                break

        print(f"\nFinal Answer:\n{repr(self.final_answer)}\n")

    def print(self, question: str | None = None) -> None:

        if question is None:
            if self.arg_inputs.question is None:  # pyright: ignore
                raise ValueError("no question has been "
                                 "passed by arg_inputs.")
            question = self.arg_inputs.question

        # json.dump([chunk.__dict__
        #            for chunk in self.k_database],
        #           search_file, indent=4)
        # for chunk in self.k_database:
        #     to_print = (f"{chunk.path} "
        #                 f"[{chunk.start_char}:"
        #                 f"{chunk.end_char}]")
        #     search_file.write(to_print + f"\tID: {chunk.id} - "
        #                       f"Score: {chunk.score}\n")
        #     print(to_print)
        retrieved_sources = MinimalAnswer(question=question,
                                          answer=self.final_answer)
        for chunk in self.k_database:
            retrieved_sources.retrieved_sources.append(chunk)

        print(f"The Answer to '{retrieved_sources.question}' is:")
        print(retrieved_sources.answer)
        print()

        try:

            with ((self.output_file_path).open("w") as search_file):
                json.dump(StudentSearchResultsAndAnswer(
                    search_results=[retrieved_sources],
                    k=self.arg_inputs.k).to_dict(),
                    search_file, indent=4)

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
    k_database_list: list[MinimalAnswer]
    output_file_path: Path

    vocab_text_int: dict[str, int]
    vocab_int_text: dict[int, str]
    questions_list: list[UnansweredQuestion]

    def __init__(self, ingest_database_path: Path, output_file_path: Path,
                 arg_inputs: InputHolder) -> None:

        self.arg_inputs = arg_inputs

        self.output_file_path = output_file_path

        self.get_all_questions()

        self.database = self._load_ingest_files(ingest_database_path)

        database_len = len(self.database)
        if not database_len:
            print("No database found. Please run the 'index' mode first.")
            return

        self.chunk_lookup = {
            (chunk.chunk.path,
             chunk.chunk.start_char,
             chunk.chunk.end_char): chunk.chunk
            for chunk in self.database
        }

        answers_obj = StudentSearchResultsAndAnswer(k=self.arg_inputs.k)

        self._load_llm()

        for question in self.all_questions:
            print(question.question)
            self.gen_k_database(question.question)
            print("k database got")

            # print(f"\nTop {self.arg_inputs.k} results for query: "
            #       f"'{self.arg_inputs.question}'\n")
            # print("\n".join(f"Chunk ID: {chunk.id}, Score: {chunk.score}"
            #                 for chunk in self.k_database))
            # print()

            answers_obj.search_results.append(self.gen_answer(question))

        self.print(answers_obj)

    def get_all_questions(self, questions_file: Path = Path(
            "data/datasets/UnansweredQuestions/dataset_docs_public.json")
            ) -> None:
        self.all_questions = []

        all_questions_json: list[dict[str, str]] = (
            get_from_json_file(questions_file)["rag_questions"]
        )

        for q in all_questions_json:
            self.all_questions.append(UnansweredQuestion(
                question=q["question"],
                question_id=q["question_id"]
            ))

    def search_cache(self, question: str) -> list[Chunk]:
        try:
            cache = StudentSearchResults(**get_from_json_file(
                self.arg_inputs.student_search_results_path))
        except FileNotFoundError:
            return []

        if not cache.k == self.arg_inputs.k:
            return []

        minimal_sources: list[MinimalSource] = []

        for search_result in cache.search_results:
            if search_result.question == question:
                minimal_sources = search_result.retrieved_sources
                break

        if not minimal_sources:
            return []

        k_database: list[Chunk | None] = [
            self.chunk_lookup.get((
                source.path,
                source.start_char,
                source.end_char
            )) for source in minimal_sources]

        if None in k_database:
            return []

        return [chunk for chunk in k_database if chunk is not None]

    def _load_ingest_files(self, ingest_database_path: Path
                           ) -> list[ChunkScorePair]:

        database_ingest_out: list[ChunkScorePair] = []

        files: list[Path] | tqdm[Path] = list(ingest_database_path.rglob("*"))

        print("\nLoading Ingested Database from:", ingest_database_path)
        if len(files) > 500:
            files = tqdm(files)

        for path in files:
            # print()
            # print(path)
            if path.is_dir():
                # print("skip", flush=True)
                continue
            elif path.is_file():
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
            else:
                continue

            database_ingest_out += add_chunks

        print()

        return database_ingest_out

    def gen_k_database(self, question: str | None = None) -> None:

        if question is None:
            if self.arg_inputs.question is None:  # pyright: ignore
                raise ValueError("no question has been "
                                 "passed by arg_inputs.")
            question = self.arg_inputs.question

        self.k_database = self.search_cache(question)

        if self.k_database:
            return

        # print()
        # print(question)
        # print()

        avg_chunk_len = (sum(len(chunk.chunk.content)
                             for chunk in self.database) / len(self.database))
        bm25_k1 = 1.4
        bm25_b = 0.75
        title_weight = 3.0

        complex_query = self.complex_split(question)

        # for chunk in self.database:
        #     print(chunk.chunk.id.replace(".", " ").lower(),
        #           chunk.chunk.content.lower(), sep="\n---\n")

        # input()

        values: list[set[str]] | tqdm[set[str]] = list(complex_query.values())

        print("\nGathering Chunks for:", question)
        if len(values) > 1000:
            values = tqdm(values)

        for variants in values:

            chunks_containing_q = sum(
                1 for chunk in self.database
                if any(
                    variant in chunk.chunk.content.lower()
                    for variant in variants
                )
            )

            idf_result = log(
                1 + ((len(self.database) - chunks_containing_q + 0.5) /
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

        k_database = self.database[:self.arg_inputs.k]

        min_relevance_score = (max(chunk.score for chunk in k_database)
                               * 0.01)
        k_database = [c for c in k_database
                      if c.score > min_relevance_score]

        self.k_database = [c.chunk for c in sorted(
            k_database, key=lambda x: x.score, reverse=True)]

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

    def gen_answer(self, question: UnansweredQuestion) -> MinimalAnswer:

        chunk_context = self._llm.encode(
            "You are a question-answering assistant. "
            "Answer the user's question using only the provided context."
            "\nRelevant context to answer:\n")

        context_separator = self._llm.encode("\n\n")

        context_prompt_separator = self._llm.encode(
            "Extra instruction:\n"
            "- Write the answer as plain, natural-language prose.\n"
            "- Do not use square brackets, lists, or placeholders."
            "- When asked for multiple items, name the actual items separated"
            " by commas, using 'and' before the final item."
            "- Never describe what the answer should contain,"
            " provide the actual answer."
            "- The answer should be short and concise. "
            "Do not repeat or rephrase the question.\n"
            "- Terminate your answer with a '.\\n'.\n\n"
            "According to the context above, Answer the following question:\n")

        post_question_prompt = self._llm.encode(
            "\n\nFinal Answer: "
        )

        self.instructions = chunk_context

        for chunk in self.k_database:
            self.instructions += chunk.content_vector
            self.instructions += context_separator

        self.instructions += context_prompt_separator

        self.instructions += (self._llm.encode(
            question.question) + post_question_prompt)

        instructions_len = len(self.instructions)

        # print(f"\aInstructions:\n\n{self._llm.decode(self.instructions)}")
        # print(f"\n\nInstructions Length: {instructions_len}\n")

        added_tokens = self.instructions

        answer_str = ""

        print(f"\nGenerating Answer for Question ID: {question.question_id}\n")

        while True:

            logit_results = self._llm.get_logits_from_input_ids(added_tokens)

            # logit_results[25] -= 2  # ':'
            logit_results[2509] -= 3  # " ['"
            logit_results[508] -= 3  # ' ['
            logit_results[364] -= 3  # " '"

            added_tokens.append(logit_results.index(max(logit_results)))

            answer_str += self._llm.decode([added_tokens[-1]])

            print(f"\nCurrent Answer:\n{repr(answer_str)}\n")

            for i in range(5):
                max_ = max(logit_results)
                index_ = logit_results.index(max_)
                print(f"Logit n{i+1}: {index_:6} -> "
                      f"{repr(self._llm.decode([index_]))},\tval: {max_}")
                logit_results[index_] = float("-inf")
            print()

            if len(added_tokens) - instructions_len > 100:
                # Stop if the answer is too long
                self.final_answer = (answer_str +
                                     "... [Answer truncated due to length]")
                break

            finisher = ".\n"

            if finisher in answer_str:
                end_str = answer_str.find(finisher) + len(finisher)
                self.final_answer = answer_str[:end_str].strip()
                break

        # print(f"\nFinal Answer:\n{repr(self.final_answer)}\n")

        return MinimalAnswer(
            question_id=question.question_id, question=question.question,
            answer=self.final_answer, retrieved_sources=list(map(
                lambda x: MinimalSource(path=x.path, start_char=x.start_char,
                                        end_char=x.end_char), self.k_database
            )))

    def print(self, answers_obj: StudentSearchResultsAndAnswer) -> None:

        try:

            with ((self.output_file_path).open("w") as search_file):
                json.dump(answers_obj.to_dict(), search_file, indent=4)

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
