"""
Copyright (c) 2015 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the BSD license. See the LICENSE file for details.


Include user-provided Dockerfile in the /root/buildinfo/
(or other if provided) directory in the built image.
This is accomplished by appending an ADD command to it.
Name of the Dockerfile is changed to include N-V-R of the build.
N-V-R is specified either by nvr argument OR from
Name/Version/Release labels in Deckerfile.
If you run add_labels_in_dockerfile to add Name/Version/Release labels
you have to run it BEFORE this one.


Example configuration:
{
    'name': 'add_dockerfile',
    'args': {'nvr': 'rhel-server-docker-7.1-20'}
}

or

[{
   'name': 'add_labels_in_dockerfile',
   'args': {'labels': {'Name': 'jboss-eap-6-docker',
                       'Version': '6.4',
                       'Release': '77'}}
},
{
   'name': 'add_dockerfile'
}]

"""

import os
from dock.constants import DOCKERFILE_FILENAME
from dock.util import get_labels_from_dockerfile
from dock.plugin import PreBuildPlugin


class AddDockerfilePlugin(PreBuildPlugin):
    key = "add_dockerfile"

    def __init__(self, tasker, workflow, nvr=None, destdir="/root/buildinfo/"):
        """
        constructor

        :param tasker: DockerTasker instance
        :param workflow: DockerBuildWorkflow instance
        :param nvr: name-version-release, will be appended to Dockerfile-.
                    If not specified, try to get it from Name, Version, Release labels.
        :param destdir: directory in the image to put Dockerfile-N-V-R into
        """
        # call parent constructor
        super(AddDockerfilePlugin, self).__init__(tasker, workflow)
        if nvr is None:
            labels = get_labels_from_dockerfile(self.workflow.builder.df_path)
            name = labels.get('Name')
            version = labels.get('Version')
            release = labels.get('Release')
            if name is None or version is None or release is None:
                raise ValueError("You have to specify either nvr arg or Name/Version/Release labels.")
            nvr = "{0}-{1}-{2}".format(name, version, release)
        self.df_name = '{0}-{1}'.format(DOCKERFILE_FILENAME, nvr)
        self.df_dir = destdir
        self.df_path = os.path.join(self.df_dir, self.df_name)

    def run(self):
        """
        run the plugin
        """
        with open(self.workflow.builder.df_path, 'r') as fp:
            lines = fp.readlines()

        content = 'ADD {0} {1}'.format(DOCKERFILE_FILENAME, self.df_path)

        # put it before last instruction
        lines.insert(-1, content + '\n')

        with open(self.workflow.builder.df_path, 'w') as fp:
            fp.writelines(lines)

        self.log.info("Added %s", self.df_path)

        return content
