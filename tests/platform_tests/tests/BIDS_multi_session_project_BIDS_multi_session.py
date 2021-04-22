#! /usr/bin/env python3
"""Run bids-app-template on project "BIDS_multi_session"

    This script was created to run Job ID 603fb4ab146a36499c6e8aca
    In project "scien/BIDS_multi_session"
    On Flywheel Instance https://rollout.ce.flywheel.io/api
"""

import argparse
import os
from datetime import datetime

import flywheel

input_files = {}


def main(fw):

    gear = fw.lookup("gears/bids-app-template")
    print("gear.gear.version for job was = 0.0.0_0.15.0")
    print(f"gear.gear.version now = {gear.gear.version}")
    print("destination_id = 602ed7b21c5936816883e901")
    print("destination type is: project")
    destination = fw.lookup("scien/BIDS_multi_session")

    inputs = dict()
    for key, val in input_files.items():
        container = fw.get(val["hierarchy_id"])
        inputs[key] = container.get_file(val["location_name"])

    config = {
        "bids_app_args": "",
        "example-bool-param": False,
        "example-empty-param": "",
        "example-threshold": 3.1415926,
        "gear-dry-run": True,
        "gear-ignore-bids-errors": False,
        "gear-intermediate-files": "",
        "gear-intermediate-folders": "",
        "gear-keep-output": False,
        "gear-log-level": "DEBUG",
        "gear-run-bids-validation": False,
        "gear-save-intermediate-output": False,
        "ignore": "",
        "verbose": "v",
        "write-graph": False,
    }

    now = datetime.now()
    analysis_label = (
        f'{gear.gear.name} {now.strftime("%m-%d-%Y %H:%M:%S")} SDK launched'
    )
    print(f"analysis_label = {analysis_label}")

    analysis_id = gear.run(
        analysis_label=analysis_label,
        config=config,
        inputs=inputs,
        destination=destination,
    )
    print(f"analysis_id = {analysis_id}")
    return analysis_id


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args()

    fw = flywheel.Client("")
    print(fw.get_config().site.api_url)

    analysis_id = main(fw)

    os.sys.exit(0)
