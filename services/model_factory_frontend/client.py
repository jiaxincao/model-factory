#!/usr/bin/env python3

from core import consts
from core.config import Config

import functools
import json
import jsonpickle
import os
import requests


def client_api(serialization="json"):
    def _client_api(func):
        def _exec_client_api(*args, **kwargs):
            response = func(*args, **kwargs)
            assert response.status_code == 200, "Failed to call {}: {}".format(
                func.__name__, vars(response)
            )

            if serialization == "json":
                return json.loads(response.content)
            elif serialization == "jsonpickle":
                return jsonpickle.loads(response.content)
            else:
                raise Exception("Serialization method \"{}\" not supported!".format(serialization))

        return functools.wraps(func)(_exec_client_api)

    return _client_api


class ModelFactoryFrontendClient():
    def __init__(self):
        self.mf_frontend_endpoint = os.environ.get(
            "MF_FRONTEND_ENDPOINT", Config.MF_FRONTEND_ENDPOINT
        )

    @client_api()
    def keepalive(self):
        return requests.post(
            '{}/keepalive'.format(self.mf_frontend_endpoint),
            json=None,
        )

    @client_api()
    def get_archived_job_log(
        self,
        job_id,
    ):
        return requests.post(
            '{}/get_archived_job_log'.format(self.mf_frontend_endpoint),
            json={
                "job_id": job_id,
            },
        )

    @client_api()
    def create_k8s_job(
        self,
        job_id,
        docker_image,
        cpu_request,
        memory_request,
        storage_request,
        ttl_after_finished,
        command,
        gpu_request,
        pool=consts.DEFAULT_POOL,
        active_deadline_seconds=None,
    ):
        return requests.post(
            '{}/create_k8s_job'.format(self.mf_frontend_endpoint),
            json={
                "job_id": job_id,
                "docker_image": docker_image,
                "cpu_request": cpu_request,
                "memory_request": memory_request,
                "storage_request": storage_request,
                "ttl_after_finished": ttl_after_finished,
                "gpu_request": gpu_request,
                "command": command,
                "pool": pool,
                "active_deadline_seconds": active_deadline_seconds,
            },
        )

    @client_api()
    def get_k8s_job_log(
        self,
        job_id,
    ):
        return requests.post(
            '{}/get_k8s_job_log'.format(self.mf_frontend_endpoint),
            json={
                "job_id": job_id,
            },
        )

    @client_api(serialization="jsonpickle")
    def list_all_k8s_jobs(self):
        return requests.post(
            '{}/list_all_k8s_jobs'.format(self.mf_frontend_endpoint),
        )

    @client_api()
    def delete_k8s_job(
        self,
        job_id,
    ):
        return requests.post(
            '{}/delete_k8s_job'.format(self.mf_frontend_endpoint),
            json={
                "job_id": job_id,
            },
        )

    @client_api(serialization="jsonpickle")
    def list_all_k8s_pods(self):
        return requests.post(
            '{}/list_all_k8s_pods'.format(self.mf_frontend_endpoint),
        )

    @client_api()
    def register_job(
        self,
        job_id,
        pipeline_name,
        pipeline_params,
        operator_id,
        docker_image_repo,
        docker_image_tag,
        docker_image_digest,
        execution_mode,
        cmd,
        owner,
        creator_host,
        tags,
        cpu_request,
        memory_request,
        storage_request,
        ttl_after_finished,
        gpu_request=None,
        parent_job_id=None,
        pool=None,
    ):
        return requests.post(
            '{}/register_job'.format(self.mf_frontend_endpoint),
            json={
                "job_id": job_id,
                "parent_job_id": parent_job_id,
                "pipeline_name": pipeline_name,
                "pipeline_params": pipeline_params,
                "operator_id": operator_id,
                "docker_image_repo": docker_image_repo,
                "docker_image_tag": docker_image_tag,
                "docker_image_digest": docker_image_digest,
                "execution_mode": execution_mode,
                "cmd": cmd,
                "owner": owner,
                "creator_host": creator_host,
                "tags": tags,
                "cpu_request": cpu_request,
                "memory_request": memory_request,
                "storage_request": storage_request,
                "ttl_after_finished": ttl_after_finished,
                "gpu_request": gpu_request,
                "pool": pool,
            },
        )

    @client_api()
    def get_info_for_single_job(
        self,
        job_id,
    ):
        return requests.post(
            '{}/get_info_for_single_job'.format(self.mf_frontend_endpoint),
            json={
                "job_id": job_id,
            },
        )

    @client_api()
    def tag_job(
        self,
        job_id,
        tag,
    ):
        return requests.post(
            '{}/tag_job'.format(self.mf_frontend_endpoint),
            json={
                "job_id": job_id,
                "tag": tag,
            },
        )

    @client_api()
    def untag_job(
        self,
        job_id,
        tag,
    ):
        return requests.post(
            '{}/untag_job'.format(self.mf_frontend_endpoint),
            json={
                "job_id": job_id,
                "tag": tag,
            },
        )

    @client_api(serialization="jsonpickle")
    def get_info_for_all_visiable_jobs(self):
        return requests.post(
            '{}/get_info_for_all_visiable_jobs'.format(
                self.mf_frontend_endpoint),
        )

    @client_api()
    def get_info_for_all_jobs(self):
        return requests.post(
            '{}/get_info_for_all_jobs'.format(self.mf_frontend_endpoint),
        )

    @client_api()
    def get_info_for_jobs(self, job_filter, job_fields=None):
        return requests.post(
            '{}/get_info_for_jobs'.format(self.mf_frontend_endpoint),
            json={
                "job_filter": json.dumps(job_filter),
                "job_fields": job_fields and json.dumps(job_fields),
            }
        )

    @client_api()
    def list_artifacts_namespaces(self):
        return requests.post(
            '{}/list_artifacts_namespaces'.format(self.mf_frontend_endpoint),
        )

    @client_api()
    def list_artifacts(
        self,
        artifact_namespace,
    ):
        return requests.post(
            '{}/list_artifacts'.format(self.mf_frontend_endpoint),
            json={
                "artifact_namespace": artifact_namespace,
            },
        )

    @client_api()
    def del_artifact(
        self,
        artifact_namespace,
        artifact_name,
    ):
        return requests.post(
            '{}/del_artifact'.format(self.mf_frontend_endpoint),
            json={
                "artifact_namespace": artifact_namespace,
                "artifact_name": artifact_name,
            },
        )

    @client_api()
    def drop_artifact_namespace(
        self,
        artifact_namespace,
    ):
        return requests.post(
            '{}/drop_artifact_namespace'.format(self.mf_frontend_endpoint),
            json={
                "artifact_namespace": artifact_namespace,
            },
        )

    @client_api()
    def get_model_by_id(
        self,
        model_id,
    ):
        return requests.post(
            '{}/get_model_by_id'.format(self.mf_frontend_endpoint),
            json={
                'model_id': model_id,
            },
        )

    @client_api()
    def list_models(
        self,
        model_filter=None,
    ):
        return requests.post(
            '{}/list_models'.format(self.mf_frontend_endpoint),
            json={
                "model_filter": model_filter or {},
            }
        )

    @client_api()
    def delete_model(
        self,
        model_id,
    ):
        return requests.post(
            '{}/delete_model'.format(self.mf_frontend_endpoint),
            json={
                "model_id": model_id,
            },
        )

    @client_api()
    def tag_model(
        self,
        model_id,
        tag,
    ):
        return requests.post(
            '{}/tag_model'.format(self.mf_frontend_endpoint),
            json={
                "model_id": model_id,
                "tag": tag,
            },
        )

    @client_api()
    def untag_model(
        self,
        model_id,
        tag,
    ):
        return requests.post(
            '{}/untag_model'.format(self.mf_frontend_endpoint),
            json={
                "model_id": model_id,
                "tag": tag,
            },
        )

    @client_api()
    def list_triggers(
        self,
    ):
        return requests.post(
            '{}/list_triggers'.format(self.mf_frontend_endpoint),
        )

    @client_api()
    def enable_trigger(
        self,
        trigger_name
    ):
        return requests.post(
            '{}/enable_trigger'.format(self.mf_frontend_endpoint),
            json={
                "trigger_name": trigger_name,
            },
        )

    @client_api()
    def disable_trigger(
        self,
        trigger_name
    ):
        return requests.post(
            '{}/disable_trigger'.format(self.mf_frontend_endpoint),
            json={
                "trigger_name": trigger_name,
            },
        )

    @client_api()
    def promote_model(
        self,
        model_id,
    ):
        return requests.post(
            '{}/promote_model'.format(self.mf_frontend_endpoint),
            json={
                "model_id": model_id,
            },
        )

    @client_api()
    def list_production_models(
        self,
        model_names=None,
    ):
        return requests.post(
            '{}/list_production_models'.format(self.mf_frontend_endpoint),
            json={
                "model_names": model_names,
            },
        )

    @client_api(serialization="jsonpickle")
    def get_devvms(self, vm_filter=[]):
        return requests.post(
            '{}/get_devvms'.format(self.mf_frontend_endpoint),
            json={
                "vm_filter": vm_filter,
            },
        )

    @client_api()
    def get_upgraded_devvms(self):
        return requests.post(
            '{}/get_upgraded_devvms'.format(self.mf_frontend_endpoint),
        )

    @client_api()
    def modify_devvm_instance_type(
        self,
        instance_id,
        instance_type,
        days=7,
    ):
        return requests.post(
            '{}/modify_devvm_instance_type'.format(self.mf_frontend_endpoint),
            json={
                "instance_id": instance_id,
                "instance_type": instance_type,
                "days": days,
            },
        )

    @client_api()
    def expire_upgrade_devvm(self, instance_id):
        return requests.post(
            '{}/expire_upgrade_devvm'.format(self.mf_frontend_endpoint),
            json={
                "instance_id": instance_id,
            },
        )

    @client_api()
    def start_devvm(self, instance_id):
        return requests.post(
            '{}/start_devvm'.format(self.mf_frontend_endpoint),
            json={
                "instance_id": instance_id,
            },
        )

    @client_api()
    def autoscaling_set_desired_capacity(self, asg_group, desired_capacity):
        return requests.post(
            '{}/autoscaling_set_desired_capacity'.format(
                self.mf_frontend_endpoint),
            json={
                "asg_group": asg_group,
                "desired_capacity": desired_capacity,
            },
        )

    @client_api(serialization="jsonpickle")
    def autoscaling_describe_asg(self, asg_group):
        return requests.post(
            '{}/autoscaling_describe_asg'.format(self.mf_frontend_endpoint),
            json={
                "asg_group": asg_group,
            },
        )

    @client_api(serialization="jsonpickle")
    def ec2_get_instances(self, instance_filters):
        return requests.post(
            '{}/ec2_get_instances'.format(self.mf_frontend_endpoint),
            json={
                "instance_filters": instance_filters,
            },
        )

    @client_api()
    def autoscaling_detach_instance(
        self,
        instance_ids,
        asg_group,
        should_decrement_desired_capacity,
    ):
        return requests.post(
            '{}/autoscaling_detach_instance'.format(self.mf_frontend_endpoint),
            json={
                "instance_ids": instance_ids,
                "asg_group": asg_group,
                "should_decrement_desired_capacity": (
                    should_decrement_desired_capacity),
            },
        )

    @client_api()
    def autoscaling_terminate_instance_in_auto_scaling_group(
        self,
        instance_id,
        should_decrement_desired_capacity,
    ):
        return requests.post(
            '{}/autoscaling_terminate_instance_in_auto_scaling_group'.format(self.mf_frontend_endpoint),
            json={
                "instance_id": instance_id,
                "should_decrement_desired_capacity": (
                    should_decrement_desired_capacity),
            },
        )

    @client_api(serialization="jsonpickle")
    def autoscaling_describe_auto_scaling_group(self):
        return requests.post(
            '{}/autoscaling_describe_auto_scaling_group'.format(self.mf_frontend_endpoint),
        )
