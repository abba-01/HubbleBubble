PY = python
VENV = .venv
ACT = source $(VENV)/bin/activate

.PHONY: all setup data validate report clean

all: setup data validate report

setup:
	python3 -m venv $(VENV); \
	$(ACT); \
	python -m pip install -U pip wheel; \
	python -m pip install -r requirements.txt

data:
	$(ACT); \
	$(PY) src/data_io.py --fetch --cache-dir assets

validate:
	$(ACT); \
	$(PY) src/validation/loao.py --out outputs/results/loao.json; \
	$(PY) src/validation/grids.py --out outputs/results/grids.json; \
	$(PY) src/validation/bootstrap.py --iters 10000 --out outputs/results/bootstrap.json; \
	$(PY) src/validation/inject.py --trials 2000 --out outputs/results/inject.json

report:
	$(ACT); \
	$(PY) src/report/build_report.py --out outputs/h0_validation_report.html

clean:
	rm -rf outputs/* __pycache__ */__pycache__ src/__pycache__ src/*/__pycache__
