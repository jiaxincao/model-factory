from core import consts
from core import utils as core_utils
from core.kubernetes_proxy import KubernetesProxy
from core.parameter import Parameter
from core.tracking import Tracking
from core.trigger_manager import TriggerManager
from croniter import croniter
from datetime import datetime
from services.model_factory_frontend.client import ModelFactoryFrontendClient

import functools
import json
import logging
import math
import time


################################################################################
# Trigger init decorator.
################################################################################
def trigger_init(input_schema):
    def _trigger_init(init_func):
        def execute_init_func(self, trigger_info, params):
            params = core_utils.construct_params(
                operator_input_schema=input_schema,
                operator_params=params,
                allow_extra_keys=False,
                pass_extra_keys=True,
            )
            return init_func(self, trigger_info, params)

        return functools.wraps(init_func)(execute_init_func)
    return _trigger_init


################################################################################
# Trigger base class.
################################################################################

class Trigger:
    def __init__(self, trigger_info):
        self.trigger_info = trigger_info

    @property
    def name(self):
        return self.trigger_info["_id"]

    @property
    def owner(self):
        return self.trigger_info["owner"]

    @property
    def enabled(self):
        return self.trigger_info["enabled"]

    def build_image(self):
        pass

    def get_extra_tags(self):
        return ["trigger_job", self.name]

    def exec(self):
        raise NotImplementedError()

    def update_action_metadata(self, action_metadata):
        logging.info("Update trigger metadata with {}".format(action_metadata))
        TriggerManager.update_action_metadata(self.name, action_metadata)


################################################################################
# Condition triggers.
################################################################################

class ConditionTrigger(Trigger):
    def is_ready(self):
        raise NotImplementedError()

    def do_exec(self):
        raise NotImplementedError()

    def exec(self):
        if not self.is_ready():
            logging.info("Trigger {} is not ready yet.".format(self.name))
            return

        logging.info("Do execute trigger {}.".format(self.name))
        return self.do_exec()


class CronTrigger(ConditionTrigger):
    @trigger_init(
        input_schema={
            Parameter(name="schedule"),
            Parameter(name="pipeline_name"),
            Parameter(name="operator_id"),
            Parameter(name="docker_image_repo"),
            Parameter(name="docker_image_tag", default=None, mandatory=False),
            Parameter(name="start_date", default=None, mandatory=False),
            Parameter(name="tags", default=None, mandatory=False),
            Parameter(name="pipeline_params", default=None, mandatory=False),
            Parameter(name="cpu_request", default=None, mandatory=False),
            Parameter(name="memory_request", default=None, mandatory=False),
            Parameter(name="storage_request", default=None, mandatory=False),
            Parameter(name="gpu_request", default=None, mandatory=False),
            Parameter(name="ttl_after_finished", default=43200, mandatory=False),
            Parameter(name="pool", default=None, mandatory=False),
            Parameter(name="active_deadline_seconds", default=None, mandatory=False),
        },
    )
    def __init__(self, trigger_info, params):
        super().__init__(trigger_info)

        self.schedule = params["schedule"]
        self.pipeline_name = params["pipeline_name"]
        self.operator_id = params["operator_id"]
        self.docker_image_repo = params["docker_image_repo"]
        self.docker_image_tag = params["docker_image_tag"]
        self.start_date = params["start_date"] and datetime.strptime(params["start_date"], "%Y-%m-%d")
        self.tags = params["tags"].split(',') if params["tags"] else []
        self.pipeline_params = params["pipeline_params"] or {}
        self.cpu_request = params["cpu_request"]
        self.memory_request = params["memory_request"]
        self.storage_request = params["storage_request"]
        self.gpu_request = params["gpu_request"]
        self.ttl_after_finished = params["ttl_after_finished"]
        self.pool = params["pool"]
        self.active_deadline_seconds = params["active_deadline_seconds"]

    def build_image(self):
        core_utils.build_image(
            pipeline_name=self.pipeline_name,
            image_tag=self.docker_image_tag,
            push=True,
        )

    def is_ready(self):
        action_metadata = self.trigger_info.get("action_metadata", {})
        last_action_time = action_metadata.get("last_action_time", 0)

        cron = croniter(self.schedule, start_time=last_action_time)
        next_ready_time = cron.get_next()
        now = time.time()

        logging.info("Next ready time is {}".format(datetime.fromtimestamp(next_ready_time)))

        return next_ready_time <= now

    def do_exec(self):
        job_id = core_utils.create_job(
            pipeline_name=self.pipeline_name,
            pipeline_params=json.dumps(self.pipeline_params),
            docker_image_repo=self.docker_image_repo,
            docker_image_tag=self.docker_image_tag,
            operator_id=self.operator_id,
            owner="trigger_service",
            tags=self.get_extra_tags() + self.tags,
            cpu_request=self.cpu_request,
            memory_request=self.memory_request,
            storage_request=self.storage_request,
            gpu_request=self.gpu_request,
            ttl_after_finished=self.ttl_after_finished,
            pool=self.pool,
            active_deadline_seconds=self.active_deadline_seconds,
        )

        self.update_action_metadata({"job_id": job_id, "last_action_time": time.time()})


