from core import consts
from core.config import Config
from core.execution_context import ExecutionContext
from core.parameter import Parameter, ParameterGroup
from core.termcolor import get_colored_text_by_hsv
from core.tracking import Tracking
from datetime import datetime
from services.model_factory_frontend.client import ModelFactoryFrontendClient

import docker
import getpass
import logging
import os
import pytz
import requests
import uuid


def get_first_available_value(values):
    for value in values:
        if value is not None:
            return value


def get_current_cpu_request():
    current_job_info = Tracking.get_info_for_single_job(ExecutionContext.job_id)
    return current_job_info["resources"]["cpu_request"]


def get_current_memory_request():
    current_job_info = Tracking.get_info_for_single_job(ExecutionContext.job_id)
    return current_job_info["resources"]["memory_request"]


def get_current_storage_request():
    current_job_info = Tracking.get_info_for_single_job(ExecutionContext.job_id)
    return current_job_info["resources"]["storage_request"]


def get_current_gpu_request():
    current_job_info = Tracking.get_info_for_single_job(ExecutionContext.job_id)
    return current_job_info["resources"]["gpu_request"]



def get_utc_time_from_timestamp(ts):
    if ts is None:
        return None

    return datetime.utcfromtimestamp(ts).replace(tzinfo=pytz.utc, microsecond=0)


def get_docker_image_fullname(docker_image_repo, docker_image_tag, docker_image_digest=None):
    docker_image_fullname = "{}{}".format(
        docker_image_repo,
        ":{}".format(docker_image_tag) if docker_image_tag else ""
    )

    if docker_image_digest:
        docker_image_fullname += "@{}".format(docker_image_digest)

    return docker_image_fullname


def get_model_factory_basedir():
    return os.path.dirname(os.path.dirname(__file__))


def get_size_in_str(size):
    size = int(size)

    kb = 1024;
    mb = kb * 1024;
    gb = mb * 1024;
    tb = gb * 1024;

    if size>=tb:
        return "{:.2f} TB".format(float(size / tb))
    if size>=gb:
        return "{:.2f} GB".format(float(size / gb))
    if size>=mb:
        return "{:.2f} MB".format(float(size / mb))
    if size>=kb:
        return "{:.2f} KB".format(float(size / kb))


def get_docker_image_digest(image_tag):
    client = docker.from_env()
    image_data = client.images.get_registry_data(image_tag)
    return image_data.attrs['Descriptor']['digest']


def pull_docker_image(image_name):
    client = docker.from_env()
    image = client.images.pull(image_name)
    return image.id


def system(cmd):
    logging.info("Executing command: {}".format(cmd))
    assert os.system(cmd) == 0


def move(src_file, dst_file):
    if os.path.exists(dst_file):
        logging.info("Removing {}".format(dst_file))
        os.remove(dst_file)

    logging.info("Moving {} to {}".format(src_file, dst_file))
    os.rename(src_file, dst_file)


def pipe(src_file, dst_file, pipe_cmd):
    if src_file == dst_file:
        prepipe_file = "{}.prepipe".format(src_file)
        system(f"mv {src_file} {prepipe_file} && cat {prepipe_file} | {pipe_cmd} > {dst_file} && rm -f {prepipe_file}")
    else:
        system("cat {} | {} > {}".format(src_file, pipe_cmd, dst_file))


def pipe_with_tee(src_file, dst_file, pipe_cmd):
    if src_file == dst_file:
        prepipe_file = "{}.prepipe".format(src_file)
        system(f"mv {src_file} {prepipe_file} && cat {prepipe_file} | {pipe_cmd} | tee {dst_file} && rm -f {prepipe_file}")
    else:
        system("cat {} | {} | tee {}".format(src_file, pipe_cmd, dst_file))


def pipe_with_append(src_file, dst_file, pipe_cmd):
    if src_file == dst_file:
        prepipe_file = "{}.prepipe".format(src_file)
        system(f"mv {src_file} {prepipe_file} && cat {prepipe_file} | {pipe_cmd} >> {dst_file} && rm -f {prepipe_file}")
    else:
        system("cat {} | {} >> {}".format(src_file, pipe_cmd, dst_file))


def get_current_user():
    return getpass.getuser()


def yes_or_no_question(question):
    while True:
        answer = str(
            input("{}, please enter yes/no: ".format(
                question))).lower().strip()
        if answer not in ['yes', 'no']:
            print('Please input with yes or no!')
        else:
            break
    if answer == 'yes':
        return True
    if answer == 'no':
        return False


