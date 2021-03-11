#!/usr/bin/env python3
"""Run all tests ./tests/platform_tests/*.py and monitor results.

Example:
    tests/platform_tests/run-platform-tests.py

"""

import argparse
import importlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import flywheel
import pandas as pd
from flywheel_bids.upload_bids import upload_bids
from flywheel_gear_toolkit.utils.zip_tools import unzip_archive

# See https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
# use colors like:
# print(f"{CY}Yellow Text{C0}")
C0 = "\x1b[0m"  # Reset
CR = "\x1b[38;5;9m"  # Red
CG = "\x1b[38;5;10m"  # Green
CP = "\x1b[38;5;12m"  # purple
CB = "\x1b[38;5;27m"  # Blue
CM = "\x1b[38;5;13m"  # Magenta
CC = "\x1b[38;5;14m"  # Cyan
CY = "\x1b[38;5;11m"  # Yellow
CO = "\x1b[38;5;202m"  # Orange

CONFIG = Path("tests/platform_tests/config.tsv")

DATA_PATH = (
    Path().home()
    / "Flywheel/gitlab/flywheel-io/scientific-solutions/data-registry/data/raw/bids"
)

KEY_FILE = Path.home() / "Flywheel/bin/.keys.json"
"""KEY_FILE be like:
{
    "default": "andyworth@flywheel.io",
    "ids": {

        "andyworth@flywheel.io": {
            "ss.ce": "ss.ce.flywheel.io:abcdefgHIJKLMNOPQR",
            "ga.ce": "ga.ce.flywheel.io:abcdefgHIJKLMNOPQR",
            "rollout.ce": "rollout.ce.flywheel.io:abcdefgHIJKLMNOPQR",
        },

        "neumopho@gmail.com": {
            "ss.ce": "ss.ce.flywheel.io:abcdefgHIJKLMNOPQR"
        }
    }
}
"""


def get_flywheel_client(instance):
    """Return a Flywheel Client given the instance name.

    Get the api_key by looking it up in the KEY_FILE

    Args:
        instance (str): The the name of the Flywheel instance

    Returns:
        fw (flywheel.client.Client): Flywheel client for the named instance
    """

    with open(KEY_FILE) as json_file:
        keys = json.load(json_file)
    the_user = keys["default"]
    for key, val in keys["ids"][the_user].items():
        if instance.startswith(key):
            api_key = val
    return flywheel.Client(api_key=api_key)


def get_or_create_group(fw, group_id, group_label):
    """Create a group if it does not already exist.

    Args:
        group_id (str): An ID for a group
        group_label (str): The label for a group

    Returns:
        group (flywheel.models.group.Group): The new or existing group
    """

    groups = fw.groups.find(f"label={group_label}")
    if len(groups) > 0:
        group = groups[0]
        print(f"group.label {group.label}")
        print(f"group.id {group.id}")
    else:
        print("Group not found - Creating it.")
        group_id = fw.add_group(flywheel.Group(group_id, group_label))
    return group


def get_or_create_project(group, project_label):
    """Return a project if it exists, if not create it.

    Args:
        group (flywheel.models.group.Group): The group the project is/should be in
        project_label (str): The label of the project

    Returns:
        project (flywheel.models.project.Project): The new or existing project
    """

    print(f"Looking for prject.label {project_label}")
    projects = group.projects.find(f"label={project_label}")
    if len(projects) > 0:
        print(f"Found it.")
        project = projects[0]
        print(f"project.label {project.label}")
        print(f"project.id {project.id}")
    else:
        print("Project not found - Creating it.")
        project = group.add_project(label=f"{project_label}")
        print(f"project.label {project.label}")
        print(f"project.id {project.id}")
    return project


