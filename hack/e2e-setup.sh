#!/usr/bin/env bash
#
# This file is part of the KubeVirt project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Copyright 2023 Red Hat, Inc.
#

# This script is based on:
# - https://github.com/ovn-org/ovn-kubernetes/blob/master/contrib/kind.sh
# - https://github.com/kiagnose/kiagnose/blob/main/automation/e2e.sh
# - https://github.com/kiagnose/kiagnose/blob/main/checkups/kubevirt-vm-latency/automation/e2e.sh

ARGCOUNT=$#
# Returns the full directory name of the script
DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
ARCH=""
case $(uname -m) in
x86_64) ARCH="amd64" ;;
aarch64) ARCH="arm64" ;;
esac

set_default_params() {
  BIN_DIR=${BIN_DIR:-$DIR/../bin}

  KIND=${KIND:-$BIN_DIR/kind}
  KIND_VERSION=${KIND_VERSION:-v0.20.0}

  KUBECTL=${KUBECTL:-$BIN_DIR/kubectl}
  KUBECTL_VERSION=${KUBECTL_VERSION:-v1.27.3}

  KUBEVIRT_VERSION=${KUBEVIRT_VERSION:-v1.0.0}
  KUBEVIRT_COMMON_INSTANCETYPES_VERSION=${KUBEVIRT_COMMON_INSTANCETYPES_VERSION:-v0.3.0}
  KUBEVIRT_USE_EMULATION=${KUBEVIRT_USE_EMULATION:-"false"}

  CNAO_VERSION=${CNAO_VERSION:-v0.87.0}

  CLUSTER_NAME=${CLUSTER_NAME:-kind}
  SECONDARY_NETWORK_NAME=${NETWORK_NAME:-kindexgw}
  SECONDARY_NETWORK_SUBNET=${SECONDARY_NETWORK_SUBNET:-172.19.0.0/16}
  SECONDARY_NETWORK_RANGE_START=${SECONDARY_NETWORK_RANGE_START:-172.19.1.1}
  SECONDARY_NETWORK_RANGE_END=${SECONDARY_NETWORK_RANGE_END:-172.19.255.254}
  SECONDARY_NETWORK_GATEWAY=${SECONDARY_NETWORK_GATEWAY:-172.19.0.1}

  NAMESPACE=${NAMESPACE:-default}
}

# Taken from:
# https://github.com/kubevirt/kubevirtci/blob/f661bfe0e3678e5409c057855951c50a912571a0/cluster-up/cluster/ephemeral-provider-common.sh#L26C1-L45C1
detect_cri() {
  PODMAN_SOCKET=${PODMAN_SOCKET:-"/run/podman/podman.sock"}

  if [ "${CRI}" = "podman" ]; then
    _cri_socket=$(detect_podman_socket)
    _cri_bin="podman --remote --url=unix://$_cri_socket"
  elif [ "${CRI}" = "docker" ]; then
    _cri_bin=docker
    _cri_socket="/var/run/docker.sock"
  else
    _cri_socket=$(detect_podman_socket)
    if [ -n "$_cri_socket" ]; then
      _cri_bin="podman --remote --url=unix://$_cri_socket"
      echo >&2 "selecting podman as container runtime"
    elif docker ps >/dev/null 2>&1; then
      _cri_bin=docker
      _cri_socket="/var/run/docker.sock"
      echo >&2 "selecting docker as container runtime"
    else
      echo >&2 "no working container runtime found. Neither docker nor podman seems to work."
      exit 1
    fi
  fi
}

# Taken from:
# https://github.com/kubevirt/kubevirtci/blob/f661bfe0e3678e5409c057855951c50a912571a0/cluster-up/cluster/ephemeral-provider-common.sh#L20
detect_podman_socket() {
  if curl --unix-socket "${PODMAN_SOCKET}" http://d/v3.0.0/libpod/info >/dev/null 2>&1; then
    echo "${PODMAN_SOCKET}"
  fi
}

