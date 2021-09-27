#!/usr/bin/env python3

from core.triggers import *

from core import consts
from core.config import Config
from core.trigger_manager import TriggerManager

import click
import logging
import sys
import traceback


@click.group()
def main():
    pass


@main.command()
def run_triggers():
    logging.info("Run triggers...")

    triggers_info = TriggerManager.load_info_for_all_triggers()

    for trigger_info in triggers_info:
        trigger_name = trigger_info["_id"]
        logging.info("Running trigger {}...".format(trigger_name))
        trigger_channel = trigger_info.get("notification_channel", None)

        try:
            if not trigger_info["enabled"]:
                logging.info("Trigger {} is disabled.".format(trigger_name))
                continue

            trigger = TriggerManager.load_trigger(trigger_info)

            trigger.exec()

            TriggerManager.update_last_failure_count(trigger_name, 0)
        except Exception:
            logging.exception("Failed on trigger {}!".format(trigger_name))

            # If the trigger has been failure for three times continuously, disable it.
            last_failure_count = trigger_info.get("last_failure_count", 0)
            TriggerManager.update_last_failure_count(trigger_name, last_failure_count + 1)
            if last_failure_count + 1 >= consts.TRIGGER_FAILURE_LIMIT:
                TriggerManager.disable_trigger(trigger_name)


if __name__ == '__main__':
    logging.basicConfig(
        format='[%(asctime)s] {%(filename)32s:%(lineno)-5d} %(levelname)8s - %(message)s',
        stream=sys.stdout,
        level=logging.INFO,
    )

    main()