def import_bids_data_if_empty(fw, group_id, project, data_path):
    """Upload BIDS data and description if the project has no acquisitions.

    Data is stored in a zip archive that has a "bids" directory at
    the top level.  The zip archive is called f"{project.label}.zip".
    The description for the project (if present) is stored in a
    file called f"{project.label}_Description.md".

    Args:
        fw (flywheel.client.Client): A Flywheel client
        group_id (str): Flywheel Instance Group ID
        project (flywheel.models.project.Project): Project that was just created
        data_path (str): where to find project.label + ".zip" to upload as BIDS
    """

    acquisitions = fw.acquisitions.find(f"project={project.id}")

    if len(acquisitions) == 0:
        print(f"Project has no acquisitions, importing BIDS data for ")
        with tempfile.TemporaryDirectory() as tmpdirname:
            unzip_archive(f"{data_path}/{project.label}.zip", tmpdirname)
            upload_bids(
                fw,
                str(tmpdirname + "/bids"),
                group_id=group_id,
                project_label=project.label,
                hierarchy_type="Flywheel",
                validate=False,
            )

        description_file = Path(f"{data_path}/{project.label}_Description.md")
        if description_file.exists():
            with open(description_file, "r") as dfp:
                description = dfp.read()
            fw.modify_project(project.id, {"description": description})
        else:
            print(f"Could not find {description_file}")

    else:
        print(
            f"Project already has {len(acquisitions)} acquisitions.  Not uploading bids."
        )


def main():

    exit_code = 0

    tests = pd.read_table(CONFIG, index_col=False)

    analysis_ids = []

    for index, row in tests.iterrows():

        test = str(row["Test"])
        c_test = f"{CG}{test}{C0}"  # Green
        instance = str(row["Instance"])
        c_instance = f"{CB}{instance}{C0}"  # Blue
        group_id = str(row["Group_ID"])
        c_group_id = f"{CP}{group_id}{C0}"  # Purple
        group_label = str(row["Group_Label"])
        c_group_label = f"{CP}{group_label}{C0}"  # Purple
        project_label = str(row["Project"])
        c_project_label = f"{CM}{project_label}{C0}"  # Magenta
        if str(row["BIDS?"]).lower() == "yes":
            is_bids = True
        else:
            is_bids = False
        delay = row["Delay"]  # number of seconds
        if str(row["Run_test?"]).lower() == "yes":
            run_test = True
        else:
            run_test = False

        if test == "Exit":
            print(f"You want me to Exit, I wasn't finished!  OK Boomer.")
            os.sys.exit()

        if not run_test:
            continue

        if test == "Null":  # only create group/project and upload data, no test
            print(f"\nCreating {c_project_label} on on {c_instance}")
        else:
            print(f"\nRunning {c_test} on {c_instance}")

        # Assume the instance exists.  Someday, create one if not!
        fw = get_flywheel_client(instance)

        print(f"Setting up or using Group: {c_group_label}")
        group = get_or_create_group(fw, group_id, group_label)

        print(f"Setting up or using Project: {c_project_label}")
        project = get_or_create_project(group, project_label)

        if row["BIDS?"].lower() == "yes":
            print(f"Setting up or using BIDS Project: {row['Project']}")
            import_bids_data_if_empty(fw, group_id, project, DATA_PATH)
        else:
            print(f"Setting up or using non-BIDS Project: {row['Project']}")
            print("Wait!  I don't know how to do that!  Ahhhhhhhhhh!")

        # Import the test and launch the job
        if test != "Null":
            print(f"Launching Test: {test}")
            test_path = f"tests.{test}"[:-3]
            print(test_path)
            __import__(test_path)
            test_module = sys.modules[test_path]
            analysis_id = test_module.main(fw)
            print(f"analysis_id = {analysis_id}")
            analysis_ids.append(analysis_id)

            # TODO make this actually work:
            if row["Delay"] == float("inf"):
                # sleep for a while and check if it is done yet, repeat until done
                print(f"Waiting for job to finish...")
            elif row["Delay"] > 0:
                print(f"Sleeping for {row['Delay']} seconds")
                time.sleep(row["Delay"])

    # TODO use analysis_ids to monitor jobs or
    # launch gear to monitor tests and produce dashboard of results
    # - check result (succeed/fail) and log for specific outcomes
    # based on what is being tested, i.e. "asserts"

    return exit_code


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-s",
        "--sleep",
        type=int,
        default="10",
        help="sleep in seconds after running each test",
    )
    parser.add_argument("-v", "--verbose", action="count", default=0)

    args = parser.parse_args()

    os.sys.exit(main())
