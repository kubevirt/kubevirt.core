#!/usr/bin/env bash
set -eux

export ANSIBLE_CALLBACKS_ENABLED=ansible.posix.profile_tasks
export ANSIBLE_INVENTORY_ENABLED=kubevirt.core.kubevirt

if [ -f "extra_vars.sh" ]; then
    source extra_vars.sh
fi

NAMESPACE="test-inventory-kubevirt-$(tr -dc '[:lower:]' < /dev/urandom | head -c 5)"
SECONDARY_NETWORK=${SECONDARY_NETWORK:-default/kindexgw}

cleanup() {
    ansible localhost -m kubernetes.core.k8s -a "name=${NAMESPACE} api_version=v1 kind=Namespace state=absent"
    rm -rf all.yml cache_after.yml cache_before.yml cleanup.yml empty.yml label.yml net.yml playbook.yml \
           test.cache.kubevirt.yml test.kubevirt.yml test.label.kubevirt.yml test.net.kubevirt.yml verify.yml \
           kubevirt-cache
}
trap cleanup EXIT

# Prepare the test environment
ansible localhost -m kubernetes.core.k8s -a "name=${NAMESPACE} api_version=v1 kind=Namespace state=present"
ansible-playbook \
  -e "NAMESPACE=${NAMESPACE}" \
  -e "SECONDARY_NETWORK=${SECONDARY_NETWORK}" \
  generate.yml

# Run the tests
ansible-inventory -i test.kubevirt.yml -y --list --output empty.yml "$@"

ansible-playbook playbook.yml "$@"

ansible-inventory -i test.kubevirt.yml -y --list --output all.yml "$@"
ansible-inventory -i test.cache.kubevirt.yml -y --list --output cache_before.yml "$@"
ansible-inventory -i test.label.kubevirt.yml -y --list --output label.yml "$@"
ansible-inventory -i test.net.kubevirt.yml -y --list --output net.yml "$@"

ansible-playbook cleanup.yml "$@"

ansible-inventory -i test.cache.kubevirt.yml -y --list --output cache_after.yml "$@"

ansible-playbook verify.yml "$@"
