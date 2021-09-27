#!/usr/bin/env python3

from core import consts as mf_consts
from core import utils as core_utils
from core.config import Config
from core.termcolor import get_colored_text_by_hsv
from datetime import datetime
from treelib import Tree
from zlib import crc32
import click
import os
import pytz
import socket
import stat
import tabulate
import uuid

from services.model_factory_frontend.client import ModelFactoryFrontendClient


@click.group(name="job")
def job():
    """
    Commands to manage model factory pipeline jobs.
    """
    pass


@job.command(name="create")
@click.argument("pipeline-name")
@click.option("--mode", type=click.Choice(['k8s', 'inplace', 'local']), default="k8s", help="The job execution mode.")
@click.option("--pipeline-params", default="{}", help="The parameters to pass into the pipeline.")
@click.option(
    "--operator-id", help="The operator to execute. If not specified, we'll use the 'main' operator."
)
@click.option(
    "-t", "--tags", default="", show_default=True, help="Tags for the job."
)
@click.option(
    "--cpu-request", help="CPU requirements."
)
@click.option(
    "--memory-request", help="Memory requirements."
)
@click.option(
    "--storage-request", help="Storage requirements."
)
@click.option(
    "--ttl-after-finished", default=3600, type=int, show_default=True, help="The timeout seconds for your job to be deleted after completion."
)
@click.option(
    "--gpu-request", type=int, help="GPU requirements."
)
@click.option(
    "--pool", default=mf_consts.DEFAULT_POOL, help="The training pool."
)
@click.option(
    "--docker-image", help="The pipeline pool image. If not provided, we will build new one based on your current code snapshot."
)
@click.option(
    "--active-deadline-seconds", help="job will be timeout after certain seconds"
)
def create(
    pipeline_name,
    mode,
    pipeline_params,
    operator_id,
    tags,
    cpu_request,
    memory_request,
    storage_request,
    ttl_after_finished,
    gpu_request,
    pool,
    docker_image,
    active_deadline_seconds,
):
    """
    Create a job to execute a model factory pipeline.
    """
    if docker_image:
        tokens = docker_image.split(':')

        docker_image_repo = tokens[0]
        docker_image_tag = len(tokens) > 1 and tokens[1]
    else:
        docker_image_repo = None
        docker_image_tag = None

    tags = [tag.strip() for tag in tags.split(",")] if tags else []
    return core_utils.create_job(
        execution_mode=mode,
        pipeline_name=pipeline_name,
        pipeline_params=pipeline_params,
        operator_id=operator_id,
        pool=pool,
        tags=tags,
        owner=core_utils.get_current_user(),
        cpu_request=cpu_request,
        memory_request=memory_request,
        storage_request=storage_request,
        gpu_request=gpu_request,
        ttl_after_finished=ttl_after_finished,
        docker_image_repo=docker_image_repo,
        docker_image_tag=docker_image_tag,
        active_deadline_seconds=active_deadline_seconds,
    )


@job.command(name="retry")
@click.argument("job-id")
@click.option("--pipeline-params", default="{}", help="The parameters to pass into the pipeline.")
@click.option(
    "--cpu-request", help="CPU requirements."
)
@click.option(
    "--memory-request", help="Memory requirements."
)
@click.option(
    "--storage-request", help="Storage requirements."
)
@click.option(
    "--ttl-after-finished", help="The timeout seconds for your job to be deleted after completion."
)
@click.option(
    "--build-new-image", is_flag=True, help="Build a new image for the retry job."
)
@click.option(
    "--gpu-request", type=int, help="GPU requirements."
)
@click.option(
    "--pool", help="The training pool."
)
def retry(
    job_id,
    pipeline_params,
    cpu_request,
    memory_request,
    storage_request,
    ttl_after_finished,
    build_new_image,
    gpu_request,
    pool,
):
    """
    Retry a job.
    """
    model_factory_frontend_client = ModelFactoryFrontendClient()
    job_info = model_factory_frontend_client.get_info_for_single_job(job_id)

    pipeline_name = job_info.get("pipeline_name")
    pipeline_params = job_info.get("pipeline_params")
    docker_image_repo = job_info.get("docker_image_repo")
    docker_image_tag = job_info.get("docker_image_tag")
    operator_id = job_info.get("operator_id")
    pool = pool or job_info.get("pool")

    cpu_request = (
        cpu_request if cpu_request is not None
        else job_info.get("resources", {}).get("cpu_request")
    )
    memory_request = (
        memory_request if memory_request is not None
        else job_info.get("resources", {}).get("memory_request")
    )
    storage_request = (
        storage_request if storage_request is not None
        else job_info.get("resources", {}).get("storage_request")
    )
    ttl_after_finished = ttl_after_finished or job_info.get("ttl_after_finished", 3600)
    tags = job_info.get("tags", [])
    gpu_request = gpu_request if gpu_request is not None else job_info.get(
        "resources", {}).get("gpu_request")

    # Add the retry flag
    if "retry" not in tags:
        tags.append("retry")

    # Remove the hide flag.
    if "hide" in tags:
        tags.remove("hide")

    return core_utils.create_job(
        execution_mode="k8s",
        pipeline_name=pipeline_name,
        pipeline_params=pipeline_params,
        operator_id=operator_id,
        pool=pool,
        tags=tags,
        owner=core_utils.get_current_user(),
        cpu_request=cpu_request,
        memory_request=memory_request,
        storage_request=storage_request,
        gpu_request=gpu_request,
        ttl_after_finished=ttl_after_finished,
        docker_image_repo=docker_image_repo if not build_new_image else None,
        docker_image_tag=docker_image_tag if not build_new_image else None,
    )


