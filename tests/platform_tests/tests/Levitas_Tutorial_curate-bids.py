#! /usr/bin/env python3
"""Run curate-bids on session "2020-01-22 14_29_46"

    This script was created to run Job ID 609c558e510043ddf4bb5a1a
    In project "bids-curation-test/Levitas_Tutorial"
    On Flywheel Instance https://ga.ce.flywheel.io/api

    This script was modified to run save_bids_curation.py after the gear
    finishes.  No it wasn't.  Instead, that gets run next by platform_tests/confit.tsv
"""

import argparse
import os
from datetime import datetime

import flywheel

input_files = {}


def main(fw):

    gear = fw.lookup("gears/curate-bids")
    print("gear.gear.version for job was = 1.1.1_0.9.3_rc5")
    print(f"gear.gear.version now = {gear.gear.version}")
    print("destination_id = 609af24b217fd6533bbb5d31")
    print("destination type is: session")
    destination = fw.lookup(
        "bids-curation-test/Levitas_Tutorial/10462@thwjames_OpenScience/2020-01-22 14_29_46"
    )

    inputs = dict()
    for key, val in input_files.items():
        container = fw.get(val["hierarchy_id"])
        inputs[key] = container.get_file(val["location_name"])

    config = {
        "entire_project": True,
        "reset": True,
        "template_type": "Default",
        "verbosity": "INFO",
    }

    job_id = gear.run(config=config, inputs=inputs, destination=destination)
    print(f"job_id = {job_id}")

    # TODO wait for job to finish, then run save_bids_curation.py on the project
    # and finally compare the results with expected results.
    return job_id


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args()

    fw = flywheel.Client("")
    print(fw.get_config().site.api_url)

    analysis_id = main(fw)

    os.sys.exit(0)
