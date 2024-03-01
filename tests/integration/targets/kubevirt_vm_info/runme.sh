#!/usr/bin/env bash
set -eux
set -o pipefail

export ANSIBLE_CALLBACKS_ENABLED=ansible.posix.profile_tasks

ansible-playbook playbook.yml "$@"
