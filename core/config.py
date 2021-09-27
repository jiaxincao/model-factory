from core import consts as mf_consts
import configparser
import os


class Config:
    MONGO_DB_ENDPOINT = None
    MF_FRONTEND_ENDPOINT = None
    S3_BUCKET = None
    S3_ENDPOINT = None
    DOCKER_REGISTRY = None
    AWS_ACCESS_KEY_ID = None
    AWS_SECRET_ACCESS_KEY = None
    STORAGE_CLASS = None

    @classmethod
    def init(cls):
        config_parser = configparser.ConfigParser()
        config_parser.read(os.path.expanduser(mf_consts.MODEL_FACTORY_CONFIG_FILE))

        config_section = config_parser["default"] if "default" in config_parser else {}

        cls.MONGO_DB_ENDPOINT = config_section.get(
            "mongo_db_endpoint",
        )
        cls.MF_FRONTEND_ENDPOINT = config_section.get(
            "mf_frontend_endpoint",
        )
        cls.S3_BUCKET = config_section.get(
            "s3_bucket",
            "model-factory",
        )
        cls.S3_ENDPOINT = config_section.get(
            "s3_endpoint",
        )
        cls.DOCKER_REGISTRY = config_section.get(
            "docker_registry",
        )
        cls.AWS_ACCESS_KEY_ID = config_section.get(
            "aws_access_key_id",
        )
        cls.AWS_SECRET_ACCESS_KEY = config_section.get(
            "aws_secret_access_key",
        )
        cls.STORAGE_CLASS = config_section.get(
            "storage_class",
            "standard",
        )


Config.init()
