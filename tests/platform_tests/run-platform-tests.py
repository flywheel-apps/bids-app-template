#!/usr/bin/env python3
"""Run tests in ./tests/platform_tests/tests/*.py and monitor results.

This uses the configuration file "tests/platform_tests/config.tsv".

Example:
    tests/platform_tests/run-platform-tests.py

"""

import argparse
import importlib
import json
import os
import subprocess as sp
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

DATA_PATH = Path().home() / "Flywheel/gitlab/flywheel-io/qa/data-registry"

ORIG_LOGIN = ""
USER_JSON = Path(Path.home() / ".config/flywheel/user.json")
if USER_JSON.exists():
    with open(USER_JSON) as json_file:
        contents = json.load(json_file)
        if "key" in contents:
            ORIG_LOGIN = contents["key"]

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

if not DATA_PATH.exists():
    print()
    print(f"{CR}Ahhhhhhhh!{C0} I can't go on like this.")
    print(f"{DATA_PATH} does not exist.")
    print()
    exit(1)


def get_api_key(instance):
    """Return a Flywheel Client given the instance name.

    Get the api_key by looking it up in the KEY_FILE

    Args:
        instance (str): The the name of the Flywheel instance

    Returns:
        fw (flywheel.client.Client): Flywheel client for the named instance
    """

    # TODO make this work with environment variables or else
    # by getting the api-key from ~/.config/flywheel/user.json
    # if the KEY_FILE is not present but that doesn't honor the
    # "instance" argument to this method

    with open(KEY_FILE) as json_file:
        keys = json.load(json_file)
    the_user = keys["default"]
    for key, val in keys["ids"][the_user].items():
        if instance.startswith(key):
            api_key = val
    if not api_key:
        print(f"{CR}Could not find instance '{instance}'{C0}")
    return api_key


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
        print(f"Found group.")
        group = groups[0]
        print(f"group.label {group.label}")
        print(f"group.id {group.id}")
    else:
        print("Group not found - Creating it.")
        group_id = fw.add_group(flywheel.Group(group_id, group_label))
        group = fw.get_group(group_id)
        print(f"group.label {group.label}")
        print(f"group.id {group.id}")
    return group


def get_data_from_storage(data_file):
    """Pull data from wherever it is stored.

    Args:
        data_file (Path): complete path to the large zip data file
    """
    print(f"{CR}Yipes, I don't know how to pull data from dvc yet{C0}")


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


def upload_data_if_empty(fw, group_id, project, data_path, upload_as):
    """Upload data and description if the project has no acquisitions.

    For BIDS:
        Data is stored in a zip archive that has a "bids" directory at
        the top level.

    For DICOM:
        Data is stored in a zip archive that has a directories with ".dcm"
        files in them.

    The zip archive is called f"{project.label}.zip".

    The description for the project (if present) is stored in a
    file called f"{project.label}_Description.md".

    Args:
        fw (flywheel.client.Client): A Flywheel client
        group_id (str): Flywheel Instance Group ID
        project (flywheel.models.project.Project): Project that was just created
        data_path (str): where to find project.label + ".zip" to upload as BIDS
        upload_as (str): "bids" or "dicom"
    """

    global api_key, current_login, log_back_in_to_orig

    acquisitions = fw.acquisitions.find(f"project={project.id}")

    if len(acquisitions) == 0:
        print(f"Project has no acquisitions, Setting up...")

        print("Importing data...")
        data_file = data_path / (project.label + ".zip")
        print(f"Looking for {str(data_file)}")
        if not data_file.exists():
            get_data_from_storage(data_file)

        with tempfile.TemporaryDirectory() as tmpdirname:
            unzip_archive(f"{data_path}/{project.label}.zip", tmpdirname)

            if upload_as == "bids":
                print("Setting up or using BIDS data")
                upload_bids(
                    fw,
                    str(tmpdirname + "/bids"),
                    group_id=group_id,
                    project_label=project.label,
                    hierarchy_type="Flywheel",
                    validate=False,
                )

            elif upload_as == "dicom":
                print("Setting up or using DICOM data")
                if args.verbose:
                    cmd = f"tree {tmpdirname}"
                    result = sp.run([w for w in cmd.split()])

                for item in Path(tmpdirname).glob("*"):
                    if item.is_dir():
                        dcm_dir = Path(tmpdirname) / item
                        if len(list(dcm_dir.glob("*.dcm"))) > 0:

                            if api_key != current_login:
                                log_back_in_to_orig = True
                                cmd = f"fw login {api_key}"
                                print(f"{CO}fw login {api_key.split(':')[0]}{C0}")
                                command = [w for w in cmd.split()]
                                result = sp.run(command)
                                current_login = api_key

                            cmd = f"fw ingest dicom {dcm_dir} {group_id} {project.label} -v -y"
                            print(f"{CO}{cmd}{C0}")
                            command = [w for w in cmd.split()]
                            result = sp.run(command)

            else:
                print(
                    f"{CR}Wait!  I don't know how to do {upload_as}!  Ahhhhhhhhhh!{C0}"
                )

        description_file = Path(f"{data_path}/{project.label}_Description.md")
        if description_file.exists():
            with open(description_file, "r") as dfp:
                description = dfp.read()
            fw.modify_project(project.id, {"description": description})
            print(f"Added {description_file} to project.")
        else:
            print(f"Could not find {description_file}")

    else:
        print(
            f"Project already has {len(acquisitions)} acquisitions.  Not uploading data."
        )