def construct_params(operator_input_schema, operator_params, allow_extra_keys=True, pass_extra_keys=False):
    params = {} if not pass_extra_keys else operator_params

    # Fill in params from the pipeline params schema default values.
    mandatory_fields = set()
    def fill_params_based_on_schema(param_node, operator_input_schema, key_path):
        for param in operator_input_schema:
            if pass_extra_keys and param.name in param_node:
                continue

            if isinstance(param, Parameter):
                param_node[param.name] = param.default

                if param.mandatory:
                    mandatory_fields.add(".".join(key_path + [param.name]))
            elif isinstance(param, ParameterGroup):
                sub_params = {}
                param_node[param.name] = sub_params
                fill_params_based_on_schema(sub_params, param.parameters, key_path + [param.name])

    fill_params_based_on_schema(params, operator_input_schema, [])

    # Fill in the parmas with the pass in operator_params.
    filled_fields = set()
    def fill_params_based_on_input(param_node, input_param_node, key_path):
        for k, v in input_param_node.items():
            if k not in param_node:
                if allow_extra_keys:
                    raise Exception((
                        "Input does not take config for key path \"{}\"! "
                    ).format(".".join(key_path + [k])))
                else:
                    continue

            if not isinstance(v, dict):
                param_node[k] = v
                filled_fields.add(".".join(key_path + [k]))
            else:
                assert isinstance(param_node[k], dict)
                fill_params_based_on_input(param_node[k], v, key_path + [k])

    fill_params_based_on_input(params, operator_params, [])

    # Make sure all mandatory fields are filled.
    missing_fields = mandatory_fields - filled_fields
    assert not missing_fields, "The following mandatory json input keys are missing: \n{}".format(
        "\n".join(["* {}".format(field) for field in sorted(missing_fields)])
    )

    return params


def create_job(
    pipeline_name,
    pipeline_params,
    execution_mode=consts.EXECUTION_MODE_K8S,
    pool=None,
    docker_image_repo=None,
    docker_image_tag=None,
    docker_image_digest=None,
    operator_id=None,
    owner=None,
    tags=None,
    cpu_request=None,
    memory_request=None,
    storage_request=None,
    gpu_request=None,
    ttl_after_finished=None,
    parent_job_id=None,
    active_deadline_seconds=None,
):
    from core.dockerfile_generator import generate_pipeline_dockerfile
    from core.pipeline_manager import PipelineManager

    # Read pipeline resource request if the pipeline code is found in the current binary.
    pipeline = PipelineManager.try_get_pipeline(pipeline_name)
    if pipeline:
        # If operator is provided, use it. Otherwise, use the pipeline main operator.
        operator_id = get_first_available_value([operator_id, pipeline.main_operator_id])
        operator = PipelineManager.get_operator_by_id(operator_id)

        cpu_request = get_first_available_value([cpu_request, operator.cpu_request])
        memory_request = get_first_available_value([memory_request, operator.memory_request])
        storage_request = get_first_available_value([storage_request, operator.storage_request])
        gpu_request = get_first_available_value([gpu_request, operator.gpu_request])
        pool = get_first_available_value([pool, operator.pool])
    else:
        cpu_request = get_first_available_value([cpu_request, consts.DEFAULT_CPU_REQUEST])
        memory_request = get_first_available_value([memory_request, consts.DEFAULT_MEMORY_REQUEST])
        storage_request = get_first_available_value([storage_request, consts.DEFAULT_STORAGE_REQUEST])
        gpu_request = get_first_available_value([gpu_request, consts.DEFAULT_GPU_REQUEST])
        pool = get_first_available_value([pool, consts.DEFAULT_POOL])

    assert operator_id, "Failed to get the operator_id!"

    # Prepare the job.
    job_id = "j-{}".format(uuid.uuid4())
    cmd = PipelineManager.get_operator_cmd(
        job_id=job_id,
        operator_id=operator_id,
        cpu=cpu_request,
        operator_params=pipeline_params,
        execution_mode=execution_mode,
    )

    # If the execution mode is inplace, run the job directly.
    if execution_mode == consts.EXECUTION_MODE_INPLACE:
        print(get_colored_text_by_hsv(0, 0.8, 0.8, (
            "****************************************************************************************************\n"
            "* Note that inplace mode jobs are NOT FULLY TRACKED, and will not be able to be reproduced later!  *\n"
            "* Please only use inplace mode for debugging purpose, DO NOT use it for model training purpose.    *\n"
            "****************************************************************************************************\n"
        )))
        return os.system(cmd)

    # Build the docker image if needed.
    if docker_image_repo:
        docker_image_fullname = get_docker_image_fullname(docker_image_repo, docker_image_tag)
    else:
        docker_image_repo = "{}/{}".format(Config.DOCKER_REGISTRY, pipeline_name)
        docker_image_tag = job_id

        docker_image_fullname = "{}:{}".format(docker_image_repo, docker_image_tag)

        # Pulling the base image.
        print(get_colored_text_by_hsv(0.4, 0.8, 0.8, "Pulling base image..."))
        assert not os.system("docker pull {}/model_factory_base_image".format(Config.DOCKER_REGISTRY))

        # Build the new image.
        print(get_colored_text_by_hsv(0.4, 0.8, 0.8, "Building job image..."))
        job_image_dockerfile = generate_pipeline_dockerfile(
            pipeline_name=pipeline_name,
        )
        assert not os.system("docker build {} -f {} -t {} --build-arg DOCKER_REGISTRY={}".format(
            get_model_factory_basedir(),
            job_image_dockerfile,
            docker_image_fullname,
            Config.DOCKER_REGISTRY,
        ))

        print(get_colored_text_by_hsv(0.4, 0.8, 0.8, "Uploading pipeline..."))
        assert not os.system("docker push {}".format(docker_image_fullname))

    # Register job.
    model_factory_frontend_client = ModelFactoryFrontendClient()
    model_factory_frontend_client.register_job(
        job_id=job_id,
        parent_job_id=parent_job_id,
        pipeline_name=pipeline_name,
        pipeline_params=pipeline_params,
        operator_id=operator_id,
        pool=pool,
        owner=owner,
        docker_image_repo=docker_image_repo,
        docker_image_tag=docker_image_tag,
        docker_image_digest=docker_image_digest or get_docker_image_digest(docker_image_fullname),
        execution_mode=execution_mode,
        tags=tags,
        creator_host=None,
        cmd=cmd,
        cpu_request=cpu_request,
        memory_request=memory_request,
        storage_request=storage_request,
        gpu_request=gpu_request,
        ttl_after_finished=ttl_after_finished,
    )

    # Create job.
    if execution_mode == consts.EXECUTION_MODE_LOCAL:
        print(get_colored_text_by_hsv(0.4, 0.8, 0.8, "Executing job {}...".format(job_id)))
        os.system(
            "docker run -m {} -v /var/run/docker.sock:/var/run/docker.sock --privileged {} -it {} {}".format(
                memory_request,
                "--gpus=all" if gpu_request else "",
                docker_image_fullname,
                cmd,
            )
        )
    elif execution_mode == consts.EXECUTION_MODE_K8S:
        print(get_colored_text_by_hsv(0.4, 0.8, 0.8, "Creating k8s job..."))
        model_factory_frontend_client.create_k8s_job(
            job_id=job_id,
            docker_image=docker_image_fullname,
            cpu_request=cpu_request,
            memory_request=memory_request,
            storage_request=storage_request,
            gpu_request=gpu_request,
            ttl_after_finished=ttl_after_finished,
            pool=pool,
            command=cmd,
            active_deadline_seconds=active_deadline_seconds,
        )
        print("k8s job created: {}".format(job_id))
    else:
        raise Exception("mode {} not supported!".format(execution_mode))

    return job_id


