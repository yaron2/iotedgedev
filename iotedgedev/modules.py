import os
import requests
from shutil import copyfile

from .module import Module
from .modulesprocessorfactory import ModulesProcessorFactory


class Modules:
    def __init__(self, envvars, utility, output, dock):
        self.envvars = envvars
        self.utility = utility
        self.utility.set_config()
        self.output = output
        self.dock = dock
        self.dock.init_registry()

    def build(self):
        self.build_push(no_push=True)

    def push(self, no_build=False):
        self.build_push(no_build=no_build)

    def build_push(self, no_build=False, no_push=False):

        self.output.header("BUILDING MODULES", suppress=no_build)

        # Get all the modules to build as specified in config.
        modules_to_process = self.utility.get_active_modules()

        for module in os.listdir(self.envvars.MODULES_PATH):

            if len(modules_to_process) == 0 or modules_to_process[0] == "*" or module in modules_to_process:

                module_dir = os.path.join(self.envvars.MODULES_PATH, module)

                self.output.info("BUILDING MODULE: {0}".format(module_dir), suppress=no_build)

                module_json = Module(self.output, self.utility, os.path.join(module_dir, "module.json"))
                mod_proc = ModulesProcessorFactory(self.envvars, self.utility, self.output, module_dir).get(module_json.language)

                # build module
                if not no_build:
                    if not mod_proc.build():
                        continue

                docker_arch_process = [docker_arch.strip() for docker_arch in self.envvars.ACTIVE_DOCKER_PLATFORMS.split(",") if docker_arch]

                for arch in module_json.platforms:
                    if len(docker_arch_process) == 0 or docker_arch_process[0] == "*" or arch in docker_arch_process:

                        # get the docker file from module.json
                        docker_file = module_json.get_platform_by_key(arch)

                        self.output.info("PROCESSING DOCKER FILE: " + docker_file, suppress=no_build)

                        docker_file_name = os.path.basename(docker_file)
                        container_tag = "" if self.envvars.CONTAINER_TAG == "" else "-" + self.envvars.CONTAINER_TAG
                        tag_name = module_json.tag_version + container_tag

                        # publish module
                        if not no_build:
                            self.output.info("PUBLISHING MODULE: " + module_dir)
                            mod_proc.publish()

                        image_destination_name = "{0}/{1}:{2}-{3}".format(self.envvars.CONTAINER_REGISTRY_SERVER, module, tag_name, arch).lower()

                        self.output.info("BUILDING DOCKER IMAGE: " + image_destination_name, suppress=no_build)

                        # cd to the module folder to build the docker image
                        project_dir = os.getcwd()
                        os.chdir(os.path.join(project_dir, module_dir))

                        # BUILD DOCKER IMAGE

                        if not no_build:
                            build_result = self.dock.docker_client.images.build(tag=image_destination_name, path=".", dockerfile=docker_file_name, buildargs={"EXE_DIR": mod_proc.exe_dir})

                            self.output.info("DOCKER IMAGE DETAILS: {0}".format(build_result))

                        # CD BACK UP
                        os.chdir(project_dir)

                        if not no_push:
                            # PUSH TO CONTAINER REGISTRY
                            self.output.info("PUSHING DOCKER IMAGE TO: " + image_destination_name)

                            for line in self.dock.docker_client.images.push(repository=image_destination_name, stream=True, auth_config={
                                                                            "username": self.envvars.CONTAINER_REGISTRY_USERNAME, "password": self.envvars.CONTAINER_REGISTRY_PASSWORD}):
                                self.output.procout(self.utility.decode(line).replace("\\u003e", ">"))

                self.output.footer("BUILD COMPLETE", suppress=no_build)
                self.output.footer("PUSH COMPLETE", suppress=no_push)