def install_project_files(fw, project, data_path):
    """Install files found in {project.label}_project_files.zip.

    Args:
        fw (flywheel.client.Client): A Flywheel client
    """
    project_zip_name = f"{project.label}_project_files.zip"
    project_zip_file = Path(f"{data_path}/{project_zip_name}")
    if project_zip_file.exists():
        print(f"Found '{project_zip_name}'")
        with tempfile.TemporaryDirectory() as tmpdirname:
            unzip_archive(project_zip_file, tmpdirname)
            if args.verbose:
                cmd = f"tree {tmpdirname}"
                result = sp.run([w for w in cmd.split()])
            project_files_dir = Path(tmpdirname) / f"{project.label}_project_files"
            for afile in project_files_dir.glob("*"):
                found_file = False
                for project_file in project.files:
                    if project_file.name == afile.name:
                        print(f"{afile.name} alredy exists on project")
                        found_file = True
                        break
                if not found_file:
                    project.upload_file(afile)
                    print(f"Uploaded {afile.name} to project")
    else:
        print(f"No '{project_zip_name}' found (no files to upload)")


def install_gear(fw, gear_name, gear_version):

    gears = {gear.gear.name: gear.gear.version for gear in fw.gears()}
    if gear_name in gears:
        print(f"Gear {gear_name} is already installed")
        if gears[gear_name] == gear_version:
            print(f"Gear version is the desired version {gear_version}")
        else:
            print(
                f"Gear version is {gears[gear_name]} but it is not "
                f"the desired version {gear_version}"
            )
            print(f"{CR}Yipes, I don't know how to fix this yet{C0}")
    else:
        print(f"Installing gear {gear_name}")
        print(f"{CR}Yipes, I don't know how to do that yet{C0}")


def add_classifier_rule(fw, project):

    name = "1. dicom classifier (all dicoms)"
    project_rules = [rule.name for rule in fw.get_project_rules(project.id)]
    if name not in project_rules:

        print("Installing classifier gear rule")
        gear = fw.lookup(f"gears/dicom-mr-classifier")
        new_rule = flywheel.models.rule.Rule(
            project_id=project.id,
            **{
                "all": [{"regex": False, "type": "file.type", "value": "dicom"}],
                "_not": [],
                "any": [],
            },
            auto_update=True,
            disabled=False,
            gear_id=gear.id,
            name=name,
        )
        fw.add_project_rule(project.id, new_rule)

    else:
        print(f"'{name}' gear rule already installed")


def add_dcm2niix_rule(fw, project):

    name = "2. DICOM Conversion"
    project_rules = [rule.name for rule in fw.get_project_rules(project.id)]
    if name not in project_rules:

        print("Installing dcm2niix gear rule")
        gear = fw.lookup(f"gears/dcm2niix")
        new_rule = flywheel.models.rule.Rule(
            project_id=project.id,
            **{
                "_not": [],
                "all": [
                    {"regex": False, "type": "file.modality", "value": "MR"},
                    {"regex": False, "type": "file.type", "value": "dicom"},
                ],
                "any": [],
            },
            auto_update=True,
            disabled=False,
            gear_id=gear.id,
            name=name,
        )
        fw.add_project_rule(project.id, new_rule)

    else:
        print(f"'{name}' gear rule already installed")