@job.command(name="events")
@click.argument("job-id")
def events(job_id):
    """
    Create a job to execute a model factory pipeline.
    """
    model_factory_frontend_client = ModelFactoryFrontendClient()
    job_info = model_factory_frontend_client.get_info_for_single_job(job_id)
    job_events = sorted(job_info["events"], key=lambda event: event["timestamp"])

    tree = Tree()

    tree.create_node(
        tag=get_colored_text_by_hsv(0.1, 0.5, 0.9, "Job {} events".format(job_id)),
        identifier="events",
    )

    for i, event in enumerate(job_events):
        type_color = float(crc32(event["type"].encode()) & 0xffffffff) / 2**32

        node_id = "event_{:08d}".format(i)
        tree.create_node(
            tag="{} ({})".format(
                get_colored_text_by_hsv(type_color, 0.5, 1, event["type"]),
                get_colored_text_by_hsv(type_color, 0.5, 0.9, datetime.utcfromtimestamp(event["timestamp"]).replace(tzinfo=pytz.utc)),
            ),
            identifier=node_id,
            parent="events",
        )

        for k, v in event["metadata"].items():
            tree.create_node(
                tag="{}: {}".format(
                    get_colored_text_by_hsv(type_color, 0.3, 0.8, k),
                    get_colored_text_by_hsv(type_color, 0.3, 1, v),
                ),
                identifier="{}_{}".format(node_id, k),
                parent=node_id,
            )

    tree.show(key=lambda node: node._identifier)