install_kind() {
  if [ ! -f "${KIND}" ]; then
    echo "Installing kind"
    mkdir -p "${BIN_DIR}"
    curl -Lo "${KIND}" "https://kind.sigs.k8s.io/dl/${KIND_VERSION}/kind-linux-${ARCH}"
    chmod +x "${KIND}"

    echo "Successfully installed kind at ${KIND}:"
    ${KIND} version
  fi
}

install_kubectl() {
  if [ ! -f "${KUBECTL}" ]; then
    echo "Installing kubectl"
    mkdir -p "${BIN_DIR}"
    curl -Lo "${KUBECTL}" "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${ARCH}/kubectl"
    chmod +x "${KUBECTL}"

    echo "Successfully installed kubectl at ${KUBECTL}:"
    ${KUBECTL} version --client
  fi
}

configure_inotify_limits() {
  echo "Configuring inotify limits"
  sudo sysctl fs.inotify.max_user_instances=512
  sudo sysctl fs.inotify.max_user_watches=1048576
}

create_cluster() {
  echo "Creating cluster with kind"
  DOCKER_HOST=unix://${_cri_socket} ${KIND} create cluster --wait 2m --name "${CLUSTER_NAME}"

  echo "Waiting for the network to be ready"
  ${KUBECTL} wait --for=condition=ready pods --namespace=kube-system -l k8s-app=kube-dns --timeout=2m

  echo "K8S cluster is up:"
  ${KUBECTL} get nodes -o wide
}

configure_secondary_network() {
  echo "Configuring secondary network"
  # Name of the single kind node
  local node=${CLUSTER_NAME}-control-plane
  # Interface added when connecting the secondary network
  local secondary_interface=eth1

  ${_cri_bin} network create "${SECONDARY_NETWORK_NAME}" --driver=bridge --subnet="${SECONDARY_NETWORK_SUBNET}"
  ${_cri_bin} network connect "${SECONDARY_NETWORK_NAME}" "${node}"

  # Get the ip address assigned to the interface of the secondary network on the node
  local ip
  ip=$(
    ${_cri_bin} exec "${node}" ip ad show dev "${secondary_interface}" scope global |
      sed -n 's/^    inet \([[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\.[[:digit:]]\{1,3\}\/[[:digit:]]\{1,2\}\).*$/\1/p'
  )

  # Configure a bridge inside the node that workloads can attach to
  ${_cri_bin} exec "${node}" ip link add "${SECONDARY_NETWORK_NAME}" type bridge
  ${_cri_bin} exec "${node}" ip link set "${secondary_interface}" master "${SECONDARY_NETWORK_NAME}"
  ${_cri_bin} exec "${node}" ip link set up "${SECONDARY_NETWORK_NAME}"
  # Move the ip address from the secondary interface to the newly created bridge
  ${_cri_bin} exec "${node}" ip address del "${ip}" dev "${secondary_interface}"
  ${_cri_bin} exec "${node}" ip address add "${ip}" dev "${SECONDARY_NETWORK_NAME}"
}

deploy_kubevirt() {
  echo "Deploying KubeVirt"
  ${KUBECTL} apply -f "https://github.com/kubevirt/kubevirt/releases/download/${KUBEVIRT_VERSION}/kubevirt-operator.yaml"
  ${KUBECTL} apply -f "https://github.com/kubevirt/kubevirt/releases/download/${KUBEVIRT_VERSION}/kubevirt-cr.yaml"

  if ! is_nested_virt_enabled; then
    echo "Configuring Kubevirt to use emulation"
    ${KUBECTL} patch kubevirt kubevirt --namespace kubevirt --type=merge --patch '{"spec":{"configuration":{"developerConfiguration":{"useEmulation":true}}}}'
  fi

  echo "Waiting for KubeVirt to be ready"
  ${KUBECTL} wait --for=condition=Available kubevirt kubevirt --namespace=kubevirt --timeout=5m

  echo "Successfully deployed KubeVirt:"
  ${KUBECTL} get pods -n kubevirt
}

