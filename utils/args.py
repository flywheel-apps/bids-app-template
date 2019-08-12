#!/usr/bin/env python3
# We do not need the "Shebang" for modules without a 
# "if __name__ == '__main__':"
# Statement.
import subprocess as sp
import os, os.path as op
import re

def make_session_directory(context):
    """
    This function acquires the session.label and uses it to store the output
    of the algorithm.  This will keep the working output of the algorithm 
    separate from the bids input in work/bids.
    """
    fw = context.client
    analysis = fw.get(context.destination['id'])
    session = fw.get(analysis.parents['session'])
    session_label = re.sub('[^0-9a-zA-Z./]+', '_', session.label)
    # attach session_label to Custom_Dict
    context.Custom_Dict['session_label'] = session_label
    # Create session_label in work directory
    session_dir = op.join(context.work_dir, session_label)
    os.makedirs(session_dir,exist_ok=True)

def build(context):
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
    return params


def validate(context):
    """
    Validate settings of the Parameters constructed.
    Gives warnings for possible settings that could result in bad results.
    Gives errors (and raises exceptions) for settings that are violations 
    """
    param_list = context.Custom_Dict['param_list']
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

    command = context.Custom_Dict['command']

    param_list = context.Custom_Dict['Param_List']
    bids_path = context.Custom_Dict['bids_path']

    for key in param_list.keys():
        # Single character command-line parameters are preceded by a single '-'
        if len(key) == 1:
            command.append('-' + key)
            if len(str(param_list[key])) != 0:
                command.append(str(param_list[key]))
        # Multi-Character command-line parameters are preceded by a double '--'
        else:
            # If Param is boolean and true include, else exclude
            if type(param_list[key]) == bool:
                if param_list[key]:
                    command.append('--' + key)
            else:
                # If Param not boolean, but without value include without value
                # (e.g. '--key'), else include value (e.g. '--key=value')
                if len(str(param_list[key])) == 0:
                    command.append('--' + key)
                else:
                    command.append('--' + key + '=' + str(param_list[key]))
        if key == 'verbose':  # handle a 'count' argparse argument
            # replace "--verbose=vvv' with '-vvv'
            command[-1] = '-' + param_list[key]

    # add positional arguments
    command.append(bids_path)
    command.append(context.output_dir)
    command.append('participant')
    context.log.info(' Command:' + ' '.join(command))

    return command

def execute(context): 
    command = build_command(context)
    environ = context.Custom_Dict['environ']
    # Run the actual command this gear was created for
    result = sp.run(command, stdout=sp.PIPE, stderr=sp.PIPE,
                    universal_newlines=True, env=environ)

    context.log.info(' return code: ' + str(result.returncode))
    # f-strings (e.g. f'string {variable}') are introduced in Python3.6
    # for Python3.5 use ('string {}'.format(variable))
    context.log.info(f' Command output:\n' + result.stdout)

    if result.returncode != 0:
        context.log.error(' The command:\n ' +
                  ' '.join(command) +
                  '\nfailed. See log for debugging.')
        raise Exception(' ' + result.stderr)
    
# vi:set autoindent ts=4 sw=4 expandtab : See Vim, :help 'modeline'
