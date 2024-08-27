#!/usr/bin/env bash
set -eux

export ANSIBLE_CALLBACKS_ENABLED=ansible.posix.profile_tasks
export ANSIBLE_INVENTORY_ENABLED=kubevirt.core.kubevirt
export ANSIBLE_HOST_KEY_CHECKING=False

if [ -f "extra_vars.sh" ]; then
    source extra_vars.sh
fi

NAMESPACE="test-kubevirt-vm-$(tr -dc '[:lower:]' < /dev/urandom | head -c 5)"
SECONDARY_NETWORK=${SECONDARY_NETWORK:-default/kindexgw}

cleanup() {
    ansible localhost -m kubernetes.core.k8s -a "name=${NAMESPACE} api_version=v1 kind=Namespace state=absent"
    rm -rf playbook.yml test.kubevirt.yml verify.yml wait_for_vm.yml files
}
trap cleanup EXIT

# Prepare the test environment
ansible localhost -m kubernetes.core.k8s -a "name=${NAMESPACE} api_version=v1 kind=Namespace state=present"
ansible-playbook \
  -e "NAMESPACE=${NAMESPACE}" \
  -e "SECONDARY_NETWORK=${SECONDARY_NETWORK}" \
  generate.yml

[ -d files ] || mkdir files
[ -f files/testkey ] || (ssh-keygen -t rsa -C test@test -f files/testkey -N "")

# Run the tests
ansible-playbook playbook.yml "$@"

ansible-inventory -i test.kubevirt.yml -y --list "$@"

# Retry connection to VM until a login is possible
# This is necessary since wait_for is not enough to wait for logins to be possible.
# wait_for is only able to wait until sshd accepts connections.
retries=0
while ! ansible-playbook wait_for_vm.yml -i test.kubevirt.yml --private-key=files/testkey "$@"; do
  if [ "$retries" -ge "10" ]; then
    echo "Maximum retries reached, giving up"
    exit 1
  fi
  echo "Failed to wait for VM, retrying..."
  sleep 10
  ((retries+=1))
done

ansible-playbook verify.yml --diff -i test.kubevirt.yml --private-key=files/testkey "$@"
