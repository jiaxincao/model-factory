from . import consts
from . import utils
from .execution_context import ExecutionContext
from .kubernetes_proxy import KubernetesProxy
from .tracking import Tracking
from dataclasses import dataclass
from typing import Optional
import importlib
import json
import logging
import time


@dataclass
class Operator:
    operator_id: str
    input_schema: object
    cpu_request: int = consts.DEFAULT_CPU_REQUEST
    memory_request: str = consts.DEFAULT_MEMORY_REQUEST
    storage_request: str = consts.DEFAULT_STORAGE_REQUEST
    gpu_request: int = consts.DEFAULT_GPU_REQUEST
    pool: Optional[str] = None

    def __call__(self, *args, **kwargs):
        tokens = self.operator_id.split(".")

        operator_module_name = ".".join(tokens[:-1])
        operator_method_name = tokens[-1]

        operator_module = importlib.import_module(operator_module_name)
        operator_method = getattr(operator_module, operator_method_name)

        return operator_method(*args, **kwargs)

    @staticmethod
    def _start_operator_in_k8s_mode(
        operator_id,
        input_json=None,
        execution_mode=consts.EXECUTION_MODE_K8S,
        cpu_request=None,
        memory_request=None,
        storage_request=None,
        gpu_request=None,
    ):
        from .pipeline_manager import PipelineManager

        operator = PipelineManager.get_operator_by_id(operator_id)

        # Get the current operator job.
        current_job_info = Tracking.get_info_for_single_job(ExecutionContext.job_id)

        # Create child job for the target operator.
        # When creating the job, the following configs are inherited from its parent (current) operator.
        # * pipeline_name
        # * docker_image_repo
        # * docker_image_tag
        # * docker_image_digest
        # * owner
        # * tags
        # * ttl_after_finished
        # * notification_channel
        job_id = utils.create_job(
            execution_mode=execution_mode,
            pipeline_name=current_job_info["pipeline_name"],
            pipeline_params=json.dumps(input_json),
            docker_image_repo=current_job_info["docker_image_repo"],
            docker_image_tag=current_job_info["docker_image_tag"],
            docker_image_digest=current_job_info["docker_image_digest"],
            operator_id=operator_id,
            owner=current_job_info["owner"],
            tags=current_job_info["tags"],
            cpu_request=utils.get_first_available_value([cpu_request, operator.cpu_request]),
            memory_request=utils.get_first_available_value([memory_request, operator.memory_request]),
            storage_request=utils.get_first_available_value([storage_request, operator.storage_request]),
            gpu_request=utils.get_first_available_value([gpu_request, operator.gpu_request]),
            ttl_after_finished=current_job_info["ttl_after_finished"],
            notification_channel=current_job_info["notification_channel"],
            parent_job_id=ExecutionContext.job_id,
        )

        logging.info("Create sub job {} to run operator {}".format(job_id, operator_id))

        return job_id

    @staticmethod
    def _join_operator_in_k8s_mode(job_id):
        logging.info("Waiting for sub job {}".format(job_id))

        while True:
            k8s_job = KubernetesProxy.get_job(job_id)

            if k8s_job.status.succeeded:
                return True
            elif k8s_job.status.failed:
                raise Exception("Job {} failed!".format(job_id))

            time.sleep(60)

    @staticmethod
    def _get_operator_job_output(job_id):
        job_info = Tracking.get_info_for_single_job(job_id)
        return job_info.get("output")

    @staticmethod
    def start(
        operator_id,
        input_json=None,
        cpu_request=None,
        memory_request=None,
        storage_request=None,
        gpu_request=None,
    ):
        return Operator._start_operator_in_k8s_mode(
            operator_id=operator_id,
            input_json=input_json,
            execution_mode=ExecutionContext.execution_mode,
            cpu_request=cpu_request,
            memory_request=memory_request,
            storage_request=storage_request,
            gpu_request=gpu_request,
        )

    @staticmethod
    def join(job_id):
        if ExecutionContext.execution_mode == consts.EXECUTION_MODE_K8S:
            Operator._join_operator_in_k8s_mode(job_id)
            return Operator._get_operator_job_output(job_id)
        elif ExecutionContext.execution_mode == consts.EXECUTION_MODE_LOCAL:
            return Operator._get_operator_job_output(job_id)
        else:
            raise NotImplementedError()

    @staticmethod
    def run(operator_id, input_json=None):
        job_id = Operator.start(operator_id, input_json)
        return Operator.join(job_id)
