# -*- coding: ascii -*-
#
# Copyright 2019 - 2025
# Andr\xe9 Malo or his licensors, as applicable
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
"""
Containerized Builds
~~~~~~~~~~~~~~~~~~~~

"""

import platform as _platform


class Container(object):
    """Container context"""

    _WAIT_COMMAND = ("/bin/sh", "-c", "while sleep 60; do :; done")

    def __init__(self, ctx, name, image):
        """
        Initialization

        Parameters:
          ctx (Context):
            Context object

          name (str):
            Container name

          image (str):
            Image

          login (callable):
            Login function
        """
        self._ctx = ctx
        # pylint: disable-next = condition-evals-to-constant
        if 0 and _platform.system() == "Darwin" and ctx.which("container"):
            self._command = ContainerCommand(ctx)
        else:
            self._command = DockerCommand(ctx)
        self._image = image
        self._name = name
        self._running = False

    def login(self):
        """Login to registry if needed"""

    def __enter__(self):
        """
        Create packager context

        * Login if requested
        * remove existing container
        * start new container

        Returns:
          Packager: The instance again
        """
        assert not self._running

        self.login()
        self._run(self._command.delete(self._name), warn=True, hide=True)

        self._run(
            self._command.run(
                self._image,
                name=self._name,
                detached=True,
                command=self._WAIT_COMMAND,
            )
        )

        self._running = True
        return self

    def __exit__(self, *args):
        """
        Exit packager context

        * stop the container
        * delete the container
        """
        try:
            kwargs = dict(hide=True, warn=True)
            self._run(self._command.stop(self._name), **kwargs)
            self._run(self._command.delete(self._name), **kwargs)
        finally:
            self._running = False

    def _run(self, command, **kwargs):
        """
        Run command

        Parameters:
          command (list):
            The command to run

        **kwargs:
          Extra arguments for ``ctx.run()``

        Returns:
          ctx.run() response
        """
        ctx = self._ctx
        kwargs.setdefault("echo", True)
        return ctx.run(ctx.c(command), **kwargs)

    def cp_in(self, src, dest):
        """
        cp files into the container

        Parameters:
          src (str):
            Source file or folder

          dest (str):
            Destination in the container
        """
        assert self._running

        self._run(self._command.cp_in(self._name, src, dest))

    def cp_out(self, src, dest):
        """
        cp files out of the container

        Parameters:
          src (str):
            Source file or folder within the container

          dest (str):
            Destination in the local file system
        """
        assert self._running

        self._run(self._command.cp_out(self._name, src, dest))

    def execute(self, command):
        """
        Execute a command in the running container

        Parameters:
          command (list):
            The command to execute
        """
        assert self._running

        self._run(self._command.execute(self._name, command))


class DockerCommand(object):
    """Docker command creator"""

    def __init__(self, ctx):
        """Initialization"""
        self._exe = ctx.which("docker")
        self._ctx = ctx
        self._email_args = (
            ["-e", "none"]
            if "--email"
            in ctx.run(
                ctx.c([self._exe, "login", "--help"]), hide=True
            ).stdout
            else []
        )

    def login(self, url, username):
        """
        Return login command

        Password needs to be passed via stdin

        Parameters:
          url (str):
            Registry URL

          username (str):
            User name

        Returns:
          list: The command
        """
        cmd = [self._exe, "login"] + self._email_args + ["--password-stdin"]
        cmd += ["-u", username]
        cmd += ["--", url]
        return cmd

    def delete(self, container):
        """
        Create command to delete a container

        Parameters:
          container (str):
            The container name

        Returns:
          list: The command
        """
        return [self._exe, "rm", "-f", "--", container]

    def stop(self, container):
        """
        Create command to stop a container

        Parameters:
          container (str):
            The container name

        Returns:
          list: The command
        """
        return [self._exe, "stop", "--", container]

    def run(
        self,
        image,
        name=None,
        detached=None,
        command=None,
        remove=None,
        privileged=False,
    ):
        """
        Create run command

        Parameters:
          image (str):
            The image to run

          name (str):
            Optional container name

          detached (bool):
            Run detached? Default: False

          command (list):
            Optional in-container command to execute

          remove (bool):
            Remove after stop? Default: false

          privileged (bool):
            Run privileged? Default: false

        Returns:
          list: The command
        """
        cmd = [self._exe, "run"]
        if detached:
            cmd += ["-d"]
        if name:
            cmd += ["--name", name]
        if remove:
            cmd += ["--rm"]
        if privileged:
            cmd += ["--privileged"]
        cmd += [image]
        if command:
            cmd += list(command)
        return cmd

    def cp_in(self, container, src, dest):
        """
        Create command to copy files into a container

        Parameters:
          container (str):
            The container name

          src (str):
            Source file or folder

          dest (str):
            Destination in the container

        Returns:
          list: The command
        """
        cmd = [self._exe, "container", "cp"]
        cmd += [src]
        cmd += ["%s:%s" % (container, dest)]
        return cmd

    def cp_out(self, container, src, dest):
        """
        Create command to copy files out of the container

        Parameters:
          src (str):
            Source file or folder within the container

          dest (str):
            Destination in the local file system
        """
        cmd = [self._exe, "container", "cp"]
        cmd += ["%s:%s" % (container, src)]
        cmd += [dest]
        return cmd

    def execute(self, container, command, interactive=True):
        """
        Create command to execute a command in the running container

        Parameters:
          container (str):
            Container name

          command (list):
            The command to execute

          interactive (bool):
            Run interactively? Default: true
        """
        cmd = [self._exe, "exec"]
        if interactive:
            cmd += ["-i"]
        cmd += [container]
        cmd.extend(command)
        return cmd


