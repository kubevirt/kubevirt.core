all:

.PHONY: cluster-up
cluster-up:
	hack/e2e-setup.sh

.PHONY: cluster-down
cluster-down:
	hack/e2e-setup.sh --cleanup

.PHONY: build-venv
build-venv:
	tox run -e venv
	ln -sf .tox/venv .venv

.PHONY: format
format:
	tox run -e format
