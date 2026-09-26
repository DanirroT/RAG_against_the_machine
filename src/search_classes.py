from pathlib import Path
# import json
from typing import Any
from src import (InputHolder, ChunkScorePair, Chunk,
                 get_from_json_file)
from math import log, e, sqrt
from tqdm import tqdm
import json


class StrSearcher():

    database: list[ChunkScorePair]
    k_database: list[ChunkScorePair]
    arg_inputs: InputHolder

    llm_files: dict[str, Path]

    vocab_text_int: dict[str, int]
    vocab_int_text: dict[int, str]

    def __init__(self, ingest_database_path: Path, output_file_path: Path,
                 arg_inputs: InputHolder) -> None:

        self.arg_inputs = arg_inputs

        self.output_file_path = output_file_path
        self.database = self._load_ingest_files(ingest_database_path)

        self.gen_k_database()

        # print(f"\nTop {self.arg_inputs.k} results for query: "
        #       f"'{self.arg_inputs.question}'\n")
        # print("\n".join(f"Chunk ID: {chunk.chunk.id}, Score: {chunk.score}"
        #                 for chunk in self.k_database))

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

    def gen_k_database(self) -> None:

        # print()
        # print(self.arg_inputs.question)
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

        complex_query = self.complex_split(self.arg_inputs.question)

        # for chunk in self.database:
        #     print(chunk.chunk.id.replace(".", " ").lower(),
        #           chunk.chunk.content.lower(), sep="\n---\n")

        # input()

        values: list[set[str]] | tqdm[set[str]] = list(complex_query.values())

        if len(values) > 1000:
            values = tqdm(values)

        print("\nGathering Chunks for:", self.arg_inputs.question, "\n")
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

    def print(self) -> None:

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
            to_print = (f"{chunk.chunk.path} "
                        f"[{chunk.chunk.start_char}:"
                        f"{chunk.chunk.end_char}]")
            retrieved_sources.append({
                "file_path": chunk.chunk.path,
                "first_character_index": chunk.chunk.start_char,
                "last_character_index": chunk.chunk.end_char

            })
            print(to_print)
        print()

        try:

            with ((self.output_file_path).open("w") as search_file):
                json.dump({
                    "search_results": [
                        {
                            "question_id": (
                                f"Q{hash(self.arg_inputs.question)}"),
                            "question": self.arg_inputs.question,
                            "retrieved_sources": retrieved_sources
                        }
                    ],
                    "k": self.arg_inputs.k
                }, search_file, indent=4)

        except FileNotFoundError:
            print(f"Output file '{self.output_file_path}' not found. "
                  "Please create the file and try again.")


class FileSearcher():

    database: list[ChunkScorePair]
    k_database_list: list[list[ChunkScorePair]]
    arg_inputs: InputHolder

    llm_files: dict[str, Path]

    vocab_text_int: dict[str, int]
    vocab_int_text: dict[int, str]

    def __init__(self, ingest_database_path: Path, output_file_path: Path,
                 arg_inputs: InputHolder) -> None:

        self.arg_inputs = arg_inputs

        self.output_file_path = output_file_path
        self.database = self._load_ingest_files(ingest_database_path)
        self.questions_dict_list: list[dict[str, str]] = get_from_json_file(
            "data/datasets/UnansweredQuestions/"
            "dataset_code_public.json")["rag_questions"]

        self.k_database_list: list[list[ChunkScorePair]] = []

        questions_dict_values: list[dict[str, str]] | tqdm[dict[str, str]] = (
            self.questions_dict_list
        )

        if len(questions_dict_values) * len(self.database) > 1000:
            questions_dict_values = tqdm(questions_dict_values)

        print("\nGathering Chunks for all questions")

        for questions_dict in questions_dict_values:
            self.k_database_list.append(
                self.gen_k_database(questions_dict["question"]))

            # print(f"\nTop {self.arg_inputs.k} results for query: "
            #       f"'{questions_dict["question"}'\n")
            # input("\n".join(f"Chunk ID: {chunk.chunk.id},"
            #                 f" Score: {chunk.score}"
            #                 for chunk in self.k_database_list[-1]))

        print()

        self.print()

    def _load_ingest_files(self, ingest_database_path: Path
                           ) -> list[ChunkScorePair]:

        database_ingest_out: list[ChunkScorePair] = []

        files: list[Path] | tqdm[Path] = list(ingest_database_path.rglob("*"))

        if len(files) > 50:
            files = tqdm(files)

        print(f"\nLoading Ingested Database from: {ingest_database_path}")
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

        return database_ingest_out

    def gen_k_database(self, question: str) -> list[ChunkScorePair]:

        for chunk in self.database:
            chunk.score = 0

        # print()
        # print(question)
        # print()

        database_len = len(self.database)
        if not database_len:
            print("No database found. Please run the 'index' mode first.")
            raise FileNotFoundError("No database found. "
                                    "Please run the 'index' mode first.")
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

        for variants in complex_query.values():

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

        return k_database

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

    def print(self) -> None:

        return_list: list[dict[str, str | list[dict[str, str | int]]]] = []
        for k_database, question_dict in zip(self.k_database_list,
                                             self.questions_dict_list):
            retrieved_sources: list[dict[str, str | int]] = []
            for chunk in k_database:
                # to_print = (f"{chunk.chunk.path} "
                #             f"[{chunk.chunk.start_char}:"
                #             f"{chunk.chunk.end_char}]")
                retrieved_sources.append({
                    "file_path": chunk.chunk.path,
                    "first_character_index": chunk.chunk.start_char,
                    "last_character_index": chunk.chunk.end_char

                })

            return_list.append({
                "question_id": question_dict["question_id"],
                "question": question_dict["question"],
                "retrieved_sources": retrieved_sources
            })
            # print(to_print)
        # print()

        try:

            with ((self.output_file_path).open("w") as search_file):
                json.dump({
                    "search_results": return_list,
                    "k": self.arg_inputs.k
                }, search_file, indent=4)

        except FileNotFoundError:
            print(f"Output file '{self.output_file_path}' not found. "
                  "Please create the file and try again.")
