#!/usr/bin/env python3
"""Run the gear: set up for and call command-line command."""

import json
import os
import shutil
import sys
from pathlib import Path

import flywheel_gear_toolkit
import psutil
from flywheel_gear_toolkit.interfaces.command_line import (
    build_command_list,
    exec_command,
)
from flywheel_gear_toolkit.licenses.freesurfer import install_freesurfer_license
from flywheel_gear_toolkit.utils.zip_tools import zip_output

from utils.bids.download_run_level import download_bids_for_runlevel
from utils.bids.run_level import get_run_level_and_hierarchy
from utils.dry_run import pretend_it_ran
from utils.fly.make_file_name_safe import make_file_name_safe
from utils.results.zip_htmls import zip_htmls
from utils.results.zip_intermediate import (
    zip_all_intermediate_output,
    zip_intermediate_selected,
)

GEAR = "bids-app-template"
REPO = "flywheel-apps"
CONTAINER = f"{REPO}/{GEAR}]"

# The BIDS App command to run, e.g. "mriqc"
BIDS_APP = "./tests/test.sh"

# What level to run at (positional_argument #3)
ANALYSIS_LEVEL = "participant"  # "group"

# when downloading BIDS Limit download to specific folders? e.g. ['anat','func','fmap']
DOWNLOAD_MODALITIES = []  # empty list is no limit

# Whether or not to include src data (e.g. dicoms) when downloading BIDS
DOWNLOAD_SOURCE = False

FREESURFER_LICENSE = "/opt/freesurfer/license.txt"


