from core.kubernetes_proxy import KubernetesProxy
from core.model_registry import ModelRegistry
from services.model_factory_frontend.client import ModelFactoryFrontendClient

import click
import logging
import sys
import time


@click.group()
def main():
    pass


@main.command()
def autohide_model():
    models_info = ModelRegistry.get_info_for_models()

    now = time.time()
    for model_info in models_info:
        model_id = model_info["_id"]
        t = model_info["timestamp"]
        tags = model_info["tags"]

        if "hide" in tags or now - t < 7 * 24 * 3600:
            continue

        ModelRegistry.tag_model(model_id, "hide")
        logging.info("hide model {}".format(model_id))


@main.command()
def autohide_job():
    # Get active jobs
    k8s_jobs = KubernetesProxy.list_jobs()

    active_job_ids = set()
    for k8s_job in k8s_jobs.items:
        if not k8s_job.status.active:
            continue

        job_id = k8s_job.metadata.labels.get("job_id", "")
        active_job_ids.add(job_id)

    logging.info("The following jobs are still active: ")
    for active_job_id in active_job_ids:
        logging.info("* {}".format(active_job_id))

    # Check visible jobs.
    model_factory_frontend_client = ModelFactoryFrontendClient()
    jobs_info = model_factory_frontend_client.get_info_for_all_visiable_jobs()

    now = time.time()
    for job_info in jobs_info:
        job_id = job_info.get("job_id", None)

        if not job_id:
            continue

        if job_id in active_job_ids:
            logging.info("Skipping {}, since it is still active".format(job_id))
            continue

        last_active_time = job_info.get("completion_timestamp", None) or job_info.get("start_timestamp", None)

        if last_active_time and now - last_active_time > 7 * 24 * 3600:
            logging.info("Hiding {}".format(job_id))
            model_factory_frontend_client.tag_job(job_id, "hide")


if __name__ == '__main__':
    logging.basicConfig(
        format='[%(asctime)s] {%(filename)32s:%(lineno)-5d} %(levelname)8s - %(message)s',
        stream=sys.stdout,
        level=logging.INFO,
    )

    main()