class ContainerCommand(object):
    """Apple container command creator"""

    def __init__(self, ctx):
        """Initialization"""
        self._exe = ctx.which("container")
        self._ctx = ctx

    def login(self, url, username):
        """
        Return login command

        Password needs to be passed via stdin

        Parameters:
          url (str):
            Registry URL

          username (str):
            User name

        Returns:
          list: The command
        """
        cmd = [self._exe, "registry", "login", "--password-stdin"]
        cmd += ["-u", username]
        cmd += ["--", url]
        return cmd

    def delete(self, container):
        """
        Create command to delete a container

        Parameters:
          container (str):
            The container name

        Returns:
          list: The command
        """
        return [self._exe, "delete", "-f", "--", container]

    def stop(self, container):
        """
        Create command to stop a container

        Parameters:
          container (str):
            The container name

        Returns:
          list: The command
        """
        return [self._exe, "stop", "--", container]

    def run(
        self,
        image,
        name=None,
        detached=None,
        command=None,
        remove=None,
        privileged=None,
    ):
        """
        Create run command

        Parameters:
          image (str):
            The image to run

          name (str):
            Optional container name

          detached (bool):
            Run detached? Default: False

          command (list):
            Optional in-container command to execute

          remove (bool):
            Remove after stop? Default: false

          privileged (bool):
            Run privileged? Default: false


        Returns:
          list: The command
        """
        cmd = [self._exe, "run"]
        if detached:
            cmd += ["-d"]
        if name:
            cmd += ["--name", name]
        if remove:
            cmd += ["--rm"]
        if privileged:
            cmd += ["--privileged"]
        cmd += [image]
        if command:
            cmd += list(command)
        return cmd

    def cp_in(self, container, src, dest):
        """
        Copy files into a container

        Parameters:
          container (str):
            The container name

          src (str):
            Source file or folder

          dest (str):
            Destination in the container

        Returns:
          list: The command
        """
        # TODO: probably wrong
        cmd = [self._exe, "container", "cp"]
        cmd += [src]
        cmd += ["%s:%s" % (container, dest)]
        return cmd

    def cp_out(self, container, src, dest):
        """
        Create command to copy files out of the container

        Parameters:
          src (str):
            Source file or folder within the container

          dest (str):
            Destination in the local file system
        """
        # TODO: probably wrong
        cmd = [self._exe, "container", "cp"]
        cmd += ["%s:%s" % (container, src)]
        cmd += [dest]
        return cmd

    def execute(self, container, command, interactive=True):
        """
        Create command to execute a command in the running container

        Parameters:
          container (str):
            Container name

          command (list):
            The command to execute

          interactive (bool):
            Run interactively? Default: true
        """
        cmd = [self._exe, "exec"]
        if interactive:
            cmd += ["-i"]
        cmd += [container]
        cmd.extend(command)
        return cmd
