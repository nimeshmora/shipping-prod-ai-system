install:
	pip3 install -r requirements.txt

run:
	python3 -m app.main

test:
	python3 -m pytest -q

# ---- guided checkpoints (no API key needed) ----
check-setup:
	python3 -m checks.check setup

check-week-00:
	python3 -m checks.check 00
check-week-01:
	python3 -m checks.check 01

# ---- the container ----
docker-build:
	docker build -t ship-agent .

docker-run:
	docker run --rm -p 7000:7000 --env-file .env ship-agent
