#! /usr/bin/env python3
"""Run dcm2niix on acquisition "4 - fmap-SE-PA"

    This script was created to run Job ID 60817598fb84816baf6f3572
    In project "bids-curation-tests/Levitas_Tutorial"
    On Flywheel Instance https://rollout.ce.flywheel.io/api
"""

import argparse
import os
from datetime import datetime

import flywheel

input_files = {
    "dcm2niix_input": {
        "hierarchy_id": "60798ec6c5a368b6b66f3475",
        "location_name": "4 - fmap-SE-PA.dicom.zip",
    }
}


def main(fw):

    gear = fw.lookup("gears/dcm2niix")
    print("gear.gear.version for job was = 1.3.6_1.0.20201102-rc.1")
    print(f"gear.gear.version now = {gear.gear.version}")
    print("destination_id = 60798ec6c5a368b6b66f3475")
    print("destination type is: acquisition")
    destination = fw.lookup(
        "bids-curation-tests/Levitas_Tutorial/10462@thwjames_OpenScience/2020-01-22 14_29_46/4 - fmap-SE-PA"
    )

    inputs = dict()
    for key, val in input_files.items():
        container = fw.get(val["hierarchy_id"])
        inputs[key] = container.get_file(val["location_name"])

    config = {
        "anonymize_bids": True,
        "bids_sidecar": "n",
        "coil_combine": False,
        "comment": "",
        "compress_images": "y",
        "compression_level": 6,
        "convert_only_series": "all",
        "crop": False,
        "dcm2niix_verbose": False,
        "decompress_dicoms": False,
        "filename": "%f",
        "ignore_derived": False,
        "ignore_errors": False,
        "lossless_scaling": "n",
        "merge2d": False,
        "output_nrrd": False,
        "philips_scaling": True,
        "pydeface": False,
        "pydeface_cost": "mutualinfo",
        "pydeface_nocleanup": False,
        "pydeface_verbose": False,
        "remove_incomplete_volumes": False,
        "single_file_mode": False,
        "text_notes_private": False,
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
