#!/usr/bin/env python3

from core import consts
from core.config import Config
from core.kubernetes_proxy import KubernetesProxy
from core.model_registry import ModelRegistry
from core.tracking import Tracking
from core.trigger_manager import TriggerManager
from flask import Flask, request
from flask_cors import CORS
import boto3
import functools
import json
import jsonpickle
import logging
import os
import shlex
import sys
import tempfile


def service_api(serialization="json"):
    def _service_api(func):
        def _exec_service_api(*args, **kwargs):
            try:
                logging.info("==> {} ({})".format(
                    func.__name__,
                    ", ".join(
                        ["\"{}\"".format(arg) for arg in args[1:]] +
                        (["{}=\"{}\"".format(k, v) for k, v in kwargs] if kwargs else [])
                    ),
                ))

                if serialization == "json":
                    return json.dumps(func(*args, **kwargs))
                elif serialization == "jsonpickle":
                    return jsonpickle.dumps(func(*args, **kwargs), keys=True)
                else:
                    raise Exception("Serialization method \"{}\" not supported!".format(serialization))
            finally:
                logging.info("<== {}".format(func.__name__))

        return functools.wraps(func)(_exec_service_api)
    return _service_api


app = Flask(__name__)
CORS(app)


################################################################################
# keepalive APIs
################################################################################

@app.route('/keepalive', methods=["GET", "POST"])
@service_api()
def keepalive():
    return {'ok': 1}


################################################################################
# S3 related APIs
################################################################################

@app.route('/get_archived_job_log', methods=["POST"])
@service_api()
def get_archived_job_log():
    job_id = request.json["job_id"]

    _, filename = tempfile.mkstemp(prefix="model_factory_job_log_")

    s3_client = boto3.client('s3')
    fp = s3_client.download_file(
        Bucket=Config.S3_BUCKET,
        Key="job_logs/{}.log".format(job_id),
        Filename=filename,
    )

    with open(filename, "rb") as fp:
        log = fp.read()

    os.remove(filename)

    return log.decode()


################################################################################
# K8s related APIs
################################################################################

@app.route('/create_k8s_job', methods=["POST"])
@service_api()
def create_k8s_job():
    job_id = request.json["job_id"]
    docker_image = request.json["docker_image"]
    cpu_request = request.json["cpu_request"]
    memory_request = request.json["memory_request"]
    storage_request = request.json["storage_request"]
    ttl_after_finished = request.json["ttl_after_finished"]
    command = request.json["command"]
    gpu_request = request.json.get("gpu_request", None)
    pool = request.json.get("pool") or consts.DEFAULT_POOL
    active_deadline_seconds = request.json.get(
        "active_deadline_seconds", None
    )

    active_deadline_seconds = (
        int(active_deadline_seconds)
        if active_deadline_seconds is not None else None
    )
    KubernetesProxy.create_job(
        job_id=job_id,
        docker_image=docker_image,
        cpu_request=cpu_request,
        memory_request=memory_request,
        storage_request=storage_request,
        ttl_after_finished=ttl_after_finished,
        command=shlex.split(command) if command else None,
        gpu_request=gpu_request,
        pool=pool,
        active_deadline_seconds=active_deadline_seconds,
    )


@app.route('/get_k8s_job_log', methods=["POST"])
@service_api()
def get_k8s_job_log():
    job_id = request.json["job_id"]

    job_info = Tracking.get_info_for_single_job(job_id)

    pod_name = job_info.get("pod_name", None)

    return pod_name and KubernetesProxy.get_job_log(pod_name)


@app.route('/list_all_k8s_jobs', methods=["POST"])
@service_api(serialization="jsonpickle")
def list_all_k8s_jobs():
    return KubernetesProxy.list_jobs()


@app.route('/delete_k8s_job', methods=["POST"])
@service_api()
def delete_k8s_job():
    job_id = request.json["job_id"]

    KubernetesProxy.delete_job(job_id)


@app.route('/list_all_k8s_pods', methods=["POST"])
@service_api(serialization="jsonpickle")
def list_all_k8s_pods():
    return KubernetesProxy.list_pods()


################################################################################
# Tracking related APIs
################################################################################
@app.route('/register_job', methods=["POST"])
@service_api()
def register_job():
    job_id = request.json["job_id"]
    parent_job_id = request.json.get("parent_job_id", None)
    pipeline_name = request.json["pipeline_name"]
    pipeline_params = request.json["pipeline_params"]
    operator_id = request.json.get("operator_id", None)
    pool = request.json.get("pool", None)
    docker_image_repo = request.json.get("docker_image_repo", None)
    docker_image_tag = request.json.get("docker_image_tag", None)
    docker_image_digest = request.json.get("docker_image_digest", None)
    execution_mode = request.json.get("execution_mode", None)
    cmd = request.json["cmd"]
    owner = request.json["owner"]
    creator_host = request.json["creator_host"]
    tags = request.json["tags"]
    cpu_request = request.json["cpu_request"]
    memory_request = request.json["memory_request"]
    storage_request = request.json["storage_request"]
    ttl_after_finished = request.json["ttl_after_finished"]
    gpu_request = request.json.get("gpu_request", None)

    Tracking.create_job(
        job_id=job_id,
        parent_job_id=parent_job_id,
        pipeline_name=pipeline_name,
        pipeline_params=pipeline_params,
        operator_id=operator_id,
        pool=pool,
        owner=owner,
        docker_image_repo=docker_image_repo,
        docker_image_tag=docker_image_tag,
        docker_image_digest=docker_image_digest,
        execution_mode=execution_mode,
        tags=sorted(list(set(tags))),
        creator_host=creator_host,
        cmd=cmd,
        cpu_request=cpu_request,
        memory_request=memory_request,
        storage_request=storage_request,
        ttl_after_finished=ttl_after_finished,
        gpu_request=gpu_request,
    )


