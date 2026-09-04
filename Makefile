install:
	pip3 install -r requirements.txt

run:
	python3 -m app.main

test:
	python3 -m pytest -q

eval:
	python3 -m evals.run_evals

# Week 08: also grade answer QUALITY, not just keywords. Needs OPENROUTER_API_KEY.
eval-judge:
	python3 -m evals.run_evals --real --judge

# Week 07: concurrency is where the honest bugs come due.
load:
	python3 -m loadtest.run_load --n 60 --concurrency 12

load-stream:
	python3 -m loadtest.run_load --n 30 --concurrency 8 --stream

docker-build:
	docker build -t ship-agent .

docker-run:
	docker run --rm -p 7000:7000 --env-file .env ship-agent

# ---- guided checkpoints (mostly no API key needed) ----
check-setup:
	python3 -m checks.check setup

check-week-00:
	python3 -m checks.check 00
check-week-01:
	python3 -m checks.check 01
check-week-02:
	python3 -m checks.check 02
check-week-03:
	python3 -m checks.check 03
check-week-04:
	python3 -m checks.check 04
check-week-05:
	python3 -m checks.check 05
check-week-06:
	python3 -m checks.check 06
check-week-07:
	python3 -m checks.check 07
check-week-08:
	python3 -m checks.check 08

# ---- Week 05: a place to look at traces ----
# Grafana + Tempo: the dashboard stack most teams actually use.
trace-ui:
	docker compose -f observability/docker-compose.yml up -d
	@echo ""
	@echo "Grafana:  http://localhost:3000   (no login)"
	@echo "  Explore -> Tempo -> Search -> Run query"
	@echo ""
	@echo "Then, in the terminal you run the agent from:"
	@echo "  export OTEL_ENABLED=1"
	@echo "  export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318"
	@echo "  make run"

trace-ui-stop:
	docker compose -f observability/docker-compose.yml down

# ---- Week 06: the planted bug (instructor only) ----
plant-bug:
	python3 -m checks.plant_bug plant

fix-bug:
	python3 -m checks.plant_bug fix

check-all: check-week-00 check-week-01 check-week-02 check-week-03 check-week-04 check-week-05 check-week-06 check-week-07 check-week-08
