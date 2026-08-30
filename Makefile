install:
	pip install -r requirements.txt

run:
	python -m app.main

test:
	python -m pytest -q

# ---- guided checkpoints (no API key needed) ----
check-setup:
	python -m checks.check setup

check-week-00:
	python -m checks.check 00
check-week-01:
	python -m checks.check 01

# ---- the container ----
docker-build:
	docker build -t ship-agent .

docker-run:
	docker run --rm -p 8080:8080 --env-file .env ship-agent
