#!/usr/bin/env python3
"""Run the gear: set up for and call command-line command."""

import json
import logging
import shutil
import sys
from pathlib import Path

import flywheel_gear_toolkit
from flywheel_gear_toolkit.interfaces.command_line import (
    build_command_list,
    exec_command,
)
from flywheel_gear_toolkit.utils.zip_tools import zip_output

from utils.bids.download_run_level import download_bids_for_runlevel
from utils.bids.run_level import get_analysis_run_level_and_hierarchy
from utils.dry_run import pretend_it_ran
from utils.fly.environment import get_and_log_environment
from utils.fly.make_file_name_safe import make_file_name_safe
from utils.fly.set_performance_config import set_mem_gb, set_n_cpus
from utils.freesurfer import install_freesurfer_license
from utils.results.zip_htmls import zip_htmls
from utils.results.zip_intermediate import (
    zip_all_intermediate_output,
    zip_intermediate_selected,
)

log = logging.getLogger(__name__)

GEAR = "bids-app-template"
REPO = "flywheel-apps"
CONTAINER = f"{REPO}/{GEAR}]"

# editme: The following 4 constants are the main things to edit.  Run-time Parameters
# passed to the command need to be set up in manifest.json.
# The BIDS App command to run, e.g. "mriqc"
BIDS_APP = "./tests/test.sh"

# What level to run at (positional_argument #3)
ANALYSIS_LEVEL = "participant"  # "group"

# when downloading BIDS Limit download to specific folders? ['anat','func','dwt','fmap']
DOWNLOAD_MODALITIES = []  # empty list is no limit

# Whether or not to include src data (e.g. dicoms) when downloading BIDS
DOWNLOAD_SOURCE = False

# Constants that do not need to be changed
FREESURFER_LICENSE = "/opt/freesurfer/license.txt"


def generate_command(config, work_dir, output_analysis_id_dir, errors, warnings):
    """Build the main command line command to run.

    Args:
        config (GearToolkitContext.config): run-time options from config.json
        work_dir (path): scratch directory where non-saved files can be put
        output_analysis_id_dir (path): directory where output will be saved
        errors (list of str): error messages
        warnings (list of str): warning messages

    Returns:
        cmd (list of str): command to execute
    """

    # start with the command itself:
    cmd = [
        BIDS_APP,
        str(work_dir / "bids"),
        str(output_analysis_id_dir),
        ANALYSIS_LEVEL,
    ]

    # 3 positional args: bids path, output dir, 'participant'
    # This should be done here in case there are nargs='*' arguments
    # These follow the BIDS Apps definition (https://github.com/BIDS-Apps)
    # editme: add any positional arguments that the command needs

    # get parameters to pass to the command by skipping gear config parameters
    # (which start with "gear-").
    command_parameters = {}
    for key, val in config.items():

        # these arguments are passed directly to the command as is
        if key == "bids_app_args":
            bids_app_args = val.split(" ")
            for baa in bids_app_args:
                cmd.append(baa)

        elif not key.startswith("gear-"):
            command_parameters[key] = val

    # editme: Validate the command parameter dictionary - make sure everything is
    # ready to run so errors will appear before launching the actual gear
    # code.  Add descriptions of problems to errors & warnings lists.
    # print("command_parameters:", json.dumps(command_parameters, indent=4))
    if "bad_arg" in cmd:
        errors.append("A bad argument was found in the config.")
    num_things = command_parameters.get("num-things")
    print(f"num_things = {str(num_things)}")
    if num_things and num_things > 41:
        warnings.append(
            f"The num-things config value should not be > 41.  It is {command_parameters['num-things']}."
        )

    cmd = build_command_list(cmd, command_parameters)

    # editme: fix --verbose argparse argument
    for ii, cc in enumerate(cmd):
        if cc.startswith("--verbose"):
            # handle a 'count' argparse argument where manifest gives
            # enumerated possibilities like v, vv, or vvv
            # e.g. replace "--verbose=vvv' with '-vvv'
            cmd[ii] = "-" + cc.split("=")[1]
        elif " " in cc:  # then is is a space-separated list so take out "="
            # this allows argparse "nargs" to work properly
            cmd[ii] = cc.replace("=", " ")

    log.info("command is: %s", str(cmd))
    return cmd


