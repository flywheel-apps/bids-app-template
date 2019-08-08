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
    # if not op.exists(Params['i']):
    #    raise Exception('Input File Not Found')

    # Tests for specific problems/interactions that can raise expections or log warnings
    # if ('betfparam' in Params) and ('nononlinreg' in Params):
    #    if(Params['betfparam']>0.0):
    #        raise Exception('For betfparam values > zero, nonlinear registration is required.')

    # if ('s' in Params.keys()):
    #    if Params['s']==0:
    #        log.warning(' The value of ' + str(Params['s'] + \
    #                    ' for -s may cause a singular matrix'))


def build_command(ParamList, bids_path):
    """
    command is a list of prepared commands
    ParamList is a dictionary of key:value pairs to be put into the command list 
    as such ("-k value" or "--key=value")
    """

    command = [COMMAND]

    for key in ParamList.keys():
        # Single character command-line parameters are preceded by a single '-'
        if len(key) == 1:
            command.append('-' + key)
            if len(str(ParamList[key])) != 0:
                command.append(str(ParamList[key]))
        # Multi-Character command-line parameters are preceded by a double '--'
        else:
            # If Param is boolean and true include, else exclude
            if type(ParamList[key]) == bool:
                if ParamList[key]:
                    command.append('--' + key)
            else:
                # If Param not boolean, but without value include without value
                # (e.g. '--key'), else include value (e.g. '--key=value')
                if len(str(ParamList[key])) == 0:
                    command.append('--' + key)
                else:
                    command.append('--' + key + '=' + str(ParamList[key]))
        if key == 'verbose':  # handle a 'count' argparse argument
            # replace "--verbose=vvv' with '-vvv'
            command[-1] = '-' + ParamList[key]

    # add positional arguments
    command.append(bids_path)
    command.append(OUTPUT_DIR)
    command.append('participant')
    LOG.info(' Command:' + ' '.join(command))

    return command

# vi:set autoindent ts=2 sw=2 expandtab : See Vim, :help 'modeline'