@job.command(name="info")
@click.argument("job-id")
def info(job_id):
    """
    Get basic information about the job.
    """
    model_factory_frontend_client = ModelFactoryFrontendClient()
    job_info = model_factory_frontend_client.get_info_for_single_job(job_id)

    print((
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "Job information: \n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "* job id                 : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "* parent job id          : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "* pod-name               : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "* ip-addr                : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "* owner                  : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "* creator_host           : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "* pipeline name          : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "* pipeline parameters    : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "* operator id            : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "* creation_time          : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "* start_time             : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "* completion_time        : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "* docker_image_repo      : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "* docker_image_tag       : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "* docker_image_digest    : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "* execution_mode         : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "* cmd                    : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "* tags                   : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "* ttl after finished     : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "* pool                   : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "* resources: \n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "  * cpu requests         : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "  * memory requests      : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "  * storage requests     : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "  * gpu requests         : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "* archived               : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "* status                 : {}\n") +
        get_colored_text_by_hsv(0.5, 0.5, 0.9, "* output                 : {}\n")
    ).format(
        get_colored_text_by_hsv(0.1, 0.3, 0.8, job_info["job_id"]),
        get_colored_text_by_hsv(0.1, 0.3, 0.8, job_info.get("parent_job_id")),
        get_colored_text_by_hsv(0.1, 0.3, 0.8, job_info["pod_name"]),
        get_colored_text_by_hsv(0.1, 0.3, 0.8, job_info.get("ip_addr", None)),
        get_colored_text_by_hsv(0.1, 0.3, 0.8, job_info["owner"]),
        get_colored_text_by_hsv(0.1, 0.3, 0.8, job_info["creator_host"]),
        get_colored_text_by_hsv(0.1, 0.3, 0.8, job_info["pipeline_name"]),
        get_colored_text_by_hsv(0.1, 0.3, 0.8, job_info["pipeline_params"]),
        get_colored_text_by_hsv(0.1, 0.3, 0.8, job_info.get("operator_id")),
        get_colored_text_by_hsv(
            0.1, 0.3, 0.8, core_utils.get_utc_time_from_timestamp(job_info.get("creation_timestamp"))
        ),
        get_colored_text_by_hsv(
            0.1, 0.3, 0.8, core_utils.get_utc_time_from_timestamp(job_info.get("start_timestamp"))
        ),
        get_colored_text_by_hsv(
            0.1, 0.3, 0.8, core_utils.get_utc_time_from_timestamp(job_info.get("completion_timestamp"))
        ),
        get_colored_text_by_hsv(0.1, 0.3, 0.8, job_info.get("docker_image_repo")),
        get_colored_text_by_hsv(0.1, 0.3, 0.8, job_info.get("docker_image_tag")),
        get_colored_text_by_hsv(0.1, 0.3, 0.8, job_info.get("docker_image_digest")),
        get_colored_text_by_hsv(0.1, 0.3, 0.8, job_info.get("execution_mode")),
        get_colored_text_by_hsv(0.1, 0.3, 0.8, job_info["cmd"]),
        get_colored_text_by_hsv(0.1, 0.3, 0.8, job_info["tags"]),
        get_colored_text_by_hsv(0.1, 0.3, 0.8, job_info["ttl_after_finished"]),
        get_colored_text_by_hsv(0.1, 0.3, 0.8, job_info.get("pool", None)),
        get_colored_text_by_hsv(0.1, 0.3, 0.8, job_info["resources"]["cpu_request"]),
        get_colored_text_by_hsv(0.1, 0.3, 0.8, job_info["resources"]["memory_request"]),
        get_colored_text_by_hsv(0.1, 0.3, 0.8, job_info["resources"]["storage_request"]),
        get_colored_text_by_hsv(0.1, 0.3, 0.8, job_info["resources"]["gpu_request"]),
        get_colored_text_by_hsv(0.1, 0.3, 0.8, job_info.get("archived", False)),
        get_colored_text_by_hsv(0.1, 0.3, 0.8, job_info.get("status", "unknown")),
        get_colored_text_by_hsv(0.1, 0.3, 0.8, job_info.get("output", {})),
    ))


@job.command(name="tag")
@click.argument("job-id")
@click.argument("tag")
def tag(job_id, tag):
    """
    Add a tag to a job.
    """
    model_factory_frontend_client = ModelFactoryFrontendClient()

    for tag in tag.split(","):
        model_factory_frontend_client.tag_job(job_id, tag)


@job.command(name="untag")
@click.argument("job-id")
@click.argument("tag")
def untag(job_id, tag):
    """
    Remove a tag from a job.
    """
    model_factory_frontend_client = ModelFactoryFrontendClient()
    for tag in tag.split(","):
        model_factory_frontend_client.untag_job(job_id, tag)


@job.command(name="hide")
@click.argument("job-id")
def hide(job_id):
    """
    Hide a tag from the mf job list command.
    """
    model_factory_frontend_client = ModelFactoryFrontendClient()
    model_factory_frontend_client.tag_job(job_id, "hide")


@job.command(name="delete")
@click.argument("job_id")
def delete(job_id):
    """
    Delete a job.
    """
    def _get_all_child_job_ids(job_id, client):
        cur_child_job_qs = client.get_info_for_jobs(
            job_filter={"parent_job_id": job_id},
            job_fields={"job_id": 1, "_id": 0},
        )
        if not cur_child_job_qs:
            return []

        cur_child_job_ids = [x['job_id'] for x in cur_child_job_qs]
        pre_child_job_ids = []
        for cur_child_job_id in cur_child_job_ids:
            pre_child_job_ids.extend(
                _get_all_child_job_ids(cur_child_job_id, client))

        cur_child_job_ids.extend(pre_child_job_ids)
        return cur_child_job_ids

    model_factory_frontend_client = ModelFactoryFrontendClient()

    child_job_ids = _get_all_child_job_ids(
        job_id, model_factory_frontend_client)
    for child_job_id in child_job_ids:
        model_factory_frontend_client.delete_k8s_job(
            child_job_id)
        model_factory_frontend_client.tag_job(
            child_job_id, "hide")
        print("{} child job deleted".format(child_job_id))

    model_factory_frontend_client.delete_k8s_job(job_id)
    model_factory_frontend_client.tag_job(job_id, "hide")
    print("{} master job deleted".format(job_id))