# Taken from:
# https://github.com/ovn-org/ovn-kubernetes/blob/59e0b62f4048be3df5b364b894b495f52f729cf1/contrib/kind.sh#L1241
is_nested_virt_enabled() {
  local kvm_nested="unknown"
  if [ -f "/sys/module/kvm_intel/parameters/nested" ]; then
    kvm_nested=$(cat /sys/module/kvm_intel/parameters/nested)
  elif [ -f "/sys/module/kvm_amd/parameters/nested" ]; then
    kvm_nested=$(cat /sys/module/kvm_amd/parameters/nested)
  fi
  [ "$kvm_nested" == "1" ] || [ "$kvm_nested" == "Y" ] || [ "$kvm_nested" == "y" ]
}

deploy_kubevirt_common_instancetypes() {
  echo "Deploying KubeVirt common-instancetypes"
  ${KUBECTL} apply -f "https://github.com/kubevirt/common-instancetypes/releases/download/${KUBEVIRT_COMMON_INSTANCETYPES_VERSION}/common-instancetypes-all-bundle-${KUBEVIRT_COMMON_INSTANCETYPES_VERSION}.yaml"
}

deploy_cnao() {
  echo "Deploying CNAO (with multus and bridge CNIs)"
  ${KUBECTL} apply -f "https://github.com/kubevirt/cluster-network-addons-operator/releases/download/${CNAO_VERSION}/namespace.yaml"
  ${KUBECTL} apply -f "https://github.com/kubevirt/cluster-network-addons-operator/releases/download/${CNAO_VERSION}/network-addons-config.crd.yaml"
  ${KUBECTL} apply -f "https://github.com/kubevirt/cluster-network-addons-operator/releases/download/${CNAO_VERSION}/operator.yaml"

  cat <<EOF | ${KUBECTL} apply -f -
apiVersion: networkaddonsoperator.network.kubevirt.io/v1
kind: NetworkAddonsConfig
metadata:
  name: cluster
spec:
  imagePullPolicy: IfNotPresent
  linuxBridge: {}
  multus: {}
EOF

  echo "Waiting for CNAO to be ready"
  ${KUBECTL} wait --for condition=Available networkaddonsconfig cluster --timeout=5m

  echo "Successfully deployed CNAO:"
  ${KUBECTL} get networkaddonsconfig cluster -o yaml
}

create_nad() {
  echo "Creating NetworkAttachmentDefinition (with bridge CNI)"
  cat <<EOF | ${KUBECTL} apply -f -
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: ${SECONDARY_NETWORK_NAME}
  namespace: ${NAMESPACE}
spec:
  config: |
    {
      "cniVersion": "0.3.1",
      "name": "${SECONDARY_NETWORK_NAME}",
      "type": "bridge",
      "bridge": "${SECONDARY_NETWORK_NAME}",
      "ipam": {
        "type": "host-local",
        "ranges": [
          [
            {
              "subnet": "${SECONDARY_NETWORK_SUBNET}",
              "rangeStart": "${SECONDARY_NETWORK_RANGE_START}",
              "rangeEnd": "${SECONDARY_NETWORK_RANGE_END}",
              "gateway": "${SECONDARY_NETWORK_GATEWAY}"
            }
          ]
        ]
      }
    }
EOF

  echo "Successfully created NetworkAttachmentDefinition:"
  ${KUBECTL} get networkattachmentdefinition.k8s.cni.cncf.io "${SECONDARY_NETWORK_NAME}" --namespace "${NAMESPACE}" -o yaml
}

cleanup() {
  DOCKER_HOST=unix://${_cri_socket} ${KIND} delete cluster --name "${CLUSTER_NAME}"
  ${_cri_bin} network rm "${SECONDARY_NETWORK_NAME}"
}

