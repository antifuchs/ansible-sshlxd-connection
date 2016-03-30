# ansible-sshlxd-connection

An Ansible 2.0 connection plugin that allows you to access LXD
containers remotely through SSH.

The `sshlxd` plugin uses SSH, `sudo` and `lxc exec` (along with `lxc
file pull` and `lxc file push`) on the remote host to run ansible
plays on an LXD container running on a remote host. It's really useful
if you have a Mac and want to provision a Linux server with containers
on it (otherwise you could just use any old LXD connection plugin and
use remote containers, I guess).

It's tested with Ansible 2.0.1 and the Ubuntu Xenial (16.04) beta.

## Requirements

Machine running ansible:

* Ansible 2.0 and its dependencies

Host:

* Linux
* LXD, tested with the version Ubuntu Xenial ships with
* SSH
* Sudo
* Ansible 2.0's dependencies (that's probably python 2.7)

LXD container:

* Ansible 2.0's dependencies (that's probably python 2.7 again)

## Installing

This is a Connection Type Plugin. The installation procedure is simple
(but you can't do it via Galaxy, sadly): Put (or link) sshlxd.py in
your ansible playbooks' `connection_plugins/` directory, and add
Inventory entries, e.g.:

```
[db]
my-db-jail@127.0.0.1 ansible_ssh_port=2222 ansible_connection=sshlxd ansible_ssh_user=vagrant
```

As you can see, the format here is relatively simple - the jail name
goes in the portion before the @ in the host name, the host name goes
after. Give SSH parameters with `ansible_ssh_*` params.

To give `sshlxd` the privileges it needs to `lxd exec`, you have to
use `become: true` in the play for the container.

In theory, you can also add hosts dynamically via the `add_host`
module, but I haven't tried this yet.

## Credit

This plugin owes pretty much everything to
[ansible-sshjail](https://github.com/austinhyde/ansible-sshjail) - it
started life as a copy of that code (and still retains most of its
heritage!). Thanks to @austinhyde for making this!
