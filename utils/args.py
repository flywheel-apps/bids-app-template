# If you edit this file, please consider updating bids-app-template

import subprocess as sp
import os, os.path as op
import logging
import re
import shutil
import json

from .fs_license import find_freesurfer_license

log = logging.getLogger(__name__)


def set_session_label(context):

    # This is used by args.make_session_directory() and 
    #                 results.zip_output()

    # TODO will this work for a non-admin user?

    try:
        fw = context.client

        dest_container = fw.get(context.destination['id'])

        session_id = dest_container.get('session')

        if session_id is None:
            session_id = dest_container.get('parents', {}).get('session')

        # Kaleb says 
        # TODO   Better to get the session information from
        #        context.get_input()['hierarchy']['id'] for a specific input.
        #        This also allows the template to accommodate inputs from different
        #        sessions.

        if session_id is None:
            log.error('Cannot get session label from destination')
            context.gear_dict['session_label'] = 'session_unknown'

        else:
            session = fw.get(session_id)
            session_label = re.sub('[^0-9a-zA-Z./]+', '_', session.label)
            # attach session_label to gear_dict
            context.gear_dict['session_label'] = session_label

        log.debug('Session label is "' + session_label + '" at debug level')
        log.info('Session label is "' + session_label + '" at info level')

    except Exception as e:
        # report error and go on in case there are more errors to report
        context.gear_dict['errors'].append(e)
        log.critical(e,)
        log.exception('Error in set_session_label()',)

def make_session_directory(context):
    """
    This function acquires the session.label and uses it to store the output
    of the algorithm.  This will keep the working output of the algorithm 
    separate from the bids input in work/bids.
    """

    try:
        # Create session_label in work directory
        session_dir = op.join(context.work_dir, 
                              context.gear_dict['session_label'])
        os.makedirs(session_dir,exist_ok=True)

    except Exception as e:
        context.gear_dict['session_label'] = 'error-unknown'
        log.error(e,)
        log.error('Unable to create session directory.')


def build(context):
    """
    Process inputs, contextual values and build a dictionary of
    key:value command-line parameter names:values These will be
    validated and assembled into a command-line below.  
    """

    # 1) Process Inputs

    # editme: optional.  Keep this if the gear runs Freesurfer
    find_freesurfer_license(context, '/opt/freesurfer/license.txt')

    # 2) Process Contextual values
    # e.g. context.matlab_license_code

    # 3) Process Configuration (config, rest of command-line parameters)
    config = context.config
    params = {}
    for key in config.keys():
        if key[:5] == 'gear-':  # Skip any gear- parameters
            continue
        # Use only those boolean values that are True
        if type(config[key]) == bool:
            if config[key]:
                params[key] = True
            # else ignore (could this cause a problem?)
        else:
            if len(key) == 1:
                params[key] = config[key]
            else:
                if config[key] != 0:  # if zero, skip and use defaults
                    params[key] = config[key]
                # else ignore (could this caus a problem?)
    
        context.gear_dict['param_list'] =  params


def validate(context):
    """
    Validate settings of the Parameters constructed.
    Gives warnings for possible settings that could result in bad results.
    Gives errors (and raises exceptions) for settings that are violations 
    """
    param_list = context.gear_dict['param_list']
    # Test for input existence
    # if not op.exists(params['i']):
    #    raise Exception('Input File Not Found')

    # Tests for specific problems/interactions that can raise exceptions or log warnings
    # if ('betfparam' in params) and ('nononlinreg' in params):
    #    if(params['betfparam']>0.0):
    #        raise Exception('For betfparam values > zero, nonlinear registration is required.')

    # if ('s' in params.keys()):
    #    if params['s']==0:
    #        log.warning(' The value of ' + str(params['s'] + \
    #                    ' for -s may cause a singular matrix'))


def build_command(context):
    """
    command is a list of prepared commands
    param_list is a dictionary of key:value pairs to be put into the command list
    as such ("-k value" or "--key=value")
    """

    param_list = context.gear_dict['param_list']

    for key in param_list.keys():
        # Single character command-line parameters are preceded by a single '-'
        if len(key) == 1:
            command.append('-' + key)
            if len(str(param_list[key])) != 0:
                # append it like '-k value'
                command.append(str(param_list[key]))
        # Multi-Character command-line parameters are preceded by a double '--'
        else:
            # If Param is boolean and true include, else exclude
            if type(param_list[key]) == bool:
                if param_list[key]:
                    command.append('--' + key)
            else:
                # If Param not boolean, but without value include without value
                if len(str(param_list[key])) == 0:
                    # append it like '--key'
                    command.append('--' + key)
                else:
                    # check for argparse nargs='*' lists of multiple values so
                    #  append it like '--key val1 val2 ...'
                    if (isinstance(param_list[key], str) and len(param_list[key].split()) > 1):
                    # then it is a list of multiple things: e.g. "--modality T1w T2w"
                        command.append('--' + key)
                        for item in param_list[key].split():
                            command.append(item)
                    else: # single value so append it like '--key=value'
                        command.append('--' + key + '=' + str(param_list[key]))
        if key == 'verbose':
            # handle a 'count' argparse argument where manifest gives
            # enumerated possibilities like v, vv, or vvv
            # e.g. replace "--verbose=vvv' with '-vvv'
            command[-1] = '-' + param_list[key]

    log.info('Command:' + ' '.join(command))

    return command


def execute(context): 

    command = build_command(context)

    environ = context.gear_dict['environ']

    # Add environment to log
    kv = ''
    for k, v in environ.items():
        kv += k + '=' + v + ' '
    log.debug(' Environment: ' + kv)

    if not context.config['gear-dry-run']:

        # Run the actual command this gear was created for
        result = sp.run(command, stdout=sp.PIPE, stderr=sp.PIPE,
                    universal_newlines=True, env=environ)

    else:
        result = sp.CompletedProcess
        result.returncode = 1
        result.stdout = ''
        result.stderr = 'gear-dry-run is set:  Did NOT run gear code.'

    return result

# vi:set autoindent ts=4 sw=4 expandtab : See Vim, :help 'modeline'