usage() {
  echo -n "$0 [--install-kind] [--install-kubectl] [--configure-inotify-limits] [--create-cluster] [--deploy-kubevirt] [--deploy-kubevirt-common-instancetypes] [--deploy-cnao] [--create-nad] [--cleanup] [--namespace]"
}

set_default_options() {
  OPT_INSTALL_KIND=false
  OPT_INSTALL_KUBECTL=false
  OPT_CONFIGURE_INOTIFY_LIMITS=false
  OPT_CREATE_CLUSTER=false
  OPT_CONFIGURE_SECONDARY_NETWORK=false
  OPT_DEPLOY_KUBEVIRT=false
  OPT_DEPLOY_KUBEVIRT_COMMON_INSTANCETYPES=false
  OPT_DEPLOY_CNAO=false
  OPT_CREATE_NAD=false
  OPT_CLEANUP=false
}

parse_args() {
  while [ "$1" != "" ]; do
    case "$1" in
    --install-kind) OPT_INSTALL_KIND=true ;;
    --install-kubectl) OPT_INSTALL_KUBECTL=true ;;
    --configure-inotify-limits) OPT_CONFIGURE_INOTIFY_LIMITS=true ;;
    --create-cluster) OPT_CREATE_CLUSTER=true ;;
    --configure-secondary-network) OPT_CONFIGURE_SECONDARY_NETWORK=true ;;
    --deploy-kubevirt) OPT_DEPLOY_KUBEVIRT=true ;;
    --deploy-kubevirt-common-instancetypes) OPT_DEPLOY_KUBEVIRT_COMMON_INSTANCETYPES=true ;;
    --deploy-cnao) OPT_DEPLOY_CNAO=true ;;
    --create-nad) OPT_CREATE_NAD=true ;;
    --cleanup) OPT_CLEANUP=true ;;
    --namespace)
      shift
      NAMESPACE=$1
      ;;
    -v | --verbose)
      set -x
      ;;
    --help)
      usage
      exit
      ;;
    *)
      usage
      exit 1
      ;;
    esac
    shift
  done
}

set_default_params
set_default_options
parse_args "$@"

# Detect the CRI to use, can be rootful podman or docker
detect_cri

set -euo pipefail

# Set defaults if no args were passed to script
if [ "${ARGCOUNT}" -eq "0" ]; then
  OPT_INSTALL_KIND=true
  OPT_INSTALL_KUBECTL=true
  OPT_CREATE_CLUSTER=true
  OPT_CONFIGURE_SECONDARY_NETWORK=true
  OPT_DEPLOY_KUBEVIRT=true
  OPT_DEPLOY_KUBEVIRT_COMMON_INSTANCETYPES=true
  OPT_DEPLOY_CNAO=true
  OPT_CREATE_NAD=true
fi

if [ "${OPT_CLEANUP}" == true ]; then
  cleanup
  exit 0
fi

if [ "${OPT_INSTALL_KIND}" == true ]; then
  install_kind
fi

if [ "${OPT_INSTALL_KUBECTL}" == true ]; then
  install_kubectl
fi

if [ "${OPT_CONFIGURE_INOTIFY_LIMITS}" == true ]; then
  configure_inotify_limits
fi

if [ "${OPT_CREATE_CLUSTER}" == true ]; then
  create_cluster
fi

if [ "${OPT_CONFIGURE_SECONDARY_NETWORK}" == true ]; then
  configure_secondary_network
fi

if [ "${OPT_DEPLOY_KUBEVIRT}" == true ]; then
  deploy_kubevirt
fi

if [ "${OPT_DEPLOY_KUBEVIRT_COMMON_INSTANCETYPES}" == true ]; then
  deploy_kubevirt_common_instancetypes
fi

if [ "${OPT_DEPLOY_CNAO}" == true ]; then
  deploy_cnao
fi

if [ "${OPT_CREATE_NAD}" == true ]; then
  create_nad
fi
