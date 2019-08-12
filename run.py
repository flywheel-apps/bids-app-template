#!/usr/bin/env python3

import json
import os
import subprocess as sp
import logging
import psutil

import flywheel

# GearContext takes care of most of these variables
# from utils.G import *
from utils import args, bids, results
from utils.Custom_Logger import get_Custom_Logger

if __name__ == '__main__':
    # Instantiate the Gear Context
    context = flywheel.GearContext()
    # Get Custom Logger and set attributes
    context.log = get_Custom_Logger('[flywheel/bids-app-template]')
    context.log.setLevel(getattr(logging, context.config['gear-log-level']))

    # Instantiate Custom Dictionary in gear context
    context.Custom_Dict = {}

    # f-strings (e.g. f'string {variable}') are introduced in Python3.6
    # for Python3.5 use ('string {}'.format(variable))
    context.log.debug(f'psutil.cpu_count()= {psutil.cpu_count()}')
    context.log.debug(f'psutil.virtual_memory().total= ' +
                      '{psutil.virtual_memory().total / (1024 ** 3):4.1f} GiB')
    context.log.debug(f'psutil.virtual_memory().available= ' + \
                      '{psutil.virtual_memory().available / (1024 ** 3):4.1f} GiB')

    # grab environment for gear
    with open('/tmp/gear_environ.json', 'r') as f:
        environ = json.load(f)
        context.Custom_Dict['environ'] = environ

    try:
        # Download bids for the current session
        bids.download(context)

        # Display bids file hierarchy
        bids.tree(context)

        # Validate Bids file heirarchy
        # Bids validation on a phantom tree may be occuring soon
        bids.run_validation(context)
    except Exception as e:
        context.log.critical(e,)
        context.log.exception('Error in BIDS download and validation.',)
        os.sys.exit(1)

    try:
        # Create working output directory with session label as name
        args.make_session_directory(context)

        # Build a parameter dictionary specific for COMMAND
        args.build(context)

        # Validate the command parameter dictionary
        # Raises Exception on fail
        args.validate(context)

        # Build command-line string for subprocess and execute
        args.execute(context)
        
        context.log.info(f' Command successfully executed!')
        os.sys.exit(0)

    except Exception as e:
        context.log.critical(e,)
        context.log.exception('Unable to execute command.')
        os.sys.exit(1)

    finally:
        # Cleanup, move all results to the output directory
        results.zip_htmls(context)

        # possibly save ALL intermediate output
        if context.config['gear-save-all-output']:
            results.zip_output(context)


# vi:set autoindent ts=4 sw=4 expandtab : See Vim, :help 'modeline'
