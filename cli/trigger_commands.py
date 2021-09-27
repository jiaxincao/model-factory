#!/usr/bin/env python3

from core.triggers import *

from core import utils as core_utils
from core.termcolor import get_colored_text_by_hsv
from core.trigger_manager import TriggerManager
from datetime import datetime
from . import job_commands
from services.model_factory_frontend.client import ModelFactoryFrontendClient

import click
import json
import pytz
import tabulate


def _delete_trigger_jobs(trigger_name):
    model_factory_frontend_client = ModelFactoryFrontendClient()

    jobs_info = model_factory_frontend_client.get_info_for_jobs(
        {"tags": {"$all": [trigger_name, "trigger_job"], "$nin": ["hide"]}},
        {"events": 0},
    )

    trigger_job_ids = [job_info["_id"] for job_info in jobs_info]

    for k8s_job in model_factory_frontend_client.list_all_k8s_jobs().items:
        job_id = k8s_job.metadata.labels.get("job_id", None)

        if job_id not in trigger_job_ids:
            continue

        print("Deleting job {}...".format(job_id))

        model_factory_frontend_client.delete_k8s_job(job_id)

    for job_info in jobs_info:
        model_factory_frontend_client.tag_job(job_info["_id"], "hide")


@click.group(name="trigger")
def trigger():
    """
    Commands to manage model-factory triggers.
    """
    pass


@trigger.command(name="create")
@click.argument("trigger_name")
@click.argument("trigger_class")
@click.option("--owner", default=core_utils.get_current_user(), help="The trigger owner.")
@click.option("--input-json", "-i", help="The input json.")
@click.option("--input-json-file", "-f", help="The input json file.")
@click.option("--disabled", is_flag=True, help="Disable the trigger after creation.")
@click.option("--build-image", is_flag=True, help="Build image (if the trigger needs it).")
def create_trigger(trigger_name, trigger_class, owner, input_json, input_json_file, disabled, build_image):
    """
    Create a trigger.
    """
    assert input_json or input_json_file, "You have to provide either input-json or input-json-file!"

    # If trigger file is provided, use the content as the trigger code.
    if input_json_file:
        with open(input_json_file, "r") as fp:
            input_json = fp.read()

    # Validate if it can be parsed.
    json.loads(input_json)

    if not build_image:
        # Create the trigger.
        TriggerManager.update_trigger(
            trigger_name=trigger_name,
            trigger_class=trigger_class,
            owner=core_utils.get_current_user(),
            input_json=input_json,
            enabled=not disabled,
        )
    else:
        # Create the trigger with enabled flag as false.
        TriggerManager.update_trigger(
            trigger_name=trigger_name,
            trigger_class=trigger_class,
            owner=core_utils.get_current_user(),
            input_json=input_json,
            enabled=False,
        )

        # Build the image.
        trigger_info = TriggerManager.load_info_for_trigger(trigger_name)
        trigger = TriggerManager.load_trigger(trigger_info)
        trigger.build_image()

        # Enable the trigger if needed.
        if not disabled:
            TriggerManager.update_trigger(
                trigger_name=trigger_name,
                trigger_class=trigger_class,
                owner=core_utils.get_current_user(),
                input_json=input_json,
                enabled=True,
            )


    print("Trigger {} added.".format(trigger_name))

@trigger.command(name="rename")
@click.argument("trigger_name")
@click.argument("new_trigger_name")
def rename_trigger(trigger_name, new_trigger_name):
    """
    Rename the target trigger.
    """
    # Validate trigger existance.
    TriggerManager.validate_existance(trigger_name)

    TriggerManager.rename_trigger(
        trigger_name=trigger_name,
        new_trigger_name=new_trigger_name,
    )
    print("Trigger {} renamed as {}.".format(trigger_name, new_trigger_name))


@trigger.command(name="enable")
@click.argument("trigger_name")
def enable_trigger(trigger_name):
    """
    Enable the target trigger.
    """
    # Validate trigger existance.
    TriggerManager.validate_existance(trigger_name)

    TriggerManager.enable_trigger(
        trigger_name=trigger_name,
    )
    print("Trigger {} enabled.".format(trigger_name))


@trigger.command(name="disable")
@click.argument("trigger_name")
def disable_trigger(trigger_name):
    """
    Disable the target trigger.
    """
    # Validate trigger existance.
    TriggerManager.validate_existance(trigger_name)

    TriggerManager.disable_trigger(
        trigger_name=trigger_name,
    )
    print("Trigger {} disabled.".format(trigger_name))


@trigger.command(name="update-owner")
@click.argument("trigger_name")
@click.argument("owner")
def update_owner(trigger_name, owner):
    """
    Update the owner of the target trigger.
    """
    # Validate trigger existance.
    TriggerManager.validate_existance(trigger_name)

    TriggerManager.update_owner(
        trigger_name=trigger_name,
        owner=owner,
    )
    print("Trigger {} owner updated.".format(trigger_name))


