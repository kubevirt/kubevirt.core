# AGENTS.MD - kubevirt.core
## Strict rules
- Always make sure Apache 2.0 headers are present.
- Always run `make format`, `make test-unit`, `make test-sanity`, `make test-integration` before pushing.

## Project Overview
`kubevirt.core` is an Ansible collection that provides modules and plugins for managing KubeVirt virtual machines on Kubernetes clusters. It includes modules to create, delete, and query VirtualMachines and VirtualMachineInstances (`kubevirt_vm`, `kubevirt_vm_info`, `kubevirt_vmi_info`), as well as a dynamic inventory plugin (`kubevirt`) that discovers running VMs for use as Ansible targets. The collection depends on `kubernetes.core` and the Python `kubernetes` client library to interact with the Kubernetes API.

## Architecture
Ansible collection project with three main plugins:

* `kubevirt`: Inventory source for KubeVirt VirtualMachines
* `kubevirt_vm`: Create or delete KubeVirt VirtualMachines
* `kubevirt_vm_info`: Describe KubeVirt VirtualMachines
* `kubevirt_vmi_info`: Describe KubeVirt VirtualMachineInstances

The key directories are:

* `plugins/` — Contains all Ansible plugin code.
  * `plugins/modules/` — Ansible modules (`kubevirt_vm`, `kubevirt_vm_info`, `kubevirt_vmi_info`) that implement the CRUD operations against the KubeVirt API.
  * `plugins/inventory/` — Dynamic inventory plugin (`kubevirt.py`) that discovers KubeVirt VMs and exposes them as Ansible hosts.
  * `plugins/module_utils/` — Shared Python helpers (`diff.py`, `info.py`) used by the modules to handle resource diffing and info retrieval.
  * `plugins/doc_fragments/` — Reusable documentation fragments (e.g., `kubevirt_auth_options.py`) included in module docs.
* `tests/` — All test suites for the collection.
  * `tests/unit/` — Unit tests for plugin logic.
  * `tests/integration/` — Integration tests that run against a live KubeVirt cluster.
  * `tests/sanity/` — Ansible sanity test ignore files per Ansible version.
* `meta/` — Collection metadata (`runtime.yml`) defining the minimum supported Ansible version (`requires_ansible`).
* `docs/` — Project documentation sources (`developing.md` for code conventions, `testing.md` for test setup, `releasing.md` for versioning strategy).
* `examples/` — Sample playbooks and inventory files demonstrating collection usage.
* `changelogs/` — Changelog configuration and release fragments used by `antsibull-changelog`.
* `hack/` — Helper scripts for CI/dev environments (e.g., `e2e-setup.sh` for end-to-end cluster setup).
* `bin/` — Vendored tool wrappers (`kind`, `kubectl`) used by CI and local development.

