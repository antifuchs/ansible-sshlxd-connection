from __future__ import (absolute_import, division, print_function)

import os
import os.path
import pipes

from ansible.errors import AnsibleError
from ansible.plugins.connection.ssh import Connection as SSHConnection
from contextlib import contextmanager

__metaclass__ = type

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

class ConnectionBase(SSHConnection):
    pass


class Connection(ConnectionBase):
    ''' ssh based connections '''

    transport = 'sshlxc'

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)
        # self.host == containername@containerhost
        self.inventory_hostname = self.host
        self.containerspec, self.host = self.host.split('@', 1)
        # self.containerspec == containername
        # self.host == containerhost
        # this way SSHConnection parent class uses the containerhost as the SSH remote host

        self.connector = None

        # logging.warning(self._play_context.connection)

    def get_container_id(self):
        return self.containerspec

    def get_container_connector(self):
        return 'lxc'

    def _strip_sudo(self, executable, cmd):
        # Get the command without sudo
        sudoless = cmd.rsplit(executable + ' -c ', 1)[1]
        # Get the quotes
        quotes = sudoless.partition('echo')[0]
        # Get the string between the quotes
        cmd = sudoless[len(quotes):-len(quotes+'?')]
        # Drop the first command becasue we don't need it
        #cmd = cmd.split('; ', 1)[1]
        return cmd

    def host_command(self, cmd, do_become=False):
        if self._play_context.become and do_become:
            cmd = self._play_context.make_become_cmd(cmd)
        return super(Connection, self).exec_command(cmd, in_data=None, sudoable=True)

    def exec_command(self, cmd, in_data=None, executable='/bin/sh', sudoable=True):
        ''' run a command in the container '''

        cmd = '%s exec %s -- %s' % (self.get_container_connector(), self.get_container_id(), cmd)
        if self._play_context.become:
            # display.debug("_low_level_execute_command(): using become for this command")
            cmd = self._play_context.make_become_cmd(cmd)

        # display.vvv("CONTAINER (%s) %s" % (local_cmd), host=self.host)
        return super(Connection, self).exec_command(cmd, in_data, True)

    def container_path(self, path):
        return self.get_container_id() + path

    @contextmanager
    def tempfile(self):
        code, stdout, stderr = self.host_command('mktemp')
        if code != 0:
            raise AnsibleError("failed to make temp file:\n%s\n%s" % (stdout, stderr))
        tmp = stdout.strip().split('\n')[-1]

        yield tmp

        code, stdout, stderr = self.host_command(' '.join(['rm', tmp]))
        if code != 0:
            raise AnsibleError("failed to remove temp file %s:\n%s\n%s" % (tmp, stdout, stderr))

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to remote container '''
        with self.tempfile() as tmp:
            super(Connection, self).put_file(in_path, tmp)
            self.host_command(' '.join(['lxc', 'exec', self.get_container_id(), '--', 'mkdir', '-p', os.path.dirname(out_path)]), do_become=True)
            self.host_command(' '.join(['lxc', 'file', 'push', '--debug', tmp, self.container_path(out_path)]), do_become=True)

    def fetch_file(self, in_path, out_path):
        ''' fetch a file from remote to local '''
        with self.tempfile() as tmp:
            self.host_command(' '.join(['lxc', 'file', 'pull', self.container_path(in_path), tmp]), do_become=True)
            super(Connection, self).fetch_file(tmp, out_path)

    def close(self):
        ''' Close the connection, nothing to do for us '''
        super(Connection, self).close()
