all:

.PHONY: cluster-up
cluster-up:
	hack/e2e-setup.sh

.PHONY: cluster-down
cluster-down:
	hack/e2e-setup.sh --cleanup