def main(gtk_context):

    gtk_context.log_config()

    # Errors and warnings will be always logged when they are detected.
    # Keep a list of errors and warning to print all in one place at end of log
    # Any errors will prevent the BIDS App from running and will cause exit(1)
    errors = []
    warnings = []

    output_dir = gtk_context.output_dir
    work_dir = gtk_context.work_dir
    gear_name = gtk_context.manifest["name"]

    # run-time configuration options from the gear's context.json
    config = gtk_context.config

    dry_run = config.get("gear-dry-run")

    # Given the destination container, figure out if running at the project,
    # subject, or session level.
    destination_id = gtk_context.destination["id"]
    hierarchy = get_analysis_run_level_and_hierarchy(gtk_context.client, destination_id)

    # This is the label of the project, subject or session and is used
    # as part of the name of the output files.
    run_label = make_file_name_safe(hierarchy["run_label"])

    # Output will be put into a directory named as the destination id.
    # This allows the raw output to be deleted so that a zipped archive
    # can be returned.
    output_analysis_id_dir = output_dir / destination_id

    # editme: optional features -- set # threads and max memory to use
    config["n_cpus"] = set_n_cpus(config.get("n_cpus"))
    config["mem_gb"] = set_mem_gb(config.get("mem_gb"))

    environ = get_and_log_environment()

    # editme: if the command needs a Freesurfer license keep this
    install_freesurfer_license(
        gtk_context.get_input_path("freesurfer_license"),
        config.get("gear-FREESURFER_LICENSE"),
        gtk_context.client,
        destination_id,
        FREESURFER_LICENSE,
    )

    command = generate_command(
        config, work_dir, output_analysis_id_dir, errors, warnings
    )

    # This is used as part of the name of output files
    command_name = make_file_name_safe(command[0])

    # Download BIDS Formatted data
    if len(errors) == 0:

        # editme: optional feature
        # Create HTML file that shows BIDS "Tree" like output
        tree = True
        tree_title = f"{command_name} BIDS Tree"

        error_code = download_bids_for_runlevel(
            gtk_context,
            hierarchy,
            tree=tree,
            tree_title=tree_title,
            src_data=DOWNLOAD_SOURCE,
            folders=DOWNLOAD_MODALITIES,
            dry_run=dry_run,
            do_validate_bids=config.get("gear-run-bids-validation"),
        )
        if error_code > 0 and not config.get("gear-ignore-bids-errors"):
            errors.append(f"BIDS Error(s) detected.  Did not run {CONTAINER}")

    else:
        log.info("Did not download BIDS because of previous errors")
        print(errors)

    # Don't run if there were errors or if this is a dry run
    return_code = 0

    try:

        if len(errors) > 0:
            return_code = 1
            log.info("Command was NOT run because of previous errors.")

        elif dry_run:
            e = "gear-dry-run is set: Command was NOT run."
            log.warning(e)
            warnings.append(e)
            pretend_it_ran(destination_id)

        else:
            # Create output directory
            log.info("Creating output directory %s", output_analysis_id_dir)
            Path(output_analysis_id_dir).mkdir()

            # This is what it is all about
            exec_command(
                command, environ=environ, dry_run=dry_run, shell=True, cont_output=True,
            )

    except RuntimeError as exc:
        return_code = 1
        errors.append(exc)
        log.critical(exc)
        log.exception("Unable to execute command.")

    finally:

        # Cleanup, move all results to the output directory

        # TODO use pybids (or delete from requirements.txt)
        # see https://github.com/bids-standard/pybids/tree/master/examples
        # for any necessary work on the bids files inside the gear, perhaps
        # to query results or count stuff to estimate how long things will take.

        # zip entire output/<analysis_id> folder into
        #  <gear_name>_<project|subject|session label>_<analysis.id>.zip
        zip_file_name = gear_name + f"_{run_label}_{destination_id}.zip"
        zip_output(
            str(output_dir),
            destination_id,
            zip_file_name,
            dry_run=False,
            exclude_files=None,
        )

        # editme: optional feature
        # zip any .html files in output/<analysis_id>/
        zip_htmls(output_dir, destination_id, output_analysis_id_dir)

        # editme: optional feature
        # possibly save ALL intermediate output
        if config.get("gear-save-intermediate-output"):
            zip_all_intermediate_output(
                destination_id, gear_name, output_dir, work_dir, run_label
            )

        # possibly save intermediate files and folders
        zip_intermediate_selected(
            config.get("gear-intermediate-files"),
            config.get("gear-intermediate-folders"),
            destination_id,
            gear_name,
            output_dir,
            work_dir,
            run_label,
        )

        # clean up: remove output that was zipped
        if Path(output_analysis_id_dir).exists():
            if not config.get("gear-keep-output"):

                log.debug('removing output directory "%s"', str(output_analysis_id_dir))
                shutil.rmtree(output_analysis_id_dir)

            else:
                log.info(
                    'NOT removing output directory "%s"', str(output_analysis_id_dir)
                )

        else:
            log.info("Output directory does not exist so it cannot be removed")

        # editme: optional feature
        # save .metadata file
        metadata = {
            "project": {
                "info": {
                    "test": "Hello project",
                    f"{run_label} {destination_id}": "put this here",
                },
                "tags": [run_label, destination_id],
            },
            "subject": {
                "info": {
                    "test": "Hello subject",
                    f"{run_label} {destination_id}": "put this here",
                },
                "tags": [run_label, destination_id],
            },
            "session": {
                "info": {
                    "test": "Hello session",
                    f"{run_label} {destination_id}": "put this here",
                },
                "tags": [run_label, destination_id],
            },
            "analysis": {
                "info": {
                    "test": "Hello analysis",
                    f"{run_label} {destination_id}": "put this here",
                },
                "files": [
                    {
                        "name": "bids_tree.html",
                        "info": {
                            "value1": "foo",
                            "value2": "bar",
                            f"{run_label} {destination_id}": "put this here",
                        },
                        "tags": ["ein", "zwei"],
                    }
                ],
                "tags": [run_label, destination_id],
            },
        }
        with open(f"{output_dir}/.metadata.json", "w") as fff:
            json.dump(metadata, fff)
            log.info(f"Wrote {output_dir}/.metadata.json")

        # Report errors and warnings at the end of the log so they can be easily seen.
        if len(warnings) > 0:
            msg = "Previous warnings:\n"
            for warn in warnings:
                msg += "  Warning: " + str(warn) + "\n"
            log.info(msg)

        if len(errors) > 0:
            msg = "Previous errors:\n"
            for err in errors:
                if str(type(err)).split("'")[1] == "str":
                    # show string
                    msg += "  Error msg: " + str(err) + "\n"
                else:  # show type (of error) and error message
                    err_type = str(type(err)).split("'")[1]
                    msg += f"  {err_type}: {str(err)}\n"
            log.info(msg)
            return_code = 1

    log.info("%s Gear is done.  Returning %s", CONTAINER, return_code)

    return return_code


if __name__ == "__main__":

    gtk_context = flywheel_gear_toolkit.GearToolkitContext()

    # Setup basic logging and log the configuration for this job
    if gtk_context.config["gear-log-level"] == "INFO":
        gtk_context.init_logging("info")
    else:
        gtk_context.init_logging("debug")

    sys.exit(main(gtk_context))
