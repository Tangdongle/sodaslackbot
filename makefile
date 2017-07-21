BIN = $(HOME)/.virtualenvs/sodaslackbot/bin

PYTHON = $(BIN)/python
NOSE = $(BIN)/nosetests
PIP = $(BIN)/pip

activate:
	source $(BIN)/activate

test:
	$(NOSE) PepsiCommandTest.py

shell:
	$(PYTHON)

sql:
	sqlite3 db/sodarecords.db