@job.command(name="list")
@click.option("--owner", default=core_utils.get_current_user(), help="The owner filter. '*' for all.")
@click.option("--tag", help="The tag filter.")
@click.option("--pipeline", help="The pipeline filter.")
@click.option("--status", help="The status filter.")
@click.option("--show-hidden", is_flag=True, help="Show the hidden jobs as well.")
@click.option("-n", type=int, help="Only show the last n jobs.")
@click.option("-o", "--output", type=click.Choice(['regular', 'full', 'short']), default="regular", help="The output format.")
def list(owner, tag, pipeline, status, show_hidden, n, output):
    """
    List jobs.
    """
    if output == "regular":
        header = [
            "Job ID",
            "Pipeline",
            "Operator",
            "Start Time (UTC)",
            "Duration",
            "Owner",
            "Stage",
            "Status",
        ]
    elif output == "full":
        header = [
            "Job ID",
            "Tags",
            "Pool",
            "Pipeline",
            "Operator",
            "Creation Time (UTC)",
            "Start Time (UTC)",
            "Completion Time (UTC)",
            "Duration",
            "Owner",
            "Stage",
            "Status",
            "Output",
        ]
    elif output == "short":
        header = [
            "Job ID",
            "Pipeline",
            "Operator",
            "Owner",
            "Stage",
            "Status",
        ]
    else:
        raise Exception("Unexpected output format {}!".format(output))

    table = []

    model_factory_frontend_client = ModelFactoryFrontendClient()

    query_filters = {}

    if not show_hidden:
        query_filters["tags"] = {"$nin": ["hide"]}

    if owner and owner != '*':
        query_filters["owner"] = owner

    jobs_info = model_factory_frontend_client.get_info_for_jobs(
        query_filters,
        {"events": 0},
    )

    for job_info in jobs_info:
        job_id = job_info.get("job_id", None)

        if not job_id:
            continue

        # Get job fields.
        tags = job_info.get("tags", []) if job_info else []
        pool = job_info.get("pool", None)
        pipeline_name = job_info.get("pipeline_name", "")
        short_operator_id = job_info.get("operator_id", "")
        job_owner = job_info.get("owner", "")
        stage = job_info.get("stage", "")
        job_output = job_info.get("output", "")
        job_status = job_info.get("status", "")
        creation_time = core_utils.get_utc_time_from_timestamp(job_info.get("creation_timestamp", None))
        creation_time_str = creation_time and creation_time.strftime("%Y-%m-%d %H:%M:%S")
        start_time = core_utils.get_utc_time_from_timestamp(job_info.get("start_timestamp", None))
        start_time_str = start_time and start_time.strftime("%Y-%m-%d %H:%M:%S")
        completion_time = core_utils.get_utc_time_from_timestamp(job_info.get("completion_timestamp", None))
        completion_time_str = completion_time and completion_time.strftime("%Y-%m-%d %H:%M:%S")
        duration = start_time and completion_time and (completion_time - start_time)
        exit_code = job_info.get("exit_code", None)
        exit_reason = job_info.get("exit_reason", None)

        if job_status == "succeeded":
            v = 0.7
            job_status_with_color = get_colored_text_by_hsv(0.35, 0.8, v, 'succeeded')
        elif job_status == "failed":
            v = 0.7
            job_status_with_color = get_colored_text_by_hsv(
                0, 0.8, v, 'failed' + (' ({})'.format(exit_reason) if exit_reason else '')
            )
        elif job_status == "running":
            v = 0.9
            job_status_with_color = get_colored_text_by_hsv(0.1, 0.8, v, 'running')
        elif job_status == "pending":
            v = 0.9
            job_status_with_color = get_colored_text_by_hsv(0.05, 0.8, v, 'pending')
        elif job_status == "deleted":
            v = 0.55
            job_status_with_color = get_colored_text_by_hsv(0, 0.8, v, 'deleted')
        else:
            v = 0.8
            job_status_with_color = status

        # Filter the jobs.
        if tag and tag not in tags:
            continue

        if pipeline and pipeline != pipeline_name:
            continue

        if owner and owner != job_owner and owner != '*':
            continue

        if status and job_status != status:
            continue

        # Prepare the job table data.
        owner_color = float(crc32(job_owner.encode()) & 0xffffffff) / 2**32

        if output == "regular":
            table.append([
                get_colored_text_by_hsv(0.4, 0.8, v, job_id),
                get_colored_text_by_hsv(0.5, 0.8, v, pipeline_name),
                get_colored_text_by_hsv(0.5, 0.8, v, short_operator_id),
                get_colored_text_by_hsv(0.2, 0.8, v, start_time_str),
                get_colored_text_by_hsv(0.2, 0.8, v, duration),
                get_colored_text_by_hsv(owner_color, 0.5, v, job_owner),
                get_colored_text_by_hsv(0.15, 0.8, v, stage),
                job_status_with_color,
            ])
        elif output == "full":
            table.append([
                get_colored_text_by_hsv(0.4, 0.8, v, job_id),
                get_colored_text_by_hsv(0.55, 0.8, v, ", ".join(tags)),
                get_colored_text_by_hsv(0.85, 0.8, v, pool),
                get_colored_text_by_hsv(0.5, 0.8, v, pipeline_name),
                get_colored_text_by_hsv(0.5, 0.8, v, short_operator_id),
                get_colored_text_by_hsv(0.2, 0.8, v, creation_time_str),
                get_colored_text_by_hsv(0.2, 0.8, v, start_time_str),
                get_colored_text_by_hsv(0.2, 0.8, v, completion_time_str),
                get_colored_text_by_hsv(0.25, 0.8, v, duration),
                get_colored_text_by_hsv(owner_color, 0.5, v, job_owner),
                get_colored_text_by_hsv(0.15, 0.8, v, stage),
                job_status_with_color,
                get_colored_text_by_hsv(0.45, 0.8, v, job_output),
            ])
        elif output == "short":
            table.append([
                get_colored_text_by_hsv(0.4, 0.8, v, job_id),
                get_colored_text_by_hsv(0.5, 0.8, v, pipeline_name),
                get_colored_text_by_hsv(0.5, 0.8, v, short_operator_id),
                get_colored_text_by_hsv(owner_color, 0.5, v, job_owner),
                get_colored_text_by_hsv(0.15, 0.8, v, stage),
                job_status_with_color,
            ])
        else:
            raise Exception("Unexpected output format {}!".format(fmt))

    print(tabulate.tabulate(table[-n:] if n else table, header, tablefmt="pretty"))


