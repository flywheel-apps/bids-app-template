#! /usr/bin/env python3
"""Run bids-app-template on subject "sub-TOME3024"

    This script was created to run Job ID 6021c81f0533ee34c07166cc
    In project "BIDS_multi_session"
    On Flywheel Instance https://ss.ce.flywheel.io/api
"""

import argparse
import os
from datetime import datetime

import flywheel

input_files = {}


def main():

    fw = flywheel.Client("")
    print(fw.get_config().site.api_url)

    gear = fw.lookup("gears/bids-app-template")
    print("gear.gear.version for job was = 0.0.0_0.14.0")
    print(f"gear.gear.version now = {gear.gear.version}")
    print("destination_id = 5dc091c269d4f3002d16f334")
    print("destination type is: subject")
    destination = fw.get("5dc091c269d4f3002d16f334")

    inputs = dict()
    for key, val in input_files.items():
        container = fw.get(val["hierarchy_id"])
        inputs[key] = container.get_file(val["location_name"])

    config = {
        "bids_app_args": "",
        "bool-param": False,
        "example-bool-param": False,
        "example-empty-param": "",
        "example-threshold": 3.1415926,
        "gear-abort-on-bids-error": False,
        "gear-dry-run": False,
        "gear-ignore-bids-errors": False,
        "gear-intermediate-files": "",
        "gear-intermediate-folders": "",
        "gear-keep-output": False,
        "gear-log-level": "DEBUG",
        "gear-run-bids-validation": False,
        "gear-save-intermediate-output": False,
        "ignore": "",
        "threshold": 3.1415926,
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
    return analysis_id


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args()

    analysis_id = main()

    print(f"analysis_id = {analysis_id}")

    os.sys.exit(0)
