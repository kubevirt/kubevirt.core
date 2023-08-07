# Lean Ansible bindings for KubeVirt
<!--start build_status -->
[![Build Status](https://github.com/kubevirt/kubevirt.core/workflows/CI/badge.svg?event=push)](https://github.com/kubevirt/kubevirt.core/actions)

> **_NOTE:_ If you are Red Hat customer, install `redhat.ocpv` from [Automation Hub](https://console.redhat.com/ansible/ansible-dashboard) as the certified version of this collection.**
<!--end build_status -->

This repository hosts the `kubevirt.core` Ansible Collection, which provides virtual machine operations and inventory source for use with Ansible.

<!--start requires_ansible-->
## Ansible version compatibility

This collection has been tested against following Ansible versions: **>=2.9.10**.
<!--end requires_ansible-->

## Included content

### Plugins

* `kubevirt`: inventory source for kubevirt virtual machines
* `kubevirt_vm`: create or delete kubevirt virtual machines

## Using this collection

<!--start galaxy_download -->
### Installing the Collection from Ansible Galaxy

Before using this collection, you need to install it with the Ansible Galaxy command-line tool:
```bash
ansible-galaxy collection install kubevirt.core
```
<!--end galaxy_download -->

### Build and install locally

Clone the repository, checkout the tag you want to build, or pick the main branch for the development version; then:
```bash
ansible-galaxy collection build .
ansible-galaxy collection install kubevirt-kubevirt.core-*.tar.gz
```

### Dependencies

#### Ansible collections

* [kubernetes.core](https://docs.ansible.com/ansible/latest/collections/kubernetes/core/index.html)

You can also include it in a `requirements.yml` file and install it with `ansible-galaxy collection install -r requirements.yml`, using the format:
```yaml
---
collections:
  - name: kubevirt.core
```

#### Python libraries

- kubernetes
- PyYaml
- jsonpatch
- jinja2

To install all the dependencies:
```bash
pip install -r requirements.txt
```

See [Ansible Using collections](https://docs.ansible.com/ansible/devel/user_guide/collections_using.html) for more details.

<!--start community_readme -->
## Code of Conduct

We follow the [KubeVirt Code of Conduct](https://github.com/kubevirt/kubevirt/blob/main/CODE_OF_CONDUCT.md).

## Contributing to this collection

The content of this collection is made by people like you, a community of individuals collaborating on making the world better through developing automation software.

We are actively accepting new contributors.

Any kind of contribution is very welcome.

You don't know how to start? Refer to our [contribution guide](CONTRIBUTING.md)!

We use the following guidelines:

* [CONTRIBUTING.md](CONTRIBUTING.md)
* [REVIEW_CHECKLIST.md](REVIEW_CHECKLIST.md)
* [Ansible Community Guide](https://docs.ansible.com/ansible/latest/community/index.html)
* [Ansible Development Guide](https://docs.ansible.com/ansible/devel/dev_guide/index.html)
* [Ansible Collection Development Guide](https://docs.ansible.com/ansible/devel/dev_guide/developing_collections.html#contributing-to-collections)

## Collection maintenance

The current maintainers are listed in the [OWNERS](OWNERS) file. If you have questions or need help, feel free to mention them in the proposals.

To learn how to maintain / become a maintainer of this collection, refer to the [Maintainer guidelines](https://docs.ansible.com/ansible/devel/community/maintainers.html).

## Governance

The process of decision making in this collection is based on discussing and finding consensus among participants.

Every voice is important. If you have something on your mind, create an issue or dedicated discussion and let's discuss it!
<!--end community_readme -->

<!--start support -->
<!--end support -->

## Licensing

GNU General Public License v3.0 or later.

See [LICENSE](./LICENSE) to see the full text.
