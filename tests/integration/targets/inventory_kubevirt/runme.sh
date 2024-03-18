#!/usr/bin/env bash
set -eux
set -o pipefail

export ANSIBLE_CALLBACKS_ENABLED=ansible.posix.profile_tasks
export ANSIBLE_INVENTORY_ENABLED=kubevirt.core.kubevirt

ansible-inventory -i test.kubevirt.yml -y --list --output empty.yml "$@"

ansible-playbook playbook.yml "$@"

ansible-inventory -i test.kubevirt.yml -y --list --output all.yml "$@"
ansible-inventory -i test.label.kubevirt.yml -y --list --output label.yml "$@"
ansible-inventory -i test.net.kubevirt.yml -y --list --output net.yml "$@"

ansible-playbook cleanup.yml "$@"

ansible-playbook verify.yml "$@"