def main(gtk_context):

    log = gtk_context.log

    # Keep a list of errors and warning to print all in one place at end of log
    # Any errors will prevent the command from running and will cause exit(1)
    errors = []
    warnings = []

    # Given the destination container, figure out if running at the project,
    # subject, or session level.
    hierarchy = get_run_level_and_hierarchy(
        gtk_context.client, gtk_context.destination["id"]
    )

    # This is the label of the project, subject or session and is used
    # as part of the name of the output files.
    run_label = make_file_name_safe(hierarchy["run_label"])

    # Output will be put into a directory named as the destination id.
    # This allows the raw output to be deleted so that a zipped archive
    # can be returned.
    output_analysisid_dir = gtk_context.output_dir / gtk_context.destination["id"]

    # editme: optional feature
    # get # cpu's to set -openmp
    os_cpu_count = str(os.cpu_count())
    log.info("os.cpu_count() = %s", os_cpu_count)
    n_cpus = gtk_context.config.get("n_cpus")
    if n_cpus:
        if n_cpus > os_cpu_count:
            log.warning("n_cpus > number available, using %d", os_cpu_count)
            gtk_context.config["n_cpus"] = os_cpu_count
        elif n_cpus == 0:
            log.info("n_cpus == 0, using %d (maximum available)", os_cpu_count)
            gtk_context.config["n_cpus"] = os_cpu_count
    else:  # Default is to use all cpus available
        gtk_context.config["n_cpus"] = os_cpu_count  # zoom zoom

    # editme: optional feature
    mem_gb = psutil.virtual_memory().available / (1024 ** 3)
    log.info("psutil.virtual_memory().available= {:4.1f} GiB".format(mem_gb))

    # grab environment for gear (saved in Dockerfile)
    with open("/tmp/gear_environ.json", "r") as f:
        environ = json.load(f)

        # Add environment to log if debugging
        kv = ""
        for k, v in environ.items():
            kv += k + "=" + v + " "
        log.debug("Environment: " + kv)

    # The main command line command to be run:
    # editme: Set the actual gear command:
    command = [BIDS_APP]

    # This is also used as part of the name of output files
    command_name = make_file_name_safe(command[0])

    # editme: add positional arguments that the above command needs
    # 3 positional args: bids path, output dir, 'participant'
    # This should be done here in case there are nargs='*' arguments
    # These follow the BIDS Apps definition (https://github.com/BIDS-Apps)
    command.append(str(gtk_context.work_dir / "bids"))
    command.append(str(output_analysisid_dir))
    command.append(ANALYSIS_LEVEL)

    # get config for command by skipping gear config parameters
    command_config = {}
    for key, val in gtk_context.config.items():

        if key == "bids_app_args":
            bids_app_args = val.split(" ")
            for baa in bids_app_args:
                command.append(baa)

        elif not key.startswith("gear-"):
            command_config[key] = val

    # print("command_config:", json.dumps(command_config, indent=4))

    # Validate the command parameter dictionary - make sure everything is
    # ready to run so errors will appear before launching the actual gear
    # code.  Add descriptions of problems to errors & warnings lists.
    # print("gtk_context.config:", json.dumps(gtk_context.config, indent=4))

    command = build_command_list(command, command_config)
    # print(command)

    # editme: fix --verbose argparse argument
    for ii, cmd in enumerate(command):
        if cmd.startswith("--verbose"):
            # handle a 'count' argparse argument where manifest gives
            # enumerated possibilities like v, vv, or vvv
            # e.g. replace "--verbose=vvv' with '-vvv'
            command[ii] = "-" + cmd.split("=")[1]

    log.info("command is: %s", str(command))

    # editme: if the command needs a freesurfer license keep this
    if Path(FREESURFER_LICENSE).exists():
        log.debug("%s exists.", FREESURFER_LICENSE)
    install_freesurfer_license(gtk_context, FREESURFER_LICENSE)

    if len(errors) == 0:

        # editme: optional feature
        # Create HTML file that shows BIDS "Tree" like output?
        tree = True
        tree_title = f"{command_name} BIDS Tree"

        error_code = download_bids_for_runlevel(
            gtk_context,
            hierarchy,
            tree=tree,
            tree_title=tree_title,
            src_data=DOWNLOAD_SOURCE,
            folders=DOWNLOAD_MODALITIES,
            dry_run=gtk_context.config.get("gear-dry-run"),
            do_validate_bids=gtk_context.config.get("gear-run-bids-validation"),
        )
        if error_code > 0 and not gtk_context.config.get("gear-ignore-bids-errors"):
            errors.append(f"BIDS Error(s) detected.  Did not run {CONTAINER}")

        # now that work/bids/ exists, copy in the ignore file
        bidsignore_path = gtk_context.get_input_path("bidsignore")
        if bidsignore_path:
            shutil.copy(bidsignore_path, "work/bids/.bidsignore")
            log.info("Installed .bidsignore in work/bids/")

        # see https://github.com/bids-standard/pybids/tree/master/examples
        # for any necessary work on the bids files inside the gear, perhaps
        # to query results or count stuff to estimate how long things will take.
        # Add that stuff to utils/bids.py

    # Don't run if there were errors or if this is a dry run
    ok_to_run = True

    if len(errors) > 0:
        ok_to_run = False
        returncode = 1
        log.info("Command was NOT run because of previous errors.")

    if gtk_context.config.get("gear-dry-run"):
        ok_to_run = False
        returncode = 0
        e = "gear-dry-run is set: Command was NOT run."
        log.warning(e)
        warnings.append(e)
        pretend_it_ran(gtk_context)

    try:

        if ok_to_run:

            returncode = 0

            # Create output directory
            log.info("Creating output directory %s", output_analysisid_dir)
            Path(output_analysisid_dir).mkdir()

            # This is what it is all about
            exec_command(command, environ=environ)

    except RuntimeError as exc:
        returncode = 1
        errors.append(exc)
        log.critical(exc)
        log.exception("Unable to execute command.")

    finally:

        # Cleanup, move all results to the output directory

        # TODO
        # see https://github.com/bids-standard/pybids/tree/master/examples
        # for any necessary work on the bids files inside the gear, perhaps
        # to query results or count stuff to estimate how long things will take.
        # Add that to utils/results.py

        # zip entire output/<analysis_id> folder into
        #  <gear_name>_<project|subject|session label>_<analysis.id>.zip
        zip_file_name = (
            gtk_context.manifest["name"]
            + f"_{run_label}_{gtk_context.destination['id']}.zip"
        )
        zip_output(
            str(gtk_context.output_dir),
            gtk_context.destination["id"],
            zip_file_name,
            dry_run=False,
            exclude_files=None,
        )

        # editme: optional feature
        # zip any .html files in output/<analysis_id>/
        zip_htmls(gtk_context, output_analysisid_dir)

        # editme: optional feature
        # possibly save ALL intermediate output
        if gtk_context.config.get("gear-save-intermediate-output"):
            zip_all_intermediate_output(gtk_context, run_label)

        # possibly save intermediate files and folders
        zip_intermediate_selected(gtk_context, run_label)

        # clean up: remove output that was zipped
        if Path(output_analysisid_dir).exists():
            if not gtk_context.config.get("gear-keep-output"):

                log.debug('removing output directory "%s"', str(output_analysisid_dir))
                shutil.rmtree(output_analysisid_dir)

            else:
                log.info(
                    'NOT removing output directory "%s"', str(output_analysisid_dir)
                )

        else:
            log.info("Output directory does not exist so it cannot be removed")

        # Report errors and warnings at the end of the log so they can be easily seen.
        if len(warnings) > 0:
            msg = "Previous warnings:\n"
            for err in warnings:
                if str(type(err)).split("'")[1] == "str":
                    # show string
                    msg += "  Warning: " + str(err) + "\n"
                else:  # show type (of warning) and warning message
                    err_type = str(type(err)).split("'")[1]
                    msg += f"  {err_type}: {str(err)}\n"
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
            returncode = 1

    return returncode


if __name__ == "__main__":

    gtk_context = flywheel_gear_toolkit.GearToolkitContext()

    # Setup basic logging and log the configuration for this job
    if gtk_context["gear-log-level"] == "INFO":
        gtk_context.init_logging("info")
    else:
        gtk_context.init_logging("debug")
    gtk_context.log_config()

    exit_status = main(gtk_context)

    gtk_context.log.info("%s Gear is done.  Returning %s", CONTAINER, exit_status)

    sys.exit(exit_status)
