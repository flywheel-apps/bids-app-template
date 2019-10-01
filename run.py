#!/usr/bin/env python3
""" Run the gear: set up for and call command-line code """

import json
import os, os.path as op
import subprocess as sp
import sys
import logging
import psutil

import flywheel

# GearContext takes care of most of these variables
# from utils.G import *
from utils import args, bids, results


if __name__ == '__main__':

    # Instantiate the Gear Context
    context = flywheel.GearContext()

    fmt = '%(asctime)s %(levelname)8s %(name)-8s - %(message)s'
    logging.basicConfig(level=context.config['gear-log-level'],format=fmt)

    log = logging.getLogger('[flywheel/bids-fmriprep]')

    log.info('log level is ' + context.config['gear-log-level'])

    context.log_config() # not configuring the log but logging the config

    # Instantiate custom gear dictionary to hold "gear global" info
    context.gear_dict = {}

    # the usual BIDS path:
    bids_path = op.join(context.work_dir, 'bids')
    context.gear_dict['bids_path'] = bids_path

    context.gear_dict['errors'] = []

    # editme: optional feature
    log.debug('psutil.cpu_count()= '+str(psutil.cpu_count()))
    log.debug('psutil.virtual_memory().total= {:4.1f} GiB'.format(
                      psutil.virtual_memory().total / (1024 ** 3)))
    log.debug('psutil.virtual_memory().available= {:4.1f} GiB'.format(
                      psutil.virtual_memory().available / (1024 ** 3)))

    # grab environment for gear
    with open('/tmp/gear_environ.json', 'r') as f:
        environ = json.load(f)
        context.gear_dict['environ'] = environ

    # Call this if args.make_session_directory() or results.zip_output() is
    # called later because they expect context.gear_dict['session_label']
    args.set_session_label(context)

    try:

        # editme: Set the actual command to run the gear:
        command = ['echo']

        # editme: add positional arguments that the above caommand needs
        # This should be done here in case there are nargs='*' arguments
        command.append('output')
        command.append(context.gear_dict['bids_path'])
        command.append(context.output_dir)
        command.append('participant')

        # Put command into gear_dict so arguments can be added in args.
        context.gear_dict['command'] = command

        # Build a parameter dictionary specific for COMMAND
        args.build(context)

        # Validate the command parameter dictionary - make sure everything is 
        # ready to run so errors will appear before launching the actual gear 
        # code.  Raises Exception on fail
        args.validate(context)

    except Exception as e:
        context.gear_dict['errors'].append(e)
        log.critical(e,)
        log.exception('Error in parameter specification.',)

    try:

        # editme: optional feature
        # Create working output directory with session label as name
        args.make_session_directory(context)

        # Download bids for the current session
        bids.download(context)

        # editme: optional feature
        # Save bids file hierarchy `tree` output in .html file
        html_file = 'output/bids_tree'
        bids.tree(bids_path, html_file)
        log.info('Wrote tree("' + bids_path + '") output into html file "' +
                         html_file + '.html')

        # editme: optional feature, but recommended!
        # Validate Bids file heirarchy
        # Bids validation on a phantom tree may be occuring soon
        bids.run_validation(context)

        # TODO
        # see https://github.com/bids-standard/pybids/tree/master/examples
        # for any necessary work on the bids files inside the gear, perhaps
        # to query results or count stuff to estimate how long things will take.
        # Add that stuff to utils/bids.py

    except Exception as e:
        context.gear_dict['errors'].append(e)
        log.critical(e,)
        log.exception('Error in BIDS download and validation.',)

    try:

        # Build command-line string for subprocess and execute
        result = args.execute(context)

        log.info('Return code: ' + str(result.returncode))
        log.info(result.stdout)

        if result.returncode == 0:
            log.info('Command successfully executed!')

        else:
            log.error(result.stderr)
            log.info('Command failed.')

    except Exception as e:
        context.gear_dict['errors'].append(e)
        log.critical(e,)
        log.exception('Unable to execute command.')

    finally:

        # TODO
        # see https://github.com/bids-standard/pybids/tree/master/examples
        # for any necessary work on the bids files inside the gear, perhaps
        # to query results or count stuff to estimate how long things will take.
        # Add that stuff to utils/results.py

        # editme: optional feature
        # Cleanup, move all results to the output directory
        results.zip_htmls(context)

        # editme: optional feature
        # possibly save ALL intermediate output
        if context.config['gear-save-all-output']:
            results.zip_output(context)

        ret = result.returncode

        if len(context.gear_dict['errors']) > 0 :
            msg = 'Previous errors:\n'
            for err in context.gear_dict['errors']:
                msg += '  ' + str(type(err)).split("'")[1] + ': ' + str(err) + '\n'
            log.info(msg)
            ret = 1

        log.info('BIDS App Gear is done.')
        os.sys.exit(ret)
 

# vi:set autoindent ts=4 sw=4 expandtab : See Vim, :help 'modeline'
