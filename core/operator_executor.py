from core import consts
from core import utils as core_utils
from core.execution_context import ExecutionContext
from core.pipeline_manager import PipelineManager
from core.tracking import Tracking
import click
import importlib
import json
import logging
import os
import socket
import sys
import time
import traceback


@click.group()
def main():
    pass


@main.command("execute-operator", context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True,
))
@click.argument("job-id")
@click.argument("operator-path")
@click.option("--operator-params", default="{}")
@click.option("--cpu", default=1, type=int)
@click.option("--execution-mode", default="k8s")
def execute_pipeline_operator(job_id, operator_path, operator_params, cpu, execution_mode=consts.EXECUTION_MODE_K8S):
    try:
        logging.basicConfig(
            format='[%(asctime)s] {%(filename)32s:%(lineno)-5d} %(levelname)8s - %(message)s',
            stream=sys.stdout,
            level=logging.INFO,
        )

        model_factory_base_dir = os.path.dirname(os.path.dirname(__file__))

        # Set up execution context.
        ExecutionContext.job_id = job_id
        ExecutionContext.cpu = cpu
        ExecutionContext.execution_mode = execution_mode

        # Starting ssh server.
        os.system("service ssh start")

        # Get local ip address.
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)

        # Init tracking db.
        Tracking.update_job_stage("STARTED")
        Tracking.update_pod_name(socket.gethostname())
        Tracking.update_job_fields(
            job_id=job_id,
            fields={
                "status": "running",
                "start_timestamp": time.time(),
                "ip_addr": local_ip,
            },
        )

        # Get the operator.
        operator = PipelineManager.get_operator_by_id(operator_path)

        # Create parameters based on the default params and the input params.
        params = core_utils.construct_params(
            operator.input_schema,
            json.loads(operator_params),
        )

        # Update the start time.
        logging.info("Executing operator {} with params \"{}\"".format(operator_path, params))

        output = operator(params)

        # Update the job output.
        if output is not None:
            Tracking.update_job_output(output)

        # Update the job stage.
        Tracking.update_job_stage("DONE")

        logging.info("Finish executing job {}".format(job_id))

        # Update the end time.
        Tracking.update_job_fields(
            job_id=job_id,
            fields={
                "completion_timestamp": time.time(),
                "status": "succeeded",
            },
        )
    except:
        Tracking.update_job_fields(
            job_id=job_id,
            fields={
                "completion_timestamp": time.time(),
                "status": "failed",
                "exception": traceback.format_exc(),
            },
        )
        raise


if __name__ == '__main__':
    main()
