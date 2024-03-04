# Testing

## Continuous integration

The `hack/e2e-setup.sh` script contains the steps necessary to reproduce the CI test environment, which relies on `kubectl` and `kind`.


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

