#!/usr/bin/env python3

from core import consts as mf_consts
from core import utils as core_utils
from core.config import Config
from core.pipeline_manager import PipelineManager
from core.termcolor import get_colored_text_by_hsv
from services.model_factory_frontend.client import ModelFactoryFrontendClient

import click
import os
import tabulate


@click.group(name="dev")
def dev():
    """
    Commands for daily development usage.
    """
    pass


@dev.command(name="install-alias")
def install_alias():
    """
    Install the mf alias.
    """
    # Checking k8s config.
    files_to_install = ["~/.bashrc", "~/.zshrc"]

    for file_to_install in files_to_install:
        lines_to_install = [
            "alias mf=\"PYTHONPATH={} python3 -m cli.mf\"".format(core_utils.get_model_factory_basedir()),
        ]

        rc_file = os.path.expanduser(file_to_install)

        if os.path.exists(rc_file):
            with open(rc_file, "r") as fp:
                for line in fp.readlines():
                    line = line.strip()

                    if line not in lines_to_install:
                        continue

                    lines_to_install.remove(line)

        with open(rc_file, "a") as fp:
            for line in lines_to_install:
                fp.write("{}\n".format(line))


@dev.command(name="container")
@click.argument("pipeline_name")
@click.option(
    "--memory-request", help="Memory requirements."
)
@click.option(
    "--gpu-request", type=int, help="GPU requirements."
)
def container(pipeline_name, memory_request, gpu_request):
    """
    Start a container which has the same execution environment as the production job.

    This command maps your local repo into the container. You can develop your pipeline code on your devbox, and run it in the container as a process.
    """
    pipeline = PipelineManager.get_pipeline(pipeline_name)
    main_operator = PipelineManager.get_operator_by_id(pipeline.main_operator_id)

    memory_request = memory_request or main_operator.memory_request

    if not pipeline:
        print("Pipeline {} not found!".format(pipeline_name))
        return

    print("Create dev container based on image {}".format(pipeline.docker_base_image))

    cmd = (
        "docker pull {}/model_factory_base_image && "
        "docker build {} -f {}/docker/{}.dockerfile -t {} --build-arg DOCKER_REGISTRY={} && "
        "docker run -m {} --privileged {} --network=host -it -v /var/run/docker.sock:/var/run/docker.sock "
        "-v {}:/model-factory/src -v {}/.ssh/id_rsa:/root/.ssh/id_rsa "
        "-v {}/.ssh/ml-infra-devvm.pem:/root/.ssh/ml-infra-devvm.pem {}"
    ).format(
        Config.DOCKER_REGISTRY,
        core_utils.get_model_factory_basedir(),
        core_utils.get_model_factory_basedir(),
        pipeline.docker_base_image,
        pipeline.docker_base_image,
        Config.DOCKER_REGISTRY,
        memory_request,
        "--gpus=all" if (
            (gpu_request is None and main_operator.gpu_request > 0) or
            (gpu_request is not None and gpu_request > 0)
        ) else "",
        core_utils.get_model_factory_basedir(),
        os.environ["HOME"],
        os.environ["HOME"],
        pipeline.docker_base_image,
    )

    os.system(cmd)
