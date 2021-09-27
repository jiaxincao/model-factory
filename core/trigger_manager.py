from core import consts
from core.config import Config
from pymongo import MongoClient
import collections
import importlib
import json
import time


class TriggerManager:
    @classmethod
    def init(cls):
        cls.mongo_client = MongoClient(Config.MONGO_DB_ENDPOINT)
        cls.triggers = cls.mongo_client[consts.MODEL_FACTORY_DB_NAME][consts.MODEL_FACTORY_TRIGGERS_COLLECTION_NAME]

    @classmethod
    def validate_existance(cls, trigger_name):
        trigger_info = cls.load_info_for_trigger(trigger_name)
        assert trigger_info, "Trigger {} does not exist!".format(trigger_name)

    @classmethod
    def update_trigger(cls, trigger_class, trigger_name, owner, input_json, enabled=True):
        cls.triggers.find_one_and_update(
            {"_id" : trigger_name},
            {
                "$set": {
                    "owner": owner,
                    "trigger_class": trigger_class,
                    "enabled": enabled,
                    "update_timestamp": time.time(),
                    "input_json": input_json,
                    "last_failure_count": 0,
                }
            },
            upsert=True
        )

    @classmethod
    def rename_trigger(cls, trigger_name, new_trigger_name):
        trigger_info = cls.load_info_for_trigger(trigger_name)

        # Create a new trigger document.
        trigger_info["_id"] = new_trigger_name

        # Create a new trigger.
        cls.triggers.insert_one(trigger_info)

        # Delete the old trigger.
        cls.triggers.delete_one({"_id" : trigger_name})

    @classmethod
    def enable_trigger(cls, trigger_name):
        return cls.triggers.find_one_and_update(
            {"_id" : trigger_name},
            {
                "$set": {
                    "enabled": True,
                    "last_failure_count": 0,
                }
            },
        )

    @classmethod
    def disable_trigger(cls, trigger_name):
        return cls.triggers.find_one_and_update(
            {"_id" : trigger_name},
            {
                "$set": {
                    "enabled": False,
                }
            },
        )

    @classmethod
    def update_owner(cls, trigger_name, owner):
        return cls.triggers.find_one_and_update(
            {"_id" : trigger_name},
            {
                "$set": {
                    "owner": owner,
                }
            },
        )

    @classmethod
    def update_last_failure_count(cls, trigger_name, last_failure_count):
        return cls.triggers.find_one_and_update(
            {"_id" : trigger_name},
            {
                "$set": {
                    "last_failure_count": last_failure_count,
                }
            },
        )

    @classmethod
    def update_trigger_fields(cls, trigger_name, fields):
        return cls.triggers.find_one_and_update(
            {"_id" : trigger_name},
            {
                "$set": fields,
            },
        )

    @classmethod
    def delete_trigger(cls, trigger_name):
        return cls.triggers.delete_one(
            {"_id" : trigger_name},
        )

    @classmethod
    def load_info_for_all_triggers(cls):
        return list(cls.triggers.find())

    @classmethod
    def load_info_for_trigger(cls, trigger_name):
        return cls.triggers.find_one({"_id" : trigger_name})

    @classmethod
    def load_trigger(cls, trigger_info):
        triggers_module = importlib.import_module("core.triggers")
        trigger_cls = getattr(triggers_module, trigger_info["trigger_class"], None)

        return trigger_cls and trigger_cls(
            trigger_info,
            json.loads(trigger_info["input_json"]),
        )

    @classmethod
    def update_action_metadata(cls, trigger_name, action_metadata):
        cls.triggers.find_one_and_update(
            {"_id" : trigger_name},
            {"$set": {
                "action_metadata": action_metadata,
            }},
        )


TriggerManager.init()
