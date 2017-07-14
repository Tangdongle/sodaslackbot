BIN = $(HOME)/.virtualenvs/sodabot/bin

PYTHON = $(BIN)/python
NOSE = $(BIN)/nosetests
PIP = $(BIN)/pip

activate:
	source $(BIN)/activate

test:
	$(NOSE) PepsiCommandTest.py

shell:
	$(PYTHON)