@app.route('/get_info_for_single_job', methods=["POST"])
@service_api()
def get_info_for_single_job():
    job_id = request.json["job_id"]

    job_info = Tracking.get_info_for_single_job(job_id)
    return job_info


@app.route('/tag_job', methods=["POST"])
@service_api()
def tag_job():
    job_id = request.json["job_id"]
    tag = request.json["tag"]

    Tracking.tag_job(job_id, tag)


@app.route('/untag_job', methods=["POST"])
@service_api()
def untag_job():
    job_id = request.json["job_id"]
    tag = request.json["tag"]

    Tracking.untag_job(job_id, tag)


@app.route('/get_info_for_all_visiable_jobs', methods=["POST"])
@service_api(serialization="jsonpickle")
def get_info_for_all_visiable_jobs():
    return Tracking.get_info_for_all_visiable_jobs()


@app.route('/get_info_for_all_jobs', methods=["POST"])
@service_api()
def get_info_for_all_jobs():
    return Tracking.get_info_for_all_jobs()


@app.route('/get_info_for_jobs', methods=["POST"])
@service_api()
def get_info_for_jobs():
    job_filter = request.json["job_filter"]
    job_fields = request.json["job_fields"]

    return Tracking.get_info_for_jobs(
        job_filter=job_filter and json.loads(job_filter),
        job_fields=job_fields and json.loads(job_fields),
    )


@app.route('/list_artifacts_namespaces', methods=["POST"])
@service_api()
def list_artifacts_namespaces():
    return Tracking.get_all_artifact_namespaces()


@app.route('/list_artifacts', methods=["POST"])
@service_api()
def list_artifacts():
    artifact_namespace = request.json["artifact_namespace"]

    artifacts_info = Tracking.get_artifacts_info(artifact_namespace)

    return {
        name: {
            str(key): str(value)
            for key, value in artifact_info.items()
        }
        for name, artifact_info in artifacts_info.items()
    }


@app.route('/del_artifact', methods=["POST"])
@service_api()
def del_artifact():
    artifact_namespace = request.json["artifact_namespace"]
    artifact_name = request.json["artifact_name"]

    Tracking.del_artifact(artifact_namespace, artifact_name)


@app.route('/drop_artifact_namespace', methods=["POST"])
@service_api()
def drop_artifact_namespace():
    artifact_namespace = request.json["artifact_namespace"]

    Tracking.drop_artifact_namespace(artifact_namespace)


@app.route('/get_model_by_id', methods=["POST"])
@service_api()
def get_model_by_id():
    model_id = request.json["model_id"]

    return ModelRegistry.get_info_for_model(model_id)


@app.route('/list_models', methods=["GET", "POST"])
@service_api()
def list_models():
    model_filter = request.json.get("model_filter", {})

    return ModelRegistry.get_info_for_models(
        query_filter=model_filter
    )


@app.route('/delete_model', methods=["POST"])
@service_api()
def delete_model():
    model_id = request.json["model_id"]

    ModelRegistry.delete_model(model_id)


@app.route('/tag_model', methods=["POST"])
@service_api()
def tag_model():
    model_id = request.json["model_id"]
    tag = request.json["tag"]

    ModelRegistry.tag_model(model_id, tag)


@app.route('/untag_model', methods=["POST"])
@service_api()
def untag_model():
    model_id = request.json["model_id"]
    tag = request.json["tag"]

    ModelRegistry.untag_model(model_id, tag)


@app.route('/list_triggers', methods=["GET", "POST"])
@service_api()
def list_triggers():
    return TriggerManager.load_info_for_all_triggers()


@app.route('/enable_trigger', methods=["POST"])
@service_api()
def enable_trigger():
    trigger_name = request.json["trigger_name"]
    return TriggerManager.enable_trigger(trigger_name)


@app.route('/disable_trigger', methods=["POST"])
@service_api()
def disable_trigger():
    trigger_name = request.json["trigger_name"]
    return TriggerManager.enable_trigger(trigger_name)


@app.route('/promote_model', methods=["POST"])
@service_api()
def promote_model():
    model_id = request.json["model_id"]

    ModelRegistry.promote_model(model_id)


@app.route('/list_production_models', methods=["POST"])
@service_api()
def list_production_models():
    model_names = request.json["model_names"]

    return ModelRegistry.list_production_models(model_names)


if __name__ == '__main__':
    logging.basicConfig(
        format='[%(asctime)s] {%(filename)32s:%(lineno)-5d} %(levelname)8s - %(message)s',
        stream=sys.stdout,
        level=logging.INFO,
    )

    app.run(host='0.0.0.0')
