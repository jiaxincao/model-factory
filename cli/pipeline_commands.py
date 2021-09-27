from core import consts as mf_consts
from core import utils as core_utils
from core.config import Config
from core.parameter import Parameter, ParameterGroup
from core.pipeline_manager import PipelineManager
from core.termcolor import get_colored_text_by_hsv
from treelib import Tree
import click
import os


@click.group(name="pipeline")
def pipeline():
    """
    Commands to access model factory pipeline information.
    """
    pass


@pipeline.command(name="create")
@click.argument("pipeline_name")
@click.option("--docker_base_image_name", help="The docker base image name. If not specific, {pipeline_name}_base_image will be used.")
def create_pipeline(pipeline_name, docker_base_image_name):
    """
    Create a completely new pipeline.
    """
    docker_base_image_name = docker_base_image_name or "{}_base_image".format(pipeline_name)

    # Validate names
    def validate_name(name):
        for ch in name:
            if not ('a' <= ch <= 'z' or '0' <= ch <= '9' or ch == '_'):
                raise Exception("Only lower case letter, digits or '_' are allowed in names!")

    validate_name(pipeline_name)
    validate_name(docker_base_image_name)

    # Create docker base image file if it does not exist yet.
    docker_base_image_file_path = os.path.join(
        core_utils.get_model_factory_basedir(),
        "docker",
        "{}.dockerfile".format(docker_base_image_name),
    )

    if os.path.exists(docker_base_image_file_path):
        print(get_colored_text_by_hsv(
            0.3, 0.8, 0.8, "* Base image dockerfile already exists: {}".format(
                get_colored_text_by_hsv(0.1, 0.8, 0.8, docker_base_image_file_path)
            )
        ))
    else:
        with open(docker_base_image_file_path, 'w') as fp:
            fp.write((
                "################################################################################\n"
                "# Section 1: Parent Image\n"
                "################################################################################\n"
                "ARG DOCKER_REGISTRY\n"
                "FROM {}/model_factory_base_image\n"
                "\n"
                "\n"
                "################################################################################\n"
                "# Section 2: Pipeline Custom Package Installation\n"
                "################################################################################\n"
                "\n"
                "# If you need any packages or special setup for your pipeline, please put them in section 2.\n"
                "\n"
                "\n"
                "################################################################################\n"
                "# Section 3: Set up environment variables\n"
                "################################################################################\n"
                "RUN echo \"export PYTHONPATH='/model-factory/src'\" >> /root/.bashrc\n"
                "ENV PYTHONPATH='/model-factory/src'\n"
            ).format(Config.DOCKER_REGISTRY))
        print(get_colored_text_by_hsv(
            0.3, 0.8, 0.8, "* Base image dockerfile successfully created: {}".format(
                get_colored_text_by_hsv(0.1, 0.8, 0.8, docker_base_image_file_path)
            ),
        ))

    # Create pipeline __init__.py file if it does not exist yet.
    pipeline_dir = os.path.join(
        core_utils.get_model_factory_basedir(),
        "pipelines",
        pipeline_name,
    )

    os.makedirs(name=pipeline_dir, exist_ok=True)

    pipeline_init_file_path = os.path.join(
        pipeline_dir,
        "__init__.py",
    )
    if os.path.exists(pipeline_init_file_path):
        print(get_colored_text_by_hsv(
            0.3, 0.8, 0.8, "* Pipeline init file already exists: {}".format(
                get_colored_text_by_hsv(0.1, 0.8, 0.8, pipeline_init_file_path)
            )
        ))
    else:
        with open(pipeline_init_file_path, 'w') as fp:
            fp.write((
                "from core.operator import Operator\n"
                "from core.parameter import Parameter, ParameterGroup\n"
                "from core.pipeline import Pipeline\n"
                "\n"
                "\n"
                "PIPELINE = Pipeline(\n"
                "    name=\"{}\",\n"
                "    docker_base_image = \"{}\",\n"
                "    main_operator_id = \"pipelines.{}.main.main\",\n"
                ")\n"
                "\n"
                "OPERATORS = [\n"
                "    Operator(\n"
                "        operator_id=\"pipelines.{}.main.main\",\n"
                "        input_schema=[\n"
                "        ],\n"
                "    ),\n"
                "]\n"
            ).format(
                pipeline_name,
                docker_base_image_name,
                pipeline_name,
                pipeline_name,
            ))
        print(get_colored_text_by_hsv(
            0.3, 0.8, 0.8, "* Pipeline init file successfully created: {}".format(
                get_colored_text_by_hsv(0.1, 0.8, 0.8, pipeline_init_file_path)
            )
        ))

    # Create pipeline main.py file if it does not exist yet.
    pipeline_main_file_path = os.path.join(
        pipeline_dir,
        "main.py",
    )
    if os.path.exists(pipeline_main_file_path):
        print(get_colored_text_by_hsv(
            0.3, 0.8, 0.8, "* Pipeline main file already exists: {}".format(
                get_colored_text_by_hsv(0.1, 0.8, 0.8, pipeline_main_file_path)
            )
        ))
    else:
        with open(pipeline_main_file_path, 'w') as fp:
            fp.write((
                "################################################################################\n"
                "# Pipeline imports and global initializations.\n"
                "################################################################################\n"
                "import logging\n"
                "\n"
                "\n"
                "################################################################################\n"
                "# Pipeline code.\n"
                "################################################################################\n"
                "def main(params):\n"
                "    logging.info(\"Start executing pipeline {}\")\n"
                "\n"
                "    # Please start implementing your pipeline logics from here.\n"
            ).format(
                pipeline_name,
            ))
        print(get_colored_text_by_hsv(
            0.3, 0.8, 0.8, "* Pipeline main file successfully created: {}".format(
                get_colored_text_by_hsv(0.1, 0.8, 0.8, pipeline_main_file_path)
            )
        ))

    print((
        "\nCongrats! Your pipeline {} has been successfully created! You can take the following steps to continue:\n"
        "{}: if you need any more package for your pipeline, do it in your dockerfile {}\n"
        "{}: implement your pipeline logics in {}\n"
        "{}: debug your pipeline with \"{}\" and \"{}\"\n"
        "{}: submit a pipeline job by running \"{}\"\n"
    ).format(
        get_colored_text_by_hsv(0.45, 0.8, 0.8, pipeline_name),
        get_colored_text_by_hsv(0.15, 0.8, 0.8, "* Step 1"),
        get_colored_text_by_hsv(0.1, 0.8, 0.8, docker_base_image_file_path),
        get_colored_text_by_hsv(0.15, 0.8, 0.8, "* Step 2"),
        get_colored_text_by_hsv(0.1, 0.8, 0.8, pipeline_main_file_path),
        get_colored_text_by_hsv(0.15, 0.8, 0.8, "* Step 3"),
        get_colored_text_by_hsv(0.45, 0.8, 0.8, "mf dev container {}".format(pipeline_name)),
        get_colored_text_by_hsv(0.45, 0.8, 0.8, "mf job create {} --mode inplace".format(pipeline_name)),
        get_colored_text_by_hsv(0.15, 0.8, 0.8, "* Step 4"),
        get_colored_text_by_hsv(0.45, 0.8, 0.8, "mf job create {}".format(pipeline_name)),
    ))


@pipeline.command(name="list")
def list_pipelines():
    """
    Show the pipeline basic information.
    """
    pipelines = PipelineManager.get_all_pipelines()

    for pipeline in pipelines:
        print("* {} (base_image=\"{}\")".format(
            get_colored_text_by_hsv(0.45, 0.8, 0.8, pipeline.name),
            get_colored_text_by_hsv(0.1, 0.8, 0.8, pipeline.docker_base_image),
        ))


@pipeline.command(name="build-image")
@click.argument("pipeline_name")
@click.option("--image-tag", help="The image tag.")
@click.option("--no-push", is_flag=True, help="Whether to push the image to the docker registry.")
def build_image(pipeline_name, image_tag, no_push):
    """
    Build a image for a pipeline.
    """
    core_utils.build_image(
        pipeline_name=pipeline_name,
        image_tag=image_tag,
        push=not no_push,
    )