@job.command(name="repro")
@click.argument("job_id")
@click.option(
    "--memory-limit", default="4Gi", show_default=True, help="The memory limitation of the docker container."
)
def repro(job_id, memory_limit):
    """
    Reproduce a job on your devbox.

    This command will create a docker container on your devbox with the exact same setup of the existing job.
    """
    model_factory_frontend_client = ModelFactoryFrontendClient()
    job_info = model_factory_frontend_client.get_info_for_single_job(job_id)

    repro_job_id = "j-{}".format(uuid.uuid4())

    pipeline_name = job_info.get("pipeline_name")
    operator_id = job_info.get("operator_id")
    docker_image_repo = job_info.get("docker_image_repo")
    docker_image_tag = job_info.get("docker_image_tag")
    docker_image_digest = job_info.get("docker_image_digest")

    cmd = job_info["cmd"].replace(job_id, repro_job_id)

    job_info = model_factory_frontend_client.register_job(
        job_id=repro_job_id,
        pipeline_name=pipeline_name,
        pipeline_params=job_info.get("pipeline_params"),
        operator_id=operator_id,
        docker_image_repo=docker_image_repo,
        docker_image_tag=docker_image_tag,
        docker_image_digest=docker_image_digest,
        execution_mode=mf_consts.EXECUTION_MODE_LOCAL,
        cmd=cmd,
        owner=core_utils.get_current_user(),
        creator_host=socket.gethostname(),
        tags=job_info.get("tags", []) + ["repro"],
        cpu_request=job_info.get("resources", {}).get("cpu_request", "1"),
        memory_request=job_info.get("resources", {}).get("memory_request", "4Gi"),
        storage_request=job_info.get("resources", {}).get("storage_request", "1Ti"),
        ttl_after_finished=job_info.get("ttl_after_finished", 3600),
    )

    print((
        "Welcome to model factory {} container\n\n"
        "This is a fresh new container on your devbox. Use the following command to start reproducing the job:\n"
        "{}\n\n"
        "Have fun!\n"
    ).format(
        pipeline_name,
        get_colored_text_by_hsv(0.05, 0.8, 0.8, cmd),
    ))

    # Print a help message.
    print("Pulling docker image. This might take a few minutes...")

    local_image_id = core_utils.pull_docker_image(
        core_utils.get_docker_image_fullname(
        docker_image_repo,
        docker_image_tag,
        docker_image_digest,
    ))

    # Erase the help message.
    print("\033[A\r\033[2K", end="")

    os.system("docker run --privileged -m {} -v ~/.ssh/id_rsa:/root/.ssh/id_rsa -it {} /bin/bash".format(
        memory_limit,
        local_image_id,
    ))