## Build and Development
### Prerequisites
- Python (check [README.md](README.md) Section [Ansible and Python version compatibility](README.md#ansible-and-python-version-compatibility) for required version).
- Ansible (check [README.md](README.md) Section [Ansible and Python version compatibility](README.md#ansible-and-python-version-compatibility) for required version).
- `kubernetes.core` Ansible collection (see `requirements.yml` for version constraints). Install with `ansible-galaxy collection install -r requirements.yml`.
- Python libraries: `jsonpatch`, `kubernetes`, `PyYAML` (see `requirements.txt` for version constraints). Install with `pip install -r requirements.txt`.
- Test dependencies: `pytest`, `pytest-ansible`, `pytest-mock`, `pytest-xdist`, `ansible-compat`, `typing-extensions` (see `test-requirements.txt`). Install with `pip install -r test-requirements.txt`.
- Formatting: `black` (installed automatically by `tox` when running `make format`).
- `tox` and `tox-ansible` for running tests and managing virtualenvs.

### Key make targets
- `make build-venv` — Create a development virtualenv (via tox) and symlink it to `.venv`.
- `make format` — Run `black` code formatter.
- `make test-unit` — Run unit tests across supported Ansible versions.
- `make test-sanity` — Run Ansible sanity tests across supported Ansible versions.

### Cluster development
- `make test-integration` — Run integration tests (requires a running KubeVirt cluster).
- `make cluster-up` — Spin up a local Kind cluster with KubeVirt installed. 
- `make cluster-down` — Tear down the local Kind cluster. 

### Building collection
In order to build the collection and install it locally, run:

```bash
ansible-galaxy collection build .
ansible-galaxy collection install kubevirt-kubevirt.core-*.tar.gz
```
### Contributor's guidelines 
Check [developing.md](docs/developing.md) to get code and naming style conventions.

## Testing
- **Unit tests:** pytest is used. Run with `make test-unit`.
- **Integration tests:** Tests ran in a live Kubernetes cluster. These tests are collections of ansible playbooks crafted to deploy, fetch and assert certain actions.
- **Sanity tests:** Built-in `ansible-test sanity` checks (PEP 8, import validation, documentation, etc.). Run with `make test-sanity`. Per-version ignore files live in `tests/sanity/`, in this directory, a per-version ignore file need to be added everytime there is a new version of ansible-core..
- **Module unit tests:** Located in `tests/unit/plugins/modules/`. These tests invoke each module's `main()` entry point with patched `AnsibleModule` args and mocked API clients, verifying argument validation, expected API calls, and exit/fail outcomes without hitting a real cluster.
- **Blackbox unit tests:** Located in `tests/unit/plugins/inventory/blackbox/`. These tests call `_populate_inventory` with crafted VM, VMI, and service data, then assert the resulting inventory state (host vars, groups, connections). They verify user-facing inventory behaviour end-to-end without hitting a real cluster.

Follow instructions in [testing.md](docs/testing.md) to set up development environments. Use the `make` targets for running the tests.
Before running a test that makes use of `ansible-test` command such as `make test-integration`, it is required to spam a Kubernetes cluster using `make cluster-up` and to bind mount the repository as described in [testing.md](docs/testing.md) section "Running tests with ansible-test".
Moreover, the Kubernetes cluster can be used to do quick tests such as running a test Ansible inventory, Ansible playbook, etc. In directory, `bin` the tool `kubectl` can be found to work with the cluster directly. Nevertheless, in this project, ansible commands are preferred.

### Test patterns

#### Naming conventions
- Test files are named `test_<function_name>.py`, one per function under test.
- Test functions are named `test_<function>_<scenario>` (e.g., `test_fetch_objects_early_return`).

#### Unit test conventions
- Unit tests must assert and test each and every code branch.
- Unit tests use `mocker.patch` / `mocker.patch.object` (from `pytest-mock`) for patching, and `monkeypatch` when simpler attribute replacement suffices.
- Unit test must use `@pytest.mark.parametrize` as much as possible.
- When parametrize arguments become too complex or definitions could be reused across tests, define them as module-level dict constants and combine variants using the `|` (dict union) operator.
- Use `pytest.raises(Exception, match=pattern)` for exception message validation.

#### Shared fixtures and utilities
- `tests/unit/plugins/inventory/conftest.py` provides shared fixtures (`inventory`, `groups`, `hosts`, `client`) all scoped to `function` for test isolation.
- Test files may define local fixtures when scenarios require specific setup (e.g., `test_kubevirt_format_dynamic_api_exc.py`).
- `tests/unit/utils/ansible_module_mock.py` provides the `patch_module_args()` context manager and `AnsibleExitJson`/`AnsibleFailJson` exception classes used across module tests.
- `tests/unit/plugins/inventory/constants.py` provides shared constants (`DEFAULT_NAMESPACE`, `DEFAULT_BASE_DOMAIN`) and a `merge_dicts()` helper for deep dictionary merging.
- `request.getfixturevalue()` is used for dynamic fixture lookup when tests need to select fixtures at runtime.

#### Integration test structure
- Integration tests are located inside each `target` directory depending on which plugin is being tested (`tests/integration/targets/`).
- Each target contains: `runme.sh` (entry point), `generate.yml` (generates test files from Jinja2 templates), and `*.yml.j2` templates.
- Tests follow a Generate -> Run -> Verify -> Cleanup lifecycle with bash trap handlers for cleanup on failure.
- Namespace isolation is achieved via random suffixes to prevent conflicts between test runs.

## Plugin Design

### Inventory plugin — `plugins/inventory/kubevirt.py`
Dynamic inventory plugin that extends Ansible's `BaseInventoryPlugin`, `Constructable`, and `Cacheable`. Config files must end in `*.kubevirt.yml` or `*.kubevirt.yaml`.

The plugin follows a fetch-then-populate pipeline:
1. Parse the user config and build an options dataclass.
2. Check the inventory cache or fetch VMs, VMIs, and Services from the Kubernetes API via the `kubernetes.core` dynamic client.
3. Populate the inventory by creating groups (by cluster name and namespace) and adding hosts with variables derived from VM/VMI metadata and status.

Key design details:
- Host naming is configurable via `host_format` (default: `{namespace}-{name}`).
- Host vars are prefixed with `vm_` or `vmi_` depending on the source object. Status fields are converted from camelCase to snake_case.
- Connection address resolution follows a priority order: `kube_secondary_dns` derived hostname, LoadBalancer/NodePort service host+port, or the VMI's primary interface IP.
- Windows VMs are auto-detected (via `guestOSInfo`, preference annotations, or `vm.kubevirt.io/os` annotation) and set `ansible_connection=winrm` with WinRM service port lookup.
- Supports Ansible `constructed` features (`compose`, `groups`, `keyed_groups`).
- Includes backwards-compatible handling for a deprecated `connections` parameter (removed in 3.0.0).

### Module — `plugins/modules/kubevirt_vm.py`
Creates, patches, or deletes KubeVirt VirtualMachines. The module:
1. Defines its argument spec by merging module-specific args with auth and common specs from `kubernetes.core`.
2. Constructs a VM resource definition from module params, translating Ansible-style snake_case params into the KubeVirt API spec (camelCase).
3. Sets a wait condition based on `running`/`run_strategy` params to determine expected VM state.
4. Delegates execution to `kubernetes.core`'s runner.

Supports `name` or `generate_name` (mutually exclusive), `running` or `run_strategy` (mutually exclusive), instancetype/preference matchers, data volume templates, and `hidden_fields` for filtering noisy metadata from results.

### Module — `plugins/modules/kubevirt_vm_info.py`
Read-only module to describe KubeVirt VirtualMachines. Builds its arg spec from a shared info spec (defined in `module_utils/info.py`) plus auth args, adds a `running` parameter to control the wait condition, and delegates to a shared info execution function.

### Module — `plugins/modules/kubevirt_vmi_info.py`
Read-only module to describe KubeVirt VirtualMachineInstances. Structurally identical to `kubevirt_vm_info` but queries `VirtualMachineInstance` resources and has no `running` parameter (always waits for Ready=True).

### Shared utilities — `plugins/module_utils/`
- `info.py` — Shared argument spec and execution logic for the info modules. Instantiates a `K8sService`, performs the resource lookup, and exits with results.
- `diff.py` — Monkey-patches `kubernetes.core`'s diff logic to ignore metadata-only changes (`generation`, `resourceVersion`), fixing false-positive "changed" results.


## Conventions

### Code
- All source files must carry Apache 2.0 license headers.
- Code style and naming conventions are documented in [developing.md](docs/developing.md).
- Always use strong typing in the function headers. This applies to parameters and return values.

### Commits
- Commit messages follow conventional commits with scope, e.g. `feat(vm_info): ...`, `fix(tests): ...`, `chore(deps): ...`.
- Commits must be signed off (`git commit -s`).
- If an AI agent assisted the developer, the commit must add `assisted-by` and the AI agent signature.

### Pull requests and issues
- PRs must follow `.github/PULL_REQUEST_TEMPLATE.md`. Key sections: what the PR does, which issue(s) it fixes, reviewer notes, and a release note block.
- Issues must follow the templates in `.github/ISSUE_TEMPLATE/` (`bug_report.md`, `feature_request.md`).
- Always read the relevant template before creating a PR or issue and fill in all sections.
- PRs must pass CI (linter, sanity, unit, and integration tests) before merge.

### Versioning and releases
- The project follows [Semantic Versioning 2.0.0](https://semver.org/) as documented in [releasing.md](docs/releasing.md).
- Releases are triggered by annotated git tags. The CI workflow (`.github/workflows/release.yml`) builds the collection, publishes to Ansible Galaxy, and creates a GitHub release.
- Changelog entries are managed by `antsibull-changelog` using fragments in `changelogs/fragments/`.

### CI
- Main CI workflow (`.github/workflows/ci.yml`) runs: tree-clean check, ansible-lint, sanity tests, and unit tests across a matrix of Ansible and Python versions.
- Integration tests run in a separate workflow (`.github/workflows/integration.yml`) against a Kind cluster with KubeVirt.
- Docs linting validates Ansible documentation format via `antsibull-docs` (`.github/workflows/extra-docs-linting.yml`).
- Dependency updates are automated via Renovate (`renovate.json`), which manages e2e-setup tool versions, GitHub Actions, and collection dependencies.
