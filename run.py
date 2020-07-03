#!/usr/bin/env python3
""" Run the gear: set up for and call command-line code """

import os
import subprocess as sp
import sys
import logging
import shutil
import psutil

import flywheel_gear_toolkit
from flywheel_gear_toolkit.licenses.freesurfer import install_freesurfer_license
from flywheel_gear_toolkit.interfaces.command_line import build_command_list 

from utils.bids.run_level import get_run_level_and_hierarchy
from utils.fly.make_file_name_safe import make_file_name_safe


from utils import args

from utils.dicom.import_dicom_header_as_dict import *

from utils.fly.custom_log import *
from utils.fly.get_root_client import *
from utils.fly.get_session_from_analysis_id import *
from utils.fly.get_session_uids import *
from utils.fly.load_manifest_json import *
from utils.fly.make_session_directory import *

from utils.helpers.exists import *
from utils.helpers.extract_return_paths import *
from utils.helpers.set_environment import *

from utils.results.zip_htmls import zip_htmls
from utils.results.zip_output import zip_output
from utils.results.zip_intermediate import zip_all_intermediate_output
from utils.results.zip_intermediate import zip_intermediate_selected

import utils.dry_run


def main(gtk_context):

    log = gtk_context.log

    # Keep a list of errors and warning to print all in one place at end of log
    # Any errors will prevent the command from running and will cause exit(1)
    errors = []  
    warnings = []

    hierarchy = get_run_level_and_hierarchy(
        gtk_context.client,
        gtk_context.destination['id'])

    run_label = make_file_name_safe(hierarchy["run_label"])

    output_analysisid_dir = gtk_context.output_dir / gtk_context.destination['id']

    # editme: optional feature
    # get # cpu's to set -openmp
    cpu_count = str(os.cpu_count())
    log.info('os.cpu_count() = ' + cpu_count)

    # editme: optional feature
    mem_gb = psutil.virtual_memory().available / (1024 ** 3)
    log.info('psutil.virtual_memory().available= {:4.1f} GiB'.format(mem_gb))

    # grab environment for gear (saved in Dockerfile)
    with open('/tmp/gear_environ.json', 'r') as f:
        environ = json.load(f)

        # Add environment to log if debugging
        kv = ''
        for k, v in environ.items():
            kv += k + '=' + v + ' '
        log.debug('Environment: ' + kv)

    gear_config = {}
    for key, val in gtk_context.config.items():
        if key.startswith('gear-'):
            gear_config[key] = val
            del gtk_context.config[key]
    json.dumps(gtk_context, indent=4)

    # The main command line command to be run:
    # editme: Set the actual gear command:
    command = ['./tests/test.sh']

    command_name = make_file_name_safe(command[0])

    # editme: add positional arguments that the above command needs
    # 3 positional args: bids path, output dir, 'participant'
    # This should be done here in case there are nargs='*' arguments
    # These follow the BIDS Apps definition (https://github.com/BIDS-Apps)
    command.append(gtk_context.work_dir / 'bids')
    command.append(output_analysisid_dir)
    command.append('participant')

    command = build_command_list(command, gtk_context.config)

    # Set first part of result zip file names based on the above file safe names
    zip_head = f"{command_name}_{run_label}_{gtk_context.destination['id']}"

    install_freesurfer_license(gtk_context, '/opt/freesurfer/license.txt')

    print(command)
    print('Stopping early')
    sys.exit(1)

"""
        # Process inputs, contextual values and build a dictionary of
        # key-value arguments specific for COMMAND
        args.get_inputs_and_args(context)

        # Validate the command parameter dictionary - make sure everything is 
        # ready to run so errors will appear before launching the actual gear 
        # code.  Raises Exception on fail
        args.validate(context)

        # Build final command-line (a list of strings)
        # result is put into context.gear_dict['command_line'] 
        args.build_command(context)

    except Exception as e:
        context.gear_dict['errors'].append(e)
        log.critical(e)
        log.exception('Error in creating and validating command.')


    if len(context.gear_dict['errors']) == 0:

def set_up_data(gtk_context):
    # Set up and validate data to be used by command
    try:

        # editme: optional feature
        # Create working output directory with session label as name
        make_session_directory(context)

        # Download bids for the current session 
        # editme: add kwargs to limit what is downloaded
        # bool src_data: Whether or not to include src data (e.g. dicoms) default: False
        # list subjects: The list of subjects to include (via subject code) otherwise all subjects
        # list sessions: The list of sessions to include (via session label) otherwise all sessions
        # list folders: The list of folders to include (otherwise all folders) e.g. ['anat', 'func']
        # **kwargs: Additional arguments to pass to download_bids_dir

        #folders_to_load = ['anat', 'func', 'fmap']
        folders_to_load = []  # leave empty to download all folders

        if context.gear_dict['run_level'] == 'project':

            log.info('Downloading BIDS for project "' + 
                     context.gear_dict['project_label'] + '"')

            # don't filter by subject or session, grab all
            download_bids(context, folders=folders_to_load)

        elif context.gear_dict['run_level'] == 'subject':

            log.info('Downloading BIDS for subject "' + 
                     context.gear_dict['subject_code'] + '"')

            # only download this subject
            download_bids(context, 
                      subjects = [context.gear_dict['subject_code']],
                      folders=folders_to_load)

        elif context.gear_dict['run_level'] == 'session':

            log.info('Downloading BIDS for session "' + 
                     context.gear_dict['session_label'] + '"')

            # only download data for this session AND this subject
            download_bids(context, 
                      subjects = [context.gear_dict['subject_code']],
                      sessions = [context.gear_dict['session_label']],
                      folders=folders_to_load)

        else:
            msg = 'This job is not being run at the project subject or ' +\
                  'session level'
            raise TypeError(msg)

        # editme: optional feature
        # Save bids file hierarchy `tree` output in .html file
        html_file = 'output/bids_tree'
        bids_path = context.gear_dict['bids_path']
        tree_bids(bids_path, html_file)
        log.info('Wrote tree("' + bids_path + '") output into html file "' +
                         html_file + '.html')

        # editme: optional feature, but recommended!
        # Validate Bids file heirarchy
        # Bids validation on a phantom tree may be occuring soon
        validate_bids(context)

        # TODO
        # see https://github.com/bids-standard/pybids/tree/master/examples
        # for any necessary work on the bids files inside the gear, perhaps
        # to query results or count stuff to estimate how long things will take.
        # Add that stuff to utils/bids.py

    except Exception as e:
        context.gear_dict['errors'].append(e)
        log.critical(e)
        log.exception('Error in BIDS download and validation.')
"""

