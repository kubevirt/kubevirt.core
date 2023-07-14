#!/usr/bin/env bash

set -eux

source virtualenv.sh
pip install kubernetes PyYAML jsonpatch Jinja2

./server.py &

cleanup() {
  kill -9 "$(jobs -p)"
}

trap cleanup INT TERM EXIT

# Fake auth file
mkdir -p ~/.kube/
cat <<EOF > ~/.kube/config
apiVersion: v1
clusters:
- cluster:
    insecure-skip-tls-verify: true
    server: http://localhost:12345
  name: development
contexts:
- context:
    cluster: development
    user: developer
  name: dev-frontend
current-context: dev-frontend
kind: Config
preferences: {}
users:
- name: developer
  user:
    token: ZDNg7LzSlp8a0u0fht_tRnPMTOjxqgJGCyi_iy0ecUw
EOF

#################################################
#   RUN THE PLUGIN
#################################################

# run the plugin second
export ANSIBLE_INVENTORY_ENABLED=kubernetes.kubevirt.kubevirt

cat << EOF > "$OUTPUT_DIR/test.kubevirt.yml"
plugin: kubernetes.kubevirt.kubevirt
connections:
  - namespaces:
    - default
EOF

ansible-inventory -vvvv -i "$OUTPUT_DIR/test.kubevirt.yml" --list --output="$OUTPUT_DIR/plugin.out"

#################################################
#   DIFF THE RESULTS
#################################################

diff "$(pwd)/test.out" "$OUTPUT_DIR/plugin.out"
