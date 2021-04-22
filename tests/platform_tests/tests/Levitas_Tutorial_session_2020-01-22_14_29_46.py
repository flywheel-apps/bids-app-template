#! /usr/bin/env python3
"""Run curate-bids on session "2020-01-22 14_29_46"

    This script was created to run Job ID 60817898f4a3a2bb836f35ca
    In project "bids-curation-tests/Levitas_Tutorial"
    On Flywheel Instance https://rollout.ce.flywheel.io/api
"""

import argparse
import os
from datetime import datetime

import flywheel

input_files = {}


def main(fw):

    gear = fw.lookup("gears/curate-bids")
    print("gear.gear.version for job was = 1.1.1_0.9.3_rc4")
    print(f"gear.gear.version now = {gear.gear.version}")
    print("destination_id = 60798ec5c5a368b6b66f3467")
    print("destination type is: session")
    destination = fw.lookup(
        "bids-curation-tests/Levitas_Tutorial/10462@thwjames_OpenScience/2020-01-22 14_29_46"
    )

    inputs = dict()
    for key, val in input_files.items():
        container = fw.get(val["hierarchy_id"])
        inputs[key] = container.get_file(val["location_name"])

    config = {
        "entire_project": True,
        "reset": True,
        "template_type": "Custom",
        "verbosity": "DEBUG",
    }

    job_id = gear.run(config=config, inputs=inputs, destination=destination)
    print(f"job_id = {job_id}")
    return job_id


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args()

    fw = flywheel.Client("")
    print(fw.get_config().site.api_url)

    analysis_id = main(fw)

    os.sys.exit(0)