class ActiveTagJobTrigger(ConditionTrigger):
    @trigger_init(
        input_schema={
            Parameter(name="active_tag"),
            Parameter(name="pipeline_name"),
            Parameter(name="docker_image_repo"),
            Parameter(name="docker_image_tag", default=None, mandatory=False),
            Parameter(name="tags", default=None, mandatory=False),
            Parameter(name="pipeline_params", default=None, mandatory=False),
            Parameter(name="cpu_request", default=None, mandatory=False),
            Parameter(name="memory_request", default=None, mandatory=False),
            Parameter(name="storage_request", default=None, mandatory=False),
            Parameter(name="gpu_request", default=None, mandatory=False),
            Parameter(name="ttl_after_finished", default=43200, mandatory=False),
            Parameter(name="operator_id", default=None, mandatory=False),
        },
    )
    def __init__(self, trigger_info, params):
        super().__init__(trigger_info)

        self.active_tag = params["active_tag"]
        self.pipeline_name = params["pipeline_name"]
        self.docker_image_repo = params["docker_image_repo"]
        self.docker_image_tag = params["docker_image_tag"]
        self.pipeline_params = params["pipeline_params"] or {}
        self.tags = params["tags"].split(',') if params["tags"] else []
        self.cpu_request = params["cpu_request"]
        self.memory_request = params["memory_request"]
        self.storage_request = params["storage_request"]
        self.gpu_request = params["gpu_request"]
        self.ttl_after_finished = params["ttl_after_finished"]
        self.operator_id = params["operator_id"]

    def is_ready(self):
        # cooldown for 5 minutes
        action_metadata = self.trigger_info.get("action_metadata", {})
        last_action_time = action_metadata.get("last_action_time", 0)

        now = time.time()
        if now - last_action_time < 300:
            logging.info(
                "Trigger in cool down. Last execution timestamp is {}".format(
                    last_action_time
                ))
            return False

        # Check if there is any active job.
        model_factory_frontend_client = ModelFactoryFrontendClient()
        active_tag_jobs = model_factory_frontend_client.get_info_for_jobs(
            job_filter={
                "status": {"$nin": ["succeeded", "failed", "deleted"]},
                "tags": self.active_tag,
                "execution_mode": "k8s",
            }
        )

        logging.info("There are active jobs: {}".format(
            ",".join([job["_id"] for job in active_tag_jobs])
        ))
        return not bool(active_tag_jobs)

    def do_exec(self):
        job_id = core_utils.create_job(
            pipeline_name=self.pipeline_name,
            pipeline_params=json.dumps(self.pipeline_params),
            docker_image_repo=self.docker_image_repo,
            docker_image_tag=self.docker_image_tag,
            operator_id=self.operator_id,
            tags=self.get_extra_tags() + [self.active_tag] + self.tags,
            owner="trigger_service",
            cpu_request=self.cpu_request,
            memory_request=self.memory_request,
            storage_request=self.storage_request,
            gpu_request=self.gpu_request,
            ttl_after_finished=self.ttl_after_finished,
        )

        self.update_action_metadata({"job_id": job_id, "last_action_time": time.time()})


class ModelServingRolloutTrigger(ConditionTrigger):
    @trigger_init(
        input_schema=[
            Parameter(name="model_name"),
            Parameter(name="deployment_namespace"),
            Parameter(name="deployment_name"),
            Parameter(name="initial_deploy", default=False, mandatory=False),
            Parameter(name="at_channel", default=False, mandatory=False),
        ],
    )
    def __init__(self, trigger_info, params):
        super().__init__(trigger_info)

        self.deployment_namespace = params["deployment_namespace"]
        self.deployment_name = params["deployment_name"]
        self.model_name = params["model_name"]
        self.initial_deploy = params["initial_deploy"]
        self.at_channel = params["at_channel"]

    def is_ready(self):
        action_metadata = self.trigger_info.get("action_metadata", {})
        model_factory_frontend_client = ModelFactoryFrontendClient()

        production_models = model_factory_frontend_client.list_production_models(
            model_names=[self.model_name],
        )

        if not production_models:
            return False

        production_model = production_models[0]

        self.current_model_id = action_metadata.get("model_id")
        self.next_model_id = production_model["model_id"]

        if self.current_model_id is None:
            if self.initial_deploy:
                return True
            else:
                self.update_action_metadata({"model_id": self.next_model_id})
                return False
        else:
            return self.current_model_id != self.next_model_id

    def do_exec(self):
        KubernetesProxy.restart_deployment(
            namespace=self.deployment_namespace,
            deployment=self.deployment_name,
        )

        logging.info(json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "verb": "updated",
            "type": "model_serving_rollout",
            "notes": "[New Model ID: {}, Old Model ID: {}]".format(
                self.next_model_id,
                self.current_model_id or "Unknown",
            ),
            "name": "model_factory_trigger_service",
            "namespace": "model_factory_services",
        }))

        Tracking.add_production_model_event(
            model_name=self.model_name,
            event_type="trigger_deployment_restart",
            event_metadata={
                "deployment_namespace": self.deployment_namespace,
                "deployment_name": self.deployment_name,
                "old_model_id": self.current_model_id or "Unknown",
                "new_model_id": self.next_model_id,
            },
        )

        self.update_action_metadata({"model_id": self.next_model_id})


