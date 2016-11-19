
install:
	pip install -r requires.txt

data:
	python draftkings/manage.py loaddata stats.nba.com.json

db:
	python draftkings/manage.py migrate

build:
	install db data

build_docs:
	sphinx-apidoc -f -e -o docs/source ./draftkings
	cd docs && $(MAKE) html

new_fixture:
	python draftkings/manage.py dumpdata basketball -o draftkings/basketball/fixtures/new_fixture.json

check:
	flake8 --max-line-length=120
