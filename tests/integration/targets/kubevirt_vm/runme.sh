#!/usr/bin/env bash
set -eux
set -o pipefail

export ANSIBLE_CALLBACKS_ENABLED=ansible.posix.profile_tasks
export ANSIBLE_INVENTORY_ENABLED=kubevirt.core.kubevirt
export ANSIBLE_HOST_KEY_CHECKING=False

[ -d files ] || mkdir files
[ -f files/testkey ] || (ssh-keygen -t ed25519 -C test@test -f files/testkey -N "")

ansible-playbook playbook.yml "$@"

ansible-inventory -i test.kubevirt.yml -y --list "$@"

ansible-playbook verify.yml -i test.kubevirt.yml --private-key=files/testkey "$@"
