# Testing

## Sanity and unit tests

Sanity and unit tests can be run in two ways:

- with `tox` and the `tox-ansible` plugin (both need to be installed on the dev machine)
- with `ansible-test`

For development purposes `tox` and `tox-ansible` are better suited, as they allow
debugging of issues in the collection on the developer's machine.

For verification purposes of the collection the compatibility with `ansible-test`
is ensured.

### Running tests with tox-ansible

Run sanity tests with `tox-ansible` like so:

```
make test-sanity
```

Run unit tests with `tox-ansible` like so:

```
make test-unit
```

### Running tests with ansible-test

In order to test changes with `ansible-test`, it is recommended to bind mount
the repository to `~/.ansible/collections/ansible_collections/kubevirt/core`
if you did not check it out into this location.

This can be done with:

```
mkdir -p ~/.ansible/collections/ansible_collections/kubevirt/core
sudo mount --bind <project_dir>/kubevirt.core ~/.ansible/collections/ansible_collections/kubevirt/core
cd ~/.ansible/collections/ansible_collections/kubevirt/core
```

Run sanity tests with `ansible-test` like so:

```
ANSIBLE_TEST_PREFER_PODMAN=1 ansible-test sanity --docker
```

Run unit tests with `ansible-test` like so:

```
ANSIBLE_TEST_PREFER_PODMAN=1 ansible-test units --docker
```

## Integration tests

Integration tests require a working cluster and can be run with
`ansible-test`.

### Continuous integration

The `hack/e2e-setup.sh` script contains the steps necessary to reproduce the
CI integration test environment, which relies on `docker` or `podman`,
`kubectl` and `kind`.

To create the CI integration test environment on your machine run:

```
make cluster-up
```

To remove the test CI integration test environment run:

```
make cluster-down
```

### Running integration tests with ansible test

Run integration tests with ansible-test like so:

```
ansible-test integration
```

## Example config and playbooks

Sample playbooks and inventory configurations are provided in the `examples/` directory; to run the playbooks locally, build the testing environment with the script above, then the steps are as follows:

```bash
# setup environment
pip install ansible-core
# clone the repository
git clone https://github.com/kubevirt/kubevirt.core
cd kubevirt.core
# install collection dependencies
ansible-galaxy collection install -r requirements.yml
# install collection python deps
pip install -r requirements.txt
# setup environment
hack/e2e-setup.sh
# run inventory source
ansible-inventory -i examples/inventory.kubevirt.yml
# create a virtual machine
ansible-playbook -i examples/inventory.kubevirt.yml examples/play-create-min.yml
# terminate a virtual machine
ansible-playbook -i examples/inventory.kubevirt.yml examples/play-delete.yml
# terminate the environment
hack/e2e-setup.sh --cleanup
```

