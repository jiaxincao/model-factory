from bson.objectid import ObjectId
from core import consts
from core.config import Config
from core.execution_context import ExecutionContext
from pymongo import MongoClient

import json
import logging
import pymongo
import time


class Tracking:
    @classmethod
    def init(cls):
        cls.mongo_client = MongoClient(Config.MONGO_DB_ENDPOINT)
        cls.jobs_collection = cls.mongo_client[consts.MODEL_FACTORY_DB_NAME][consts.MODEL_FACTORY_JOB_COLLECTION_NAME]
        cls.models = cls.mongo_client[consts.MODEL_FACTORY_DB_NAME][consts.MODEL_FACTORY_MODEL_REGISTRY]
        cls.prod_models = cls.mongo_client[consts.MODEL_FACTORY_DB_NAME][consts.MODEL_FACTORY_PROD_MODEL]

    @classmethod
    def create_job(
        cls,
        job_id,
        pipeline_name,
        pipeline_params,
        operator_id,
        pool,
        owner,
        cmd,
        cpu_request,
        memory_request,
        storage_request,
        gpu_request,
        ttl_after_finished,
        docker_image_repo=None,
        docker_image_tag=None,
        docker_image_digest=None,
        execution_mode=None,
        tags=None,
        creator_host=None,
        parent_job_id=None,
    ):
        cls.jobs_collection.insert({
            "_id": job_id,
            "job_id": job_id,
            "parent_job_id": parent_job_id,
            "pipeline_name": pipeline_name,
            "pipeline_params": pipeline_params,
            "operator_id": operator_id,
            "pool": pool,
            "owner": owner,
            "docker_image_repo": docker_image_repo,
            "docker_image_tag": docker_image_tag,
            "docker_image_digest": docker_image_digest,
            "execution_mode": execution_mode,
            "tags": tags,
            "creator_host": creator_host,
            "cmd": cmd,
            "pod_name": None,
            "ip_addr": None,
            "stage": "CREATED",
            "output": None,
            "ttl_after_finished": ttl_after_finished,
            "resources": {
                "cpu_request": cpu_request,
                "memory_request": memory_request,
                "storage_request": storage_request,
                "gpu_request": gpu_request,
            },
            "events": [],
            "creation_timestamp": time.time(),
            "start_timestamp": None,
            "completion_timestamp": None,
            "status": "pending",
            "exit_code": None,
            "exit_reason": None,
            "exception": None,
            "archived": False,  # check if a job is archived or not
            "exception": None,
        })

    @classmethod
    def get_info_for_single_job(cls, job_id):
        return cls.jobs_collection.find_one(
            {"job_id": job_id},
        )

    @classmethod
    def get_info_for_multi_jobs(cls, job_ids):
        return cls.jobs_collection.find(
            {"job_id": {"$in": job_ids}},
        )

    @classmethod
    def get_info_for_all_visiable_jobs(cls):
        return list(cls.jobs_collection.find(
            {"tags": {"$nin": ["hide"]}},
        ))

    @classmethod
    def get_info_for_all_jobs(cls):
        return cls.jobs_collection.find()

    @classmethod
    def get_info_for_jobs(cls, job_filter, job_fields=None):
        """
        Get job info, passing filter json dictionary in.
        """
        return list(cls.jobs_collection.find(job_filter, job_fields))

    @classmethod
    def get_job_stage(cls, job_id):
        job_obj = cls.jobs_collection.find_one(
            {"_id" : job_id},
        )
        return job_obj and job_obj["stage"]

    @classmethod
    def update_job_stage(cls, stage_name):
        cls.jobs_collection.find_one_and_update(
            {"_id" : ExecutionContext.job_id},
            {"$set": {"stage": stage_name}},
            upsert=True
        )

        cls.add_job_event("update_stage", {"stage_name": stage_name})

    @classmethod
    def update_job_fields(cls, job_id, fields):
        cls.jobs_collection.find_one_and_update(
            {"_id" : job_id},
            {"$set": fields},
            upsert=True
        )

    @classmethod
    def update_pod_name(cls, pod_name):
        cls.jobs_collection.find_one_and_update(
            {"_id" : ExecutionContext.job_id},
            {"$set": {"pod_name": pod_name}},
            upsert=True
        )

    @classmethod
    def tag_job(cls, job_id, tag):
        cls.jobs_collection.find_one_and_update(
            {"_id" : job_id},
            {"$addToSet": {"tags": tag}},
            upsert=True
        )

    @classmethod
    def untag_job(cls, job_id, tag):
        cls.jobs_collection.find_one_and_update(
            {"_id" : job_id},
            {"$pull": {"tags": tag}},
            upsert=True
        )

    @classmethod
    def update_job_output(cls, output):
        cls.jobs_collection.find_one_and_update(
            {"_id" : ExecutionContext.job_id},
            {"$set": {"output": output}},
            upsert=True
        )

    @classmethod
    def add_job_event(cls, event_type, event_metadata):
        cls.jobs_collection.find_one_and_update(
            {"_id" : ExecutionContext.job_id},
            {"$push": {
                "events": {
                    "timestamp": time.time(),
                    "type": event_type,
                    "metadata": event_metadata,
                }
            }},
            upsert=True
        )

    @classmethod
    def create_model(
        cls,
        model_id,
        model_name,
        job_id,
        timestamp,
        tags=[],
        metadata={},
    ):
        cls.models.insert({
            "_id": model_id,
            "model_name": model_name,
            "job_id": job_id,
            "timestamp": timestamp,
            "tags": tags,
            "metadata": json.dumps(metadata),
            "metric": {},
        })

    @classmethod
    def delete_model(cls, model_id):
        cls.models.delete_one(
            {"_id" : model_id},
        )

    @classmethod
    def update_model_metadata(cls, model_id, metadata):
        return cls.models.find_one_and_update(
            {"_id" : model_id},
            {"$set": {"metadata": json.dumps(metadata)}},
            upsert=True
        )

    @classmethod
    def get_info_for_single_model(cls, model_id):
        return cls.models.find_one(
            {"_id": model_id},
        )

    @classmethod
    def get_info_for_multi_models(cls, model_ids):
        return cls.models.find(
            {"_id": {"$in": model_ids}},
        )

    @classmethod
    def get_model_info_by_model_name(
        cls, model_name, sort_by_field=None
    ):
        res = cls.models.find(
            {"model_name": model_name},
        )
        if sort_by_field:
            res.sort(sort_by_field, pymongo.DESCENDING)
        return res

    @classmethod
    def get_info_for_models(
        cls,
        query_filter={},
        fields=None,
        sort_by_field=None,
    ):
        """
        query_filter: filter conditions
        field_filter: return specified field only
        example
        # filter only model_name = 'demo_model'
        query_filter = {
            model_name:'demo_model'
        }


        # only return results with _id and model_name
        fields = {
            model_name: 1
        }

        """
        if query_filter:
            mongo_qs = cls.models.find(
                query_filter,
                fields,
            )
        else:
            mongo_qs = cls.models.find(
                query_filter
            )

        if sort_by_field:
            mongo_qs.sort(sort_by_field, pymongo.DESCENDING)

        return list(mongo_qs)

    @classmethod
    def tag_model(cls, model_id, tag):
        cls.models.find_one_and_update(
            {"_id" : model_id},
            {"$addToSet": {"tags": tag}},
            upsert=True
        )

    @classmethod
    def untag_model(cls, model_id, tag):
        cls.models.find_one_and_update(
            {"_id" : model_id},
            {"$pull": {"tags": tag}},
            upsert=True
        )

    @classmethod
    def delete_model(cls, model_id):
        cls.models.delete_one(
            {"_id" : model_id},
        )

    @classmethod
    def promote_model(cls, model_id):
        model_info = cls.get_info_for_single_model(model_id)
        return cls.prod_models.find_one_and_update(
            {"_id" : model_info["model_name"]},
            {"$set": {"model_id": model_id}},
            upsert=True
        )

    @classmethod
    def add_production_model_event(cls, model_name, event_type, event_metadata):
        cls.prod_models.find_one_and_update(
            {"_id" : model_name},
            {"$push": {
                "events": {
                    "timestamp": time.time(),
                    "type": event_type,
                    "metadata": event_metadata,
                }
            }},
            upsert=True
        )

    @classmethod
    def list_production_models(cls, model_names):
        if model_names:
            return list(cls.prod_models.find(
                {"_id": {"$in": model_names}}
            ))
        else:
            return list(cls.prod_models.find())

    @classmethod
    def add_metric(cls, model_id, key, value, timestamp=None):
        if not timestamp:
            timestamp = time.time()
        metric_val = {
            "value": value,
            "timestamp": timestamp,
        }
        cls.models.find_one_and_update(
            {"_id": model_id},
            {"$addToSet": {"metric.{}".format(key): metric_val}},
        )


Tracking.init()
