PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python

.PHONY: venv validate test index export-smoke ci clean

venv:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r tools/requirements.txt

validate: venv
	mkdir -p out
	$(PY) tools/validate_library.py --report-json out/validation-report.json

test: venv
	$(PY) -m pytest -q tests/test_validate_library_fixtures.py

index: venv
	$(PY) tools/build_search_index.py

export-smoke: venv
	mkdir -p out/release-smoke
	$(PY) tools/export_field_pack.py \
		--project-id CI-SMOKE \
		--product SOIT-SCOMM-CF-CD-RAK-7266@AS9231_BASIC_STATION_POE \
		--product SOIT-SCOMM-CF-MD-RAK4630-RAK5802-MFM384@AS9231_RS485_9600N81 \
		--combined \
		--out out/release-smoke
	sha256sum out/release-smoke/*.zip > out/release-smoke/SHA256SUMS.txt

ci: validate test index export-smoke

clean:
	rm -rf out
