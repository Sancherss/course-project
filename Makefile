PYTHON ?= .venv/bin/python

.PHONY: install tools check baseline matrix diagnostics precision witnesses summary test report verify
install:
	python3 -m venv .venv
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install --no-deps -e .
tools:
	./scripts/bootstrap_proverif.sh
check:
	$(PYTHON) scripts/check_environment.py
baseline:
	$(PYTHON) scripts/run_baseline.py
matrix:
	$(PYTHON) -m experiment_manager run experiments/configs/matrix.yaml
diagnostics:
	$(PYTHON) -m experiment_manager run experiments/configs/diagnostics.yaml
precision:
	$(PYTHON) -m experiment_manager run experiments/configs/precision.yaml
witnesses:
	$(PYTHON) -m experiment_manager run experiments/configs/witnesses.yaml
summary:
	$(PYTHON) -m experiment_manager summary
test:
	$(PYTHON) -m pytest -q
report:
	$(PYTHON) scripts/plot_protocols.py
	$(PYTHON) scripts/plot_results.py
	$(PYTHON) scripts/render_report.py
verify:
	$(PYTHON) scripts/verify_artifacts.py
