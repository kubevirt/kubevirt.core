all:

.PHONY: cluster-up
cluster-up:
	hack/e2e-setup.sh

.PHONY: cluster-down
cluster-down:
	hack/e2e-setup.sh --install-kind --install-kubectl --cleanup

.PHONY: build-venv
build-venv:
	tox run -e venv
	ln -sf .tox/venv .venv

.PHONY: format
format:
	tox run -e format

.PHONY: test-sanity
test-sanity:
	tox -f sanity --ansible -p auto --conf tox-ansible.ini

.PHONY: test-unit
test-unit:
	tox -f unit --ansible -p auto --conf tox-ansible.ini

.PHONY: test-integration
test-integration:
	ansible-test integration
