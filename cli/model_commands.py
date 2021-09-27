#!/usr/bin/env python3

from core import utils as core_utils
from core.model_registry import ModelRegistry
from core.termcolor import get_colored_text_by_hsv
from core.trigger_manager import TriggerManager
from core.triggers import *
from services.model_factory_frontend.client import ModelFactoryFrontendClient

from datetime import datetime
from treelib import Tree
from zlib import crc32
import click
import collections
import pytz
import re
import tabulate


@click.group(name="model")
def model():
    """
    Commands to manage model factory models
    """
    pass


@model.command(name="list")
@click.option("--tag", help="The tag filter.")
@click.option("--model_id", help="The model_id filter.")
@click.option("--model_name", help="The model_name filter.")
@click.option("-n", type=int, help="Only show the last n models.")
@click.option("--show-metadata", is_flag=True, help="Whether to show the model metadata.")
@click.option("--show-metric", is_flag=True, help="Whether to show the model metric.")
@click.option("--show-hidden", is_flag=True, help="Whether to show the hidden models.")
def list_models(tag, model_id, model_name, n, show_metadata, show_metric, show_hidden):
    """
    List all models
    """

    model_factory_frontend_client = ModelFactoryFrontendClient()
    models_info = model_factory_frontend_client.list_models()
    production_models_info = model_factory_frontend_client.list_production_models()
    production_model_ids = {production_model_info["model_id"] for production_model_info in production_models_info}

    header = [
        "Model ID",
        "Tags",
        "Model Name",
        "Job ID",
        "Production",
        "Creation Time",
        "Auto Rollout Deployments",
    ]

    if show_metadata:
        header.append("Metadata")
    if show_metric:
        header.append("Metric")

    model_auto_rollout_deployments = collections.defaultdict(set)
    for db_trigger_info in TriggerManager.load_info_for_all_triggers():
        trigger = TriggerManager.load_trigger(db_trigger_info)
        if not isinstance(trigger, ModelServingRolloutTrigger):
            continue
        model_auto_rollout_deployments[trigger.model_name].add("{}.{}".format(
            trigger.deployment_namespace,
            trigger.deployment_name,
        ))

    table = []
    for model_info in models_info:
        cur_model_id = model_info.get("_id", None)

        if not cur_model_id:
            continue

        tags = model_info.get('tags', []) if model_info else []
        cur_model_name = model_info.get("model_name", "")
        job_id = model_info.get('job_id', "")
        creation_time = model_info.get("timestamp", None) and datetime.utcfromtimestamp(
            float(model_info["timestamp"])
        ).replace(tzinfo=pytz.utc, microsecond=0)

        if cur_model_id not in production_model_ids and ("hide" in tags and not show_hidden):
            continue

        if tag and tag not in tags:
            continue

        if model_id and model_id != cur_model_id:
            continue

        if model_name and model_name != cur_model_name:
            continue

        model_color = float(crc32(cur_model_name.encode()) & 0xffffffff) / 2**32

        auto_rollout_deployments = ",".join(
            sorted(model_auto_rollout_deployments.get(cur_model_name, []))
        ) if cur_model_id in production_model_ids else ""

        row = [
            get_colored_text_by_hsv(0.4, 0.8, 0.7, cur_model_id),
            get_colored_text_by_hsv(0.55, 0.8, 0.7, ", ".join(tags)),
            get_colored_text_by_hsv(model_color, 0.8, 0.7, cur_model_name),
            get_colored_text_by_hsv(0.15, 0.8, 0.7, job_id),
            get_colored_text_by_hsv(0.45, 0.8, 0.7, "PROD" if cur_model_id in production_model_ids else ""),
            get_colored_text_by_hsv(0.2, 0.8, 0.7, creation_time),
            get_colored_text_by_hsv(0.05, 0.8, 0.7, auto_rollout_deployments),
        ]

        if show_metadata:
            metadata = model_info.get("metadata", None)
            row.append(
                get_colored_text_by_hsv(0.35, 0.8, 0.7, metadata),
            )
        if show_metric:
            metric = model_info.get("metric", None)
            row.append(
                get_colored_text_by_hsv(0.65, 0.8, 0.7, metric),
            )

        table.append(row)

    print(tabulate.tabulate(table[-n:] if n else table, header, tablefmt="pretty"))


