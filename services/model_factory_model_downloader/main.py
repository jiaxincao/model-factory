#!/usr/bin/env python3

from core.model_registry import ModelRegistry
from core.tracking import Tracking
from datetime import datetime
import click
import json
import logging
import os
import socket
import sys


@click.group()
def main():
    pass


@main.command()
@click.argument("model-id")
@click.argument("target-dir")
def download_model(model_id, target_dir):
    ModelRegistry.pull(model_id, target_dir)


@main.command()
@click.argument("model-name")
@click.argument("target-dir")
@click.option("--use-model-id-as-name", is_flag=True, help="Use model id as the file name.")
def download_model_by_name(model_name, target_dir, use_model_id_as_name):
    production_model_info = ModelRegistry.list_production_models([model_name])[0]
    model_id = production_model_info["model_id"]

    ModelRegistry.pull(model_id, target_dir)

    if use_model_id_as_name:
        os.rename(
            os.path.expanduser(os.path.join(target_dir, model_name)),
            os.path.expanduser(os.path.join(target_dir, model_id)),
        )

    Tracking.add_production_model_event(
        model_name=model_name,
        event_type="model_download",
        event_metadata={
            "hostname": socket.gethostname(),
            "model_id": model_id,
        },
    )

    logging.info(json.dumps({
        "timestamp": datetime.utcnow().isoformat(),
        "verb": "updated",
        "type": "deployment",
        "notes": "[Model ID: {}]".format(model_id),
        "name": "model_factory_model_downloader",
        "namespace": "model_factory_services",
    }))


if __name__ == '__main__':
    logging.basicConfig(
        format='[%(asctime)s] {%(filename)32s:%(lineno)-5d} %(levelname)8s - %(message)s',
        stream=sys.stdout,
        level=logging.INFO,
    )

    main()
