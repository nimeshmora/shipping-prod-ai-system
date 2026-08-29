install:
	pip install -r requirements.txt

run:
	python -m app.main

test:
	python -m pytest -q

eval:
	python -m evals.run_evals

docker-build:
	docker build -t ship-agent .

docker-run:
	docker run --rm -p 8080:8080 --env-file .env ship-agent

# ---- guided checkpoints (mostly no API key needed) ----
check-setup:
	python -m checks.check setup

check-week-00:
	python -m checks.check 00
check-week-01:
	python -m checks.check 01
check-week-02:
	python -m checks.check 02
check-week-03:
	python -m checks.check 03
check-week-04:
	python -m checks.check 04
check-week-05:
	python -m checks.check 05
check-week-06:
	python -m checks.check 06
check-week-07:
	python -m checks.check 07
check-week-08:
	python -m checks.check 08

# ---- Week 06: the planted bug (instructor only) ----
plant-bug:
	python -m checks.plant_bug plant

fix-bug:
	python -m checks.plant_bug fix

check-all: check-week-00 check-week-01 check-week-02 check-week-03 check-week-04 check-week-05 check-week-06 check-week-07 check-week-08