@model.command(name="delete")
@click.argument("model-id")
def delete(model_id):
    """
    Delete a model.
    """
    model_factory_frontend_client = ModelFactoryFrontendClient()
    model_factory_frontend_client.delete_model(model_id)

    print("Model {} deleted!".format(model_id))


@model.command(name="tag")
@click.argument("model-id")
@click.argument("tag")
def tag(model_id, tag):
    """
    Add a tag to a model.
    """
    assert isinstance(model_id, str), "model_id must be a string!"

    model_factory_frontend_client = ModelFactoryFrontendClient()
    model_factory_frontend_client.tag_model(model_id, tag)


@model.command(name="untag")
@click.argument("model-id")
@click.argument("tag")
def untag(model_id, tag):
    """
    Remove a tag from a model.
    """
    assert isinstance(model_id, str), "model_id must be a string!"

    model_factory_frontend_client = ModelFactoryFrontendClient()
    model_factory_frontend_client.untag_model(model_id, tag)



@model.command(name="log")
@click.argument("model-id")
def log(model_id):
    """
    Show job logs for a model.
    """
    model_factory_frontend_client = ModelFactoryFrontendClient()
    model_info = model_factory_frontend_client.get_model_by_id(model_id)
    job_id = model_info["job_id"]

    job_info = model_factory_frontend_client.get_info_for_single_job(job_id)

    is_archived = job_info.get("archived", False)

    if not is_archived:
        job_log = model_factory_frontend_client.get_k8s_job_log(job_id)
    else:
        job_log = model_factory_frontend_client.get_archived_job_log(job_id)

    if job_log:
        print(job_log)
    else:
        print("Job {} has no log.".format(job_id))


@model.command(name="promote")
@click.argument("model-id")
def promote(model_id):
    """
    Promote a model for production usage.
    """
    model_factory_frontend_client = ModelFactoryFrontendClient()
    model_factory_frontend_client.promote_model(model_id)

    print("Model {} has been promoted for production usage.".format(model_id))


@model.command(name="prod-events")
@click.argument("model-name")
@click.option("--event-types")
def prod_events(model_name, event_types):
    """
    Present a production information for a model.
    """
    event_types = event_types.split(",") if event_types else []

    model_factory_frontend_client = ModelFactoryFrontendClient()
    prod_model_info = model_factory_frontend_client.list_production_models([model_name])[0]

    tree = Tree()

    tree.create_node(
        tag=get_colored_text_by_hsv(0.1, 0.5, 0.9, "Production model {} events".format(model_name)),
        identifier="events",
    )

    for i, event in enumerate(prod_model_info["events"]):
        if event_types and event["type"] not in event_types:
            continue

        type_color = float(crc32(event["type"].encode()) & 0xffffffff) / 2**32

        node_id = "event_{:08d}".format(i)
        tree.create_node(
            tag="{} ({})".format(
                get_colored_text_by_hsv(type_color, 0.5, 1, event["type"]),
                get_colored_text_by_hsv(type_color, 0.5, 0.9, datetime.utcfromtimestamp(event["timestamp"]).replace(tzinfo=pytz.utc)),
            ),
            identifier=node_id,
            parent="events",
        )

        for k, v in event["metadata"].items():
            tree.create_node(
                tag="{}: {}".format(
                    get_colored_text_by_hsv(type_color, 0.3, 0.8, k),
                    get_colored_text_by_hsv(type_color, 0.3, 1, v),
                ),
                identifier="{}_{}".format(node_id, k),
                parent=node_id,
            )

    tree.show(key=lambda node: node._identifier)
