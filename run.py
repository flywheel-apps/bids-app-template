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

# editme: The following 4 constants are the main things to edit.  Run-time Parameters
# passed to the command need to be set up in manifest.json.
# The BIDS App command to run, e.g. "mriqc"
BIDS_APP = "./tests/test.sh"

# What level to run at (positional_argument #3)
ANALYSIS_LEVEL = "participant"  # "group"

# when downloading BIDS Limit download to specific folders? e.g. ['anat','func','fmap']
DOWNLOAD_MODALITIES = []  # empty list is no limit

# Whether or not to include src data (e.g. dicoms) when downloading BIDS
DOWNLOAD_SOURCE = False

# Constants that do not need to be changed
FREESURFER_LICENSE = "/opt/freesurfer/license.txt"
ENVIRONMENT_FILE = "/tmp/gear_environ.json"

# Keep a list of errors and warning to print all in one place at end of log
# Any errors will prevent the command from running and will cause exit(1)
ERRORS = []
WARNINGS = []


def set_performance_config(config, log):
    """Set run-time performance config params to pass to BIDS App.

    Set --n_cpus (number of threads) and --mem_gb (maximum memory to use).
    Use the given number unless it is too big.  Use the max available if zero.

    The user may want to set these number to less than the maximum if using a
    shared compute resource.

    Args:
        config (GearToolkitContext.config): run-time options from config.json
        log (GearToolkitContext().log): logger set up by Gear Toolkit

    Results:
        sets config["n_cpus"] which will become part of the command line command
        sets config["mem_gb"] which will become part of the command line command
    """

    os_cpu_count = os.cpu_count()
    log.info("os.cpu_count() = %d", os_cpu_count)
    n_cpus = config.get("n_cpus")
    if n_cpus:
        if n_cpus > os_cpu_count:
            log.warning("n_cpus > number available, using max %d", os_cpu_count)
            config["n_cpus"] = os_cpu_count
        else:
            log.info("n_cpus using %d from config", n_cpus)
    else:  # Default is to use all cpus available
        config["n_cpus"] = os_cpu_count  # zoom zoom
        log.info("using n_cpus = %d (maximum available)", os_cpu_count)

    psutil_mem_gb = int(psutil.virtual_memory().available / (1024 ** 3))
    log.info("psutil.virtual_memory().available= {:5.2f} GiB".format(psutil_mem_gb))
    mgm_gb = config.get("mgm_gb")
    if mgm_gb:
        if mgm_gb > psutil_mem_gb:
            log.warning("mgm_gb > number available, using max %d", psutil_mem_gb)
            config["mgm_gb"] = psutil_mem_gb
        else:
            log.info("mgm_gb using %d from config", n_cpus)
    else:  # Default is to use all cpus available
        config["mgm_gb"] = psutil_mem_gb
        log.info("using mgm_gb = %d (maximum available)", psutil_mem_gb)


def get_and_log_environment(log):
    """Grab and log environment for to use when executing command line.

    The shell environment is saved into a file at an appropriate place in the Dockerfile.

    Args:
        log (GearToolkitContext().log): logger set up by Gear Toolkit

    Returns: (nothing)
    """
    with open(ENVIRONMENT_FILE, "r") as f:
        environ = json.load(f)

        # Add environment to log if debugging
        kv = ""
        for k, v in environ.items():
            kv += k + "=" + v + " "
        log.debug("Environment: " + kv)

    return environ


def generate_command(config, work_dir, output_analysis_id_dir, log):
    """Build the main command line command to run.

    Args:
        config (GearToolkitContext.config): run-time options from config.json
        work_dir (path): scratch directory where non-saved files can be put
        output_analysis_id_dir (path): directory where output will be saved
        log (GearToolkitContext().log): logger set up by Gear Toolkit

    Returns:
        cmd (list of str): command to execute
    """

    # start with the command itself:
    cmd = [BIDS_APP]

    # 3 positional args: bids path, output dir, 'participant'
    # This should be done here in case there are nargs='*' arguments
    # These follow the BIDS Apps definition (https://github.com/BIDS-Apps)
    cmd.append(str(work_dir / "bids"))
    cmd.append(str(output_analysis_id_dir))
    cmd.append(ANALYSIS_LEVEL)
    # editme: add any positional arguments that the command needs

    # get parameters to pass to the command by skipping gear config parameters
    # (which start with "gear-").
    command_parameters = {}
    for key, val in config.items():

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
    # ERRORS.append("error message")
    # WARNINGS.append("warning message")

    cmd = build_command_list(cmd, command_parameters)

    # editme: fix --verbose argparse argument
    for ii, cc in enumerate(cmd):
        if cc.startswith("--verbose"):
            # handle a 'count' argparse argument where manifest gives
            # enumerated possibilities like v, vv, or vvv
            # e.g. replace "--verbose=vvv' with '-vvv'
            cmd[ii] = "-" + cc.split("=")[1]

    log.info("command is: %s", str(cmd))
    return cmd


