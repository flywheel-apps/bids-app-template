#!/usr/bin/env python3

from utils.G import *


def build(config):
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


def validate(params):
    """
    Validate settings of the Parameters constructed.
    Gives warnings for possible settings that could result in bad results.
    Gives errors (and raises exceptions) for settings that are violations 
    """

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


def build_command(param_list, bids_path):
    """
    command is a list of prepared commands
    param_list is a dictionary of key:value pairs to be put into the command list
    as such ("-k value" or "--key=value")
    """

    command = [COMMAND]

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
    command.append(OUTPUT_DIR)
    command.append('participant')
    LOG.info(' Command:' + ' '.join(command))

    return command

# vi:set autoindent ts=4 sw=4 expandtab : See Vim, :help 'modeline'
