# Container engine. Defaults to Podman (rootless/daemonless); override with:
#   make infra-up CONTAINER_ENGINE="docker"
CONTAINER_ENGINE ?= podman

.PHONY: help install demo analytics api dashboard produce fmr clean infra-up infra-down oc-build oc-deploy oc-undeploy

help:
	@echo "Targets:"
	@echo "  install     Create .venv and install core dependencies"
	@echo "  demo        Run the full pipeline end-to-end locally (no external services)"
	@echo "  analytics   Recompute analytics + AI-evaluation metrics and HTML/MD reports"
	@echo "  api         Serve the metrics API (http://localhost:8001)"
	@echo "  dashboard   Launch the Streamlit analytics dashboard"
	@echo "  fmr         Run the FMR mock API server (http://localhost:8000)"
	@echo "  produce     Generate mock SDMX submissions to a local JSONL file"
	@echo "  infra-up    Start Kafka + FMR mock via '$(CONTAINER_ENGINE) compose'"
	@echo "  infra-down  Stop the compose services"
	@echo "  oc-build    Build the app image on OpenShift (ImageStream + BuildConfig)"
	@echo "  oc-deploy   Deploy all workloads to the current OpenShift project"
	@echo "  oc-undeploy Remove the OpenShift workloads"
	@echo "  clean       Remove generated data artifacts"

install:
	python3 -m venv .venv
	./.venv/bin/pip install --upgrade pip
	./.venv/bin/pip install duckdb numpy fastapi uvicorn pydantic requests

demo:
	python3 run_demo.py

analytics:
	python3 analytics/run_analytics.py

api:
	uvicorn analytics.metrics_api:app --reload --port 8001

dashboard:
	streamlit run dashboard/app.py

fmr:
	uvicorn metadata_registry.fmr_mock_api:app --reload --port 8000

produce:
	python3 data_generator/kafka_producer.py --local --count 500

infra-up:
	$(CONTAINER_ENGINE) compose up -d --build

infra-down:
	$(CONTAINER_ENGINE) compose down -v

oc-build:
	oc apply -f openshift/imagestream.yaml -f openshift/buildconfig.yaml
	oc start-build suptech-xai --from-dir=. --follow

oc-deploy:
	oc apply -k openshift/

oc-undeploy:
	oc delete -k openshift/ --ignore-not-found

clean:
	rm -rf data/*.jsonl data/*.parquet data/*.csv data/*.json data/reports/*.md data/reports/*.html