def main(gtk_context):

    # run-time configuration options from the gear's context.json
    config = gtk_context.config

    # Setup basic logging and log the configuration for this job
    if config["gear-log-level"] == "INFO":
        gtk_context.init_logging("info")
    else:
        gtk_context.init_logging("debug")
    gtk_context.log_config()
    log = gtk_context.log

    # Given the destination container, figure out if running at the project,
    # subject, or session level.
    destination_id = gtk_context.destination["id"]
    hierarchy = get_run_level_and_hierarchy(gtk_context.client, destination_id)

    # This is the label of the project, subject or session and is used
    # as part of the name of the output files.
    run_label = make_file_name_safe(hierarchy["run_label"])

    # Output will be put into a directory named as the destination id.
    # This allows the raw output to be deleted so that a zipped archive
    # can be returned.
    output_analysis_id_dir = gtk_context.output_dir / destination_id

    # editme: optional feature -- set # threads and max memory to use
    set_performance_config(config, log)

    environ = get_and_log_environment(log)

    # editme: if the command needs a freesurfer license keep this
    if Path(FREESURFER_LICENSE).exists():
        log.debug("%s exists.", FREESURFER_LICENSE)
    install_freesurfer_license(gtk_context, FREESURFER_LICENSE)

    command = generate_command(
        config, gtk_context.work_dir, output_analysis_id_dir, log
    )

    # This is used as part of the name of output files
    command_name = make_file_name_safe(command[0])

    # Download BIDS Formatted data
    if len(ERRORS) == 0:

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
            dry_run=config.get("gear-dry-run"),
            do_validate_bids=config.get("gear-run-bids-validation"),
        )
        if error_code > 0 and not config.get("gear-ignore-bids-errors"):
            ERRORS.append(f"BIDS Error(s) detected.  Did not run {CONTAINER}")

    # Don't run if there were errors or if this is a dry run
    ok_to_run = True
    return_code = 0

    if len(ERRORS) > 0:
        ok_to_run = False
        return_code = 1
        log.info("Command was NOT run because of previous errors.")

    if config.get("gear-dry-run"):
        ok_to_run = False
        return_code = 0
        e = "gear-dry-run is set: Command was NOT run."
        log.warning(e)
        WARNINGS.append(e)
        pretend_it_ran(gtk_context)

    try:

        if ok_to_run:

            # Create output directory
            log.info("Creating output directory %s", output_analysis_id_dir)
            Path(output_analysis_id_dir).mkdir()

            # This is what it is all about
            exec_command(command, environ=environ)

    except RuntimeError as exc:
        return_code = 1
        ERRORS.append(exc)
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
        zip_file_name = (
            gtk_context.manifest["name"] + f"_{run_label}_{destination_id}.zip"
        )
        zip_output(
            str(gtk_context.output_dir),
            destination_id,
            zip_file_name,
            dry_run=False,
            exclude_files=None,
        )

        # editme: optional feature
        # zip any .html files in output/<analysis_id>/
        zip_htmls(gtk_context, output_analysis_id_dir)

        # editme: optional feature
        # possibly save ALL intermediate output
        if config.get("gear-save-intermediate-output"):
            zip_all_intermediate_output(gtk_context, run_label)

        # possibly save intermediate files and folders
        zip_intermediate_selected(gtk_context, run_label)

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
        with open(f"{gtk_context.output_dir}/.metadata.json", "w") as fff:
            json.dump(metadata, fff)
            log.info(f"Wrote {gtk_context.output_dir}/.metadata.json")

        # Report errors and warnings at the end of the log so they can be easily seen.
        if len(WARNINGS) > 0:
            msg = "Previous warnings:\n"
            for err in WARNINGS:
                if str(type(err)).split("'")[1] == "str":
                    # show string
                    msg += "  Warning: " + str(err) + "\n"
                else:  # show type (of warning) and warning message
                    err_type = str(type(err)).split("'")[1]
                    msg += f"  {err_type}: {str(err)}\n"
            log.info(msg)

        if len(ERRORS) > 0:
            msg = "Previous errors:\n"
            for err in ERRORS:
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

    sys.exit(main(flywheel_gear_toolkit.GearToolkitContext()))