@trigger.command(name="delete")
@click.argument("trigger_name")
@click.option("--delete-jobs", is_flag=True, help="Delete jobs scheduled for this trigger.")
def delete_trigger(trigger_name, delete_jobs):
    """
    Delete a trigger.
    """
    # Validate trigger existance.
    TriggerManager.validate_existance(trigger_name)

    TriggerManager.delete_trigger(trigger_name)

    print("Trigger {} delete.".format(trigger_name))

    if delete_jobs:
        _delete_trigger_jobs(trigger_name)


@trigger.command(name="reset")
@click.argument("trigger_name")
@click.option("--delete-jobs", is_flag=True, help="Delete jobs scheduled for this trigger.")
def reset_trigger(trigger_name, delete_jobs):
    """
    Reset the trigger to its initial state.
    """
    # Validate trigger existance.
    TriggerManager.validate_existance(trigger_name)

    if delete_jobs:
        _delete_trigger_jobs(trigger_name)

    TriggerManager.update_action_metadata(trigger_name, {})


@trigger.command(name="list")
def list_triggers():
    """
    List triggers.
    """
    triggers_info = TriggerManager.load_info_for_all_triggers()

    header = ["Name", "Owner", "Trigger Class", "Update Time", "Enabled"]
    table_data = []

    for trigger_info in triggers_info:
        v = 0.9 if trigger_info["enabled"] else 0.7

        table_data.append([
            get_colored_text_by_hsv(0.4, 0.8, v, trigger_info["_id"]),
            get_colored_text_by_hsv(0.05, 0.8, v, trigger_info["owner"]),
            get_colored_text_by_hsv(0.9, 0.8, v, trigger_info["trigger_class"]),
            get_colored_text_by_hsv(0.1, 0.5, v, datetime.utcfromtimestamp(trigger_info["update_timestamp"]).replace(tzinfo=pytz.utc)),
            get_colored_text_by_hsv(0.45, 0.8, v, trigger_info["enabled"]),
        ])

    print(tabulate.tabulate(table_data, header, tablefmt="pretty"))


@trigger.command(name="list-jobs")
@click.argument("trigger_name")
@click.option("-o", "--output", type=click.Choice(['regular', 'full', 'short']), default="regular", help="The output format.")
@click.pass_context
def list_jobs(ctx, trigger_name, output):
    """
    List jobs.
    """
    ctx.invoke(
        job_commands.list,
        owner="*",
        tag=trigger_name,
        output=output,
    )


@trigger.command(name="force-run")
@click.argument("trigger_name")
def force_run_trigger(trigger_name):
    """
    Forcefully execute a trigger.
    """
    # Validate trigger existance.
    TriggerManager.validate_existance(trigger_name)

    print("Forcefully executing trigger for {}...".format(trigger_name))

    trigger_info = TriggerManager.load_info_for_trigger(trigger_name)
    trigger = TriggerManager.load_trigger(trigger_info)

    print("Triggering action for {}...".format(trigger.name))
    trigger.do_exec()

    print("Trigger job executed.")


@trigger.command(name="run")
@click.argument("trigger_name")
def run_trigger(trigger_name):
    """
    Execute a trigger.
    """
    # Validate trigger existance.
    TriggerManager.validate_existance(trigger_name)

    print("Running trigger for {}...".format(trigger_name))

    trigger_info = TriggerManager.load_info_for_trigger(trigger_name)
    trigger = TriggerManager.load_trigger(trigger_info)

    trigger.exec()


@trigger.command(name="dump")
@click.argument("trigger_name")
def dump_trigger(trigger_name):
    """
    Dump the python code for the trigger.
    """
    # Validate trigger existance.
    TriggerManager.validate_existance(trigger_name)

    trigger_info = TriggerManager.load_info_for_trigger(trigger_name)

    assert trigger_info is not None, "Trigger {} not found!".format(trigger_name)

    print(json.dumps(json.loads(trigger_info["input_json"]), indent=4))


@trigger.command(name="update-input-json")
@click.argument("trigger_name")
@click.option("--input-json", "-i", help="The input json.")
@click.option("--input-json-file", "-f", help="The input json file.")
def update_input_json(trigger_name, input_json, input_json_file):
    """
    Update the trigger's json input.
    """
    assert input_json or input_json_file, "You have to provide either input-json or input-json-file!"

    # Validate trigger existance.
    TriggerManager.validate_existance(trigger_name)

    # If trigger file is provided, use the content as the trigger code.
    if input_json_file:
        with open(input_json_file, "r") as fp:
            input_json = fp.read()

    # Validate if it can be parsed.
    json.loads(input_json)

    # Update input json
    TriggerManager.update_trigger_fields(
        trigger_name=trigger_name,
        fields={
            "input_json": input_json
        }
    )

    print("Trigger {} input updated.".format(trigger_name))