def execute(gtk_context):
    try:

        log.info('Command: ' + 
        ' '.join(str(w) for w in context.gear_dict['command_line']))

        # Don't run if there were errors or if this is a dry run
        ok_to_run = True

        if len(context.gear_dict['errors']) > 0:
            ok_to_run = False
            result = sp.CompletedProcess
            result.returncode = 1
            log.info('Command was NOT run because of previous errors.')

        elif context.config['gear-dry-run']:
            ok_to_run = False
            result = sp.CompletedProcess
            result.returncode = 0
            e = 'gear-dry-run is set: Command was NOT run.'
            log.warning(e)
            context.gear_dict['warnings'].append(e)
            utils.dry_run.pretend_it_ran(context)

        if ok_to_run:

            # Create output directory
            log.info('Creating ' + context.gear_dict['output_analysisid_dir'])
            os.mkdir(context.gear_dict['output_analysisid_dir'])

            # Run the actual command this gear was created for
            result = sp.run(context.gear_dict['command_line'], 
                        env = context.gear_dict['environ'])
            log.debug(repr(result))

        log.info('Return code: ' + str(result.returncode))

        if result.returncode == 0:
            log.info('Command successfully executed!')

        else:
            log.info('Command failed.')

    except Exception as e:
        context.gear_dict['errors'].append(e)
        log.critical(e)
        log.exception('Unable to execute command.')

    finally:

        # TODO
        # see https://github.com/bids-standard/pybids/tree/master/examples
        # for any necessary work on the bids files inside the gear, perhaps
        # to query results or count stuff to estimate how long things will take.
        # Add that stuff to utils/results.py

        # editme: optional feature
        # Cleanup, move all results to the output directory
        zip_htmls(context, context.output_dir)  # zip any .html files in output/
        path = context.gear_dict['output_analysisid_dir']
        zip_htmls(context, path)  # zip any .html files in output/<analysis_id>/

        # zip entire output/<analysis_id> folder
        zip_output(context)

        # editme: optional feature
        # possibly save ALL intermediate output
        if context.config['gear-save-intermediate-output']:
            zip_all_intermediate_output(context)

        # possibly save intermediate files and folders
        zip_intermediate_selected(context)

        # clean up: remove output that was zipped
        if os.path.exists(context.gear_dict['output_analysisid_dir']):
            if not context.config['gear-keep-output']:

                shutil.rmtree(context.gear_dict['output_analysisid_dir'])
                log.debug('removing output directory "' + 
                          str(context.gear_dict['output_analysisid_dir']) + '"')

            else:
                log.info('NOT removing output directory "' + 
                          context.gear_dict['output_analysisid_dir'] + '"')

        else:
            log.info('Output directory does not exist so it cannot be removed')

        ret = result.returncode

        if len(context.gear_dict['warnings']) > 0 :
            msg = 'Previous warnings:\n'
            for err in context.gear_dict['warnings']:
                if str(type(err)).split("'")[1] == 'str':
                    # show string
                    msg += '  Warning: ' + str(err) + '\n'
                else:  # show type (of warning) and warning message
                    msg += '  ' + str(type(err)).split("'")[1] + ': ' + str(err) + '\n'
            log.info(msg)

        if len(context.gear_dict['errors']) > 0 :
            msg = 'Previous errors:\n'
            for err in context.gear_dict['errors']:
                if str(type(err)).split("'")[1] == 'str':
                    # show string
                    msg += '  Error msg: ' + str(err) + '\n'
                else:  # show type (of error) and error message
                    msg += '  ' + str(type(err)).split("'")[1] + ': ' + str(err) + '\n'
            log.info(msg)
            ret = 1

        return ret




    return exit_status


if __name__ == '__main__':

    gtk_context = flywheel_gear_toolkit.GearToolkitContext()

    # Setup basic logging and log the configuration for this job
    gtk_context.init_logging('debug')
    gtk_context.log_config()

    exit_status = main(context)

    gtk_context.log.info('BIDS App Gear is done.  Returning %s', exit_status)

    sys.exit(exit_status)
