from core import consts as mf_consts
from core import utils as core_utils
from core.config import Config
from core.kubernetes_proxy import KubernetesProxy
from core.tracking import Tracking

from datetime import datetime
import click
import logging
import os
import sys
import time


@click.group()
def main():
    pass


@main.command()
def sync_job_metadata():
    logging.info("Start syncing jobs metadata...")

    jobs_info = Tracking.get_info_for_jobs(
        job_filter={
            "execution_mode": "k8s",
            "status": {"$nin": ["succeeded", "failed", "deleted"]},
        },
    )

    logging.info("Syncing {} jobs...".format(len(jobs_info)))

    k8s_jobs = {
        k8s_job.metadata.labels.get("job_id", ""): k8s_job
        for k8s_job in KubernetesProxy.list_jobs().items
    }

    now = time.time()

    for job_info in jobs_info:
        job_id = job_info["_id"]

        try:
            logging.info("Scanning job {}".format(job_id))

            if now - job_info["creation_timestamp"] <= 60:
                logging.info("Job has been created for less than one minute. Skip syncing status.")
                continue

            # Update job status
            job_status = None
            job_exit_code = None
            job_exit_reason = None

            k8s_job = k8s_jobs.get(job_id)
            if not k8s_job:
                job_status = "deleted"
            elif k8s_job.status.succeeded:
                job_status = "succeeded"
            elif k8s_job.status.failed:
                job_status = "failed"

                # If job failed, get its exit code and reason.
                k8s_pod = KubernetesProxy.get_pod(job_id)
                if k8s_pod and k8s_pod.status.container_statuses:
                    terminated = k8s_pod.status.container_statuses[0].state.terminated
                    if terminated:
                        job_exit_code = terminated.exit_code
                        job_exit_reason = terminated.reason
                elif k8s_job.status.conditions:
                    job_exit_reason = k8s_job.status.conditions[-1].reason

            if job_status is None:
                continue

            fields = {
                "status": job_status,
                "exit_code": job_exit_code,
                "exit_reason": job_exit_reason,
            }

            logging.info("Updating job {}'s fields: {}".format(job_id, fields))

            Tracking.update_job_fields(job_id=job_id, fields=fields)
        except:
            logging.exception("Failed to archive job {}!".format(job_id))

    logging.info("Finished achiving jobs...")


if __name__ == '__main__':
    logging.basicConfig(
        format='[%(asctime)s] {%(filename)32s:%(lineno)-5d} %(levelname)8s - %(message)s',
        stream=sys.stdout,
        level=logging.INFO,
    )

    main()