def install_gear_rules(fw, project, gear_rules):
    """Install gear rules if listed.
    Args:
        fw (flywheel.client.Client): A Flywheel client
        gear_rules (str): space separated list of gear rules, one of:
            [classifier, dcm2niix]
    """

    for gr in gear_rules.split(" "):
        if gr.lower() == "none":
            pass
        if gr == "classifier":
            add_classifier_rule(fw, project)
        elif gr == "dcm2niix":
            add_dcm2niix_rule(fw, project)
        else:
            print(f"{CR}Wait!  I don't know what {gr} is!  Ahhhhhhhhhh!{C0}")


def run_test(test, fw):
    """Import the test and launch the job

    Args:
        tests (str): name of python test script

    Returns:
        analysis_id (str): ID that can be tracked
    """

    test_path = f"tests.{test}"[:-3]
    print(test_path)
    __import__(test_path)
    test_module = sys.modules[test_path]
    analysis_id = test_module.main(fw)
    print(f"analysis_id = {analysis_id}")
    return analysis_id


def main():

    global api_key

    tests = pd.read_table(CONFIG, index_col=False)

    analysis_ids = []
    line_num = 1  # skip header line

    for index, row in tests.iterrows():
        line_num += 1

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
        upload_as = str(row["Upload_As"]).lower()
        registry_path = row["Registry_Path"]
        gear_rules = str(row["Gear_Rules"])
        gear_name = str(row["Gear_Name"])
        gear_version = str(row["Gear_Version"])
        delay = row["Delay"]  # number of seconds
        if str(row["Skip?"]).lower() in ["yes", "skip"]:
            continue

        # Say what is about to happen.  The main pupose is to run tests, but
        # if no tests are going to be run, still set up everything else unless
        # already set up.
        print()
        print(f"Running config.tsv line {line_num}")
        if test == "Null":  # only create group/project and upload data, no test
            print(f"Setting up {c_project_label} on {c_instance}")
        else:  # run test and do other set-up if necessary
            print(f"Running {c_test} on {c_instance}")

        if test == "Exit":
            print(f"You want me to Exit, I wasn't finished!  OK Boomer.")
            os.sys.exit()

        # Assume the instance exists.  Someday, create one if not!
        api_key = get_api_key(instance)

        fw = flywheel.Client(api_key=api_key)

        print(f"Setting up or using Group: {c_group_id} a.k.a. {c_group_label}")
        group = get_or_create_group(fw, group_id, group_label)

        print(f"Setting up or using Project: {c_project_label}")
        project = get_or_create_project(group, project_label)

        if gear_rules and gear_rules != "nan":
            print("Installing gear rules:")
            install_gear_rules(fw, project, gear_rules)

        print("Installing project files")
        install_project_files(fw, project, DATA_PATH / registry_path)

        print(f"Setting up or using '{upload_as}' Project: {row['Project']}")
        upload_data_if_empty(
            fw, group_id, project, DATA_PATH / registry_path, upload_as
        )

        if gear_name and gear_name != "nan":
            print("Installing gear")
            install_gear(fw, gear_name, gear_version)

        if test != "Null":
            print(f"Launching test")
            analysis_ids.append(run_test(test, fw))

        # TODO make this actually work:
        if delay == float("inf"):
            # sleep for a while and check if it is done yet, repeat until done
            print(f"Waiting for job to finish...")
            print(f"{CR}Yipes, this isn't written yet!{C0}")
        elif delay == "all-jobs-finished":
            print(f"Waiting for all job to finish...")
            print(f"{CR}Yipes, this isn't written yet!{C0}")
        elif float(delay) > 0.0:
            print(f"Sleeping for {delay} seconds")
            time.sleep(delay)
        else:
            print(f"{CR}Unknown Delay value: {delay}{C0}")

    # TODO use analysis_ids to monitor jobs or
    # launch gear to monitor tests and produce dashboard of results
    # - check result (succeed/fail) and log for specific outcomes
    # based on what is being tested, i.e. "asserts"

    return 0


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

    api_key = ""
    current_login = ORIG_LOGIN
    log_back_in_to_orig = False

    ret_val = main()

    if log_back_in_to_orig:
        if ORIG_LOGIN:
            cmd = f"fw login {ORIG_LOGIN}"
            print(f"{CO}fw login {ORIG_LOGIN.split(':')[0]}{C0}")
        else:
            cmd = f"fw logout"
            print(f"{CO}fw loout{C0}")
        command = [w for w in cmd.split()]
        result = sp.run(command)

    os.sys.exit(ret_val)
