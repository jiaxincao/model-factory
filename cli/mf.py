#!/usr/bin/env python3

import click
import logging

from cli import dev_commands
from cli import job_commands
from cli import pipeline_commands
from cli import trigger_commands
from cli import model_commands


@click.group()
def main():
    pass


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    main.add_command(dev_commands.dev)
    main.add_command(job_commands.job)
    main.add_command(pipeline_commands.pipeline)
    main.add_command(trigger_commands.trigger)
    main.add_command(model_commands.model)

    main()