################################################################################
# Other triggers.
################################################################################
class BackfillCronTrigger(Trigger):
    @trigger_init(
        input_schema=[
            Parameter(name="schedule"),
            Parameter(name="pipeline_name"),
            Parameter(name="docker_image_repo"),
            Parameter(name="docker_image_tag", default=None),
            Parameter(name="start_date", default=None),
            Parameter(name="end_date", default=None),
            Parameter(name="backfill_hours", default=3),
            Parameter(name="tags", default=None),
            Parameter(name="pipeline_params", default=None),
            Parameter(name="cpu_request", default=None),
            Parameter(name="memory_request", default=None),
            Parameter(name="storage_request", default=None),
            Parameter(name="gpu_request", default=None),
            Parameter(name="pool", default=None),
            Parameter(name="ttl_after_finished", default=43200),
        ],
    )
    def __init__(self, trigger_info, params):
        super().__init__(trigger_info)

        self.schedule = params["schedule"]
        self.pipeline_name = params["pipeline_name"]
        self.docker_image_repo = params["docker_image_repo"]
        self.docker_image_tag = params["docker_image_tag"]
        self.start_date = params["start_date"] and datetime.strptime(params["start_date"], "%Y-%m-%d")
        self.end_date = params["end_date"] and datetime.strptime(params["end_date"], "%Y-%m-%d")
        self.tags = params["tags"].split(',') if params["tags"] else []
        self.backfill_hours = params["backfill_hours"]
        self.pipeline_params = params["pipeline_params"] or {}
        self.cpu_request = params["cpu_request"]
        self.memory_request = params["memory_request"]
        self.storage_request = params["storage_request"]
        self.gpu_request = params["gpu_request"]
        self.pool = params["pool"]
        self.ttl_after_finished = params["ttl_after_finished"]

    def build_image(self):
        core_utils.build_image(
            pipeline_name=self.pipeline_name,
            image_tag=self.docker_image_tag,
            push=True,
        )

    def exec(self):
        action_metadata = self.trigger_info.get("action_metadata", {})

        execution_history = action_metadata.get("history", {})

        curr_date = max(
            self.start_date.timestamp() if self.start_date else 0,
            time.time() - self.backfill_hours * 3600,
        )
        now = time.time()

        cron = croniter(self.schedule, start_time=curr_date)

        self.scheduled_jobs = []
        while True:
            next_ready_time = cron.get_next()

            if next_ready_time > now:
                break

            if self.end_date and next_ready_time > self.end_date.timestamp():
                break

            trigger_date_tag = "date_{}".format(
                datetime.fromtimestamp(next_ready_time).strftime("%Y_%m_%d_%H_%M_%S")
            )

            logging.info("Checking {}".format(trigger_date_tag))

            job_id = execution_history.get(trigger_date_tag, None)
            if job_id:
                logging.info("Job exists {}".format(job_id))
                continue

            logging.info("scheduling job at {}".format(datetime.fromtimestamp(next_ready_time)))

            self.pipeline_params["datetime"] = next_ready_time

            job_id = core_utils.create_job(
                pipeline_name=self.pipeline_name,
                pipeline_params=json.dumps(self.pipeline_params),
                docker_image_repo=self.docker_image_repo,
                docker_image_tag=self.docker_image_tag,
                tags=self.get_extra_tags() + [trigger_date_tag] + self.tags,
                owner="trigger_service",
                cpu_request=self.cpu_request,
                memory_request=self.memory_request,
                storage_request=self.storage_request,
                gpu_request=self.gpu_request,
                ttl_after_finished=self.ttl_after_finished,
                pool=self.pool,
            )

            execution_history[trigger_date_tag] = job_id

            self.scheduled_jobs.append(job_id)

        if not self.scheduled_jobs:
            return

        action_metadata["history"] = execution_history

        self.update_action_metadata(action_metadata)
