#!/usr/bin/env bash
set -eux
set -o pipefail

export ANSIBLE_CALLBACKS_ENABLED=ansible.posix.profile_tasks
export ANSIBLE_INVENTORY_ENABLED=kubevirt.core.kubevirt
export ANSIBLE_HOST_KEY_CHECKING=False

[ -d files ] || mkdir files
[ -f files/testkey ] || (ssh-keygen -t rsa -C test@test -f files/testkey -N "")

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
