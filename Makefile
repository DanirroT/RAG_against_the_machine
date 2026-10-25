# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    Makefile                                           :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: dmota-ri <dmota-ri@student.42lisboa.com    +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/04/10 16:50:27 by dmota-ri          #+#    #+#              #
#    Updated: 2026/10/25 21:06:33 by dmota-ri         ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

NAME = RAG_against_the_machine

# figure out what is " Your system must provide a Command-Line Interface (CLI) using Python Fire"

SRC = src

OBJ = $(SRC)/*.py

VENV = .venv/

UV_RUN = uv run python -m
DEBUGGER = $(UV_RUN) pdb

RM = rm -fr

.ONESHELL:

index:
	@$(UV_RUN) $(SRC) index
index_run_time:
	@time -f "\n\nTotal Run Time: %E" $(UV_RUN) $(SRC) index

search:
	@$(UV_RUN) $(SRC) search $(filter-out $@,$(MAKECMDGOALS))

search_dataset:
	@$(UV_RUN) $(SRC) search_dataset

answer:
	@$(UV_RUN) $(SRC) answer $(filter-out $@,$(MAKECMDGOALS))

answer_dataset:
	@$(UV_RUN) $(SRC) answer_dataset

evaluate:
	@$(UV_RUN) $(SRC) evaluate

ARGS = answer_dataset
NOW = $(shell date +%m-%d_%H:%M)

logs:
	@mkdir -p logs

record: logs

	@touch logs/$(NOW).log
	@$(UV_RUN) $(SRC) $(ARGS) 2>&1 | tee "logs/$(NOW).log"
	@echo "\n\nOutput_file:\n\n"

# record:
# 	@$(UV_RUN) $(SRC) $(filter-out $@,$(MAKECMDGOALS)) | tee Historic/$(NOW).log
# 	@echo "\n\nOutput_file:\n\n" >> Historic/$(NOW).log
# 	@cat data/output/function_calls.json >> Historic/$(NOW).log

QUESTION = "what are the Imports for inputs?"

run_full:
	@echo "\nRunning all modes:\n"
# 	@echo "\nIndexing:"
# 	@$(UV_RUN) $(SRC) index
	@echo "\nSearching:"
# 	@$(UV_RUN) $(SRC) search $(QUESTION)
	@$(UV_RUN) $(SRC) search_dataset
#	@echo "\nAnswering:"
#	@$(UV_RUN) $(SRC) answer
#	#	@$(UV_RUN) $(SRC) answer_dataset
#	#	@echo "\nEvaluating:"
#	#	@$(UV_RUN) $(SRC) evaluate


#  2>&1
debug:
	@$(DEBUGGER) $(MAIN).py $(MAP_FILE)

%:
	@:

install: $(VENV)

	. $(VENV)bin/activate
	uv sync
# 	uv pip install $(DEPENDENCIES)

$(VENV):
	uv venv $(VENV)

clean:
	@$(RM) ./__pycache__/ ./.mypy_cache/
	@$(RM) ./$(SRC)/__pycache__/ ./$(SRC)/.mypy_cache/
	@$(RM) ./llm_sdk/__pycache__/ ./llm_sdk/.mypy_cache/
	@$(RM) data/output

lint:
	@$(UV_RUN) flake8 $(OBJ) || true
	@$(UV_RUN) mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs $(OBJ) || true

lint-strict:
	@$(UV_RUN) flake8 $(OBJ) || true
	@$(UV_RUN) mypy --strict $(OBJ) || true
# 	@mypy --strict $(OBJ) || true
