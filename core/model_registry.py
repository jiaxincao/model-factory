#!/usr/bin/env python3

from core import consts as mf_consts
from core import utils
from core.config import Config
from core.tracking import Tracking

import boto3
import logging
import os
import time
import uuid


class ModelRegistry:
    """
    Model registry provides a centralized management for model factory produced models.
    """

    @classmethod
    def register(cls, model_name, job_id, tags=[], metadata={}):
        model_id = "m-{}".format(uuid.uuid4())
        # Registry the model on the tracking db.
        logging.info("registering {} model_id {} at mongodb".format(
            model_name, model_id))
        Tracking.create_model(
            model_id=model_id,
            model_name=model_name,
            job_id=job_id,
            timestamp=time.time(),
            tags=tags,
            metadata=metadata,
        )

        return model_id

    @classmethod
    def push(
        cls,
        model_id,
        model_path,
    ):
        """
        Push a model to model registry.
        """
        assert os.path.exists(model_path), "Missing model file directory at {}".format(model_path)

        model_s3_key = cls.get_model_s3_key(model_id)
        model_s3_path = cls.get_model_s3_path(model_id)
        model_name = Tracking.get_info_for_single_model(model_id)["model_name"]
        packed_model_path = "{}.tar".format(model_name)

        logging.info("Start committing model {} from {} to {}".format(
            model_id,
            model_path,
            model_s3_path,
        ))

        # Pack the target model.
        cls._pack_model(model_path, model_name, packed_model_path)

        # Upload the packed model to s3.
        s3_client = boto3.client(
            's3',
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            endpoint_url=Config.S3_ENDPOINT,
        )

        s3_client.upload_file(
            packed_model_path,
            Config.S3_BUCKET,
            model_s3_key,
        )

        logging.info("Finished committing model {} from {} to {}".format(
            model_id,
            model_path,
            model_s3_path,
        ))

        # Clean up
        os.remove(packed_model_path)

    @classmethod
    def pull(cls, model_id, target_dir):
        """
        Pull a model from model registry to the target directory on your local file system.
        """
        model_info = Tracking.get_info_for_single_model(model_id)

        assert model_info, "Model {} not found!".format(model_id)

        target_model_dir = os.path.expanduser(target_dir)
        os.makedirs(target_model_dir, exist_ok=True)

        logging.info("Loading model {} from {} to {}".format(
            model_id,
            cls.get_model_s3_path(model_id),
            target_model_dir,
        ))

        target_model_tar_file = os.path.join(target_model_dir, "model.tar")
        s3_client = boto3.client('s3')
        s3_client.download_file(
            Bucket=Config.S3_BUCKET,
            Key=cls.get_model_s3_key(model_id),
            Filename=target_model_tar_file,
        )

        cls._unpack_model(target_model_tar_file, target_dir)
        return model_info

    @classmethod
    def delete_model(cls, model_id):
        """
        Delete a model from model registry.
        """
        # Upload the packed model to s3.
        s3_client = boto3.client('s3')
        s3_client.delete_object(
            Bucket=Config.S3_BUCKET,
            Key=cls.get_model_s3_key(model_id),
        )
        logging.info("Deleted {} from s3".format(cls.get_model_s3_path(model_id)))

        # Registry the model on the tracking db.
        Tracking.delete_model(
            model_id=model_id,
        )
        logging.info("Deleted metadata for {} from db".format(model_id))

    @classmethod
    def tag_model(cls, model_id, tag):
        Tracking.tag_model(model_id, tag)

    @classmethod
    def untag_model(cls, model_id, tag):
        Tracking.untag_model(model_id, tag)

    @classmethod
    def update_model_metadata(cls, model_id, metadata):
        return Tracking.update_model_metadata(model_id, metadata)

    @classmethod
    def promote_model(cls, model_id):
        # Promote model.
        Tracking.promote_model(model_id)

        # Add tracking information.
        model_info = Tracking.get_info_for_single_model(model_id)
        Tracking.add_production_model_event(model_info["model_name"], "promote", {"model_id": model_id})

        return True

    @classmethod
    def list_production_models(cls, model_names):
        return Tracking.list_production_models(model_names)

    @classmethod
    def get_info_for_model(cls, model_id):
        return Tracking.get_info_for_single_model(model_id)

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
        field_filter = {
            model_name: 1
        }

        """
        return Tracking.get_info_for_models(
            query_filter, fields, sort_by_field)

    @classmethod
    def get_model_s3_key(cls, model_id):
        return "{}/{}.tar".format(
            mf_consts.MODEL_FACTORY_MODELS_NAMESPACE,
            model_id,
        )

    @classmethod
    def get_model_s3_path(cls, model_id):
        return "s3://{}/{}".format(
            Config.S3_BUCKET,
            cls.get_model_s3_key(model_id),
        )

    @classmethod
    def _pack_model(cls, model_path, model_name, tar_path):
        model_path_basename = os.path.basename(model_path)

        if model_path_basename == model_name:
            utils.system("tar -cvf {} {}".format(
                tar_path,
                model_path,
            ))
        else:
            utils.system("ln -s {} {} && tar cvfh {} {} && rm {}".format(
                model_path,
                model_name,
                tar_path,
                model_name,
                model_name,
            ))

    @classmethod
    def _unpack_model(cls, model_tar_file, target_model_dir):
        utils.system("tar xvf {} -C {} && rm {}".format(
            model_tar_file,
            target_model_dir,
            model_tar_file,
        ))