def get_job_log_from_loki(job_id):
    response = requests.get(
        "{}/loki/api/v1/query".format(Config.LOKI_ENDPOINT),
        params={
            "query": '{{container="{}"}}'.format(job_id),
            "limit": 5000,
        },
    )

    assert response.status_code == 200, vars(response)

    result = response.json()["data"]["result"]

    if not result:
        return None

    log_lines = []

    for result_item in result:
        log_lines += result_item["values"]

    return "".join([log_line for _, log_line in sorted(log_lines)])


def get_existing_upgraded_instances():
    existing_upgraded_instances = \
        ModelFactoryFrontendClient().get_devvms(
            vm_filter=[
                {
                    "Name": "tag:expiration_time",
                    "Values": ["*"]
                }
            ],
        )

    return existing_upgraded_instances["Reservations"]


def build_image(pipeline_name, image_tag, push=False):
    from core.dockerfile_generator import generate_pipeline_dockerfile

    image_name = pipeline_name
    docker_image_repo = "{}/{}".format(Config.DOCKER_REGISTRY, image_name)
    docker_image_fullname = "{}:{}".format(
        docker_image_repo,
        image_tag or "latest",
    )

    job_image_dockerfile = generate_pipeline_dockerfile(
        pipeline_name=pipeline_name,
    )

    assert not os.system("docker build {} -f {} -t {} --build-arg DOCKER_REGISTRY={}".format(
        get_model_factory_basedir(),
        job_image_dockerfile,
        docker_image_fullname,
        Config.DOCKER_REGISTRY,
    ))

    if push:
        assert not os.system("docker push {}".format(
            docker_image_fullname,
        ))


def get_current_pipeline_name():
    current_job_info = Tracking.get_info_for_single_job(
        ExecutionContext.job_id)
    if not current_job_info:
        return None
    return current_job_info["pipeline_name"]
