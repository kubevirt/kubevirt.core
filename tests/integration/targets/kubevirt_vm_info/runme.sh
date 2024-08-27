#!/usr/bin/env bash
set -eux

export ANSIBLE_CALLBACKS_ENABLED=ansible.posix.profile_tasks

if [ -f "extra_vars.sh" ]; then
    source extra_vars.sh
fi

NAMESPACE="test-kubevirt-vm-info-$(tr -dc '[:lower:]' < /dev/urandom | head -c 5)"

cleanup() {
    ansible localhost -m kubernetes.core.k8s -a "name=${NAMESPACE} api_version=v1 kind=Namespace state=absent"
    rm -rf playbook.yml
}
trap cleanup EXIT

# Prepare the test environment
ansible localhost -m kubernetes.core.k8s -a "name=${NAMESPACE} api_version=v1 kind=Namespace state=present"
ansible-playbook -e "NAMESPACE=${NAMESPACE}" generate.yml

# Run the tests
ansible-playbook playbook.yml "$@"
