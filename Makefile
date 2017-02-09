init:
	sudo pip install -r requirements.txt
	sudo pip install -e .

test:
	py.test tests

docs:
	cd docs; make html; cd ..

all: init test docs

.PHONY: init
