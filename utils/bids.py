#!/usr/bin/env python3

import subprocess as sp
import os.path as op
import json
import pprint

from utils.G import *

def download(context):
    """ Download all files from the session in BIDS format
        bids_path will point to the local BIDS folder
        This creates a simiple dataset_description.json if
        one did not get downloaded.
    """

    # the usual BIDS path:
    bids_path = op.join(FLYWHEEL_BASE, 'work/bids')

    # If BIDS was already downloaded, don't do it again
    # (this saves time when developing locally)
    if not op.isdir(bids_path):

        bids_path = context.download_session_bids()
        # Use the following command instead (after core is updated with a fix
        # for it) because it will return the existing dataset_description.json
        # file and does not download scans that mriqc does not handle.
        # bids_path = context.download_project_bids(folders=['anat', 'func'])

        # make sure dataset_description.json exists
        # Is there a way to download the dataset_description.json file from the 
        # platform instead of creating a generic stub?
        required_file = bids_path + '/dataset_description.json'
        if not op.exists(required_file):
            LOG.info(f' Creating missing {required_file}.')
            the_stuff = {
                "Acknowledgements": "",
                "Authors": [],
                "BIDSVersion": "1.2.0",
                "DatasetDOI": "",
                "Funding": "",
                "HowToAcknowledge": "",
                "License": "",
                "Name": "tome",
                "ReferencesAndLinks": [],
                "template": "project"
            }
            with open(required_file, 'w') as outfile:
                json.dump(the_stuff, outfile)
        else:
            LOG.info(f'{required_file} exists.')

        LOG.info(f' BIDS was downloaded into {bids_path}')

    else:
        LOG.info(f' Using existing BIDS path {bids_path}')

    return bids_path


def run_validation(config, bids_path, environ):
    """ Run BIDS Validator on bids_path
        Install BIDS Validator into container with: 
            RUN npm install -g bids-validator
        This prints a summary of files that are valid,
        and then lists errors and warnings.
        Then it exits if gear-abort-on-bids-error is set and
        if there are any errors.
        The config MUST contain both of these:
            gear-run-bids-validation
            gear-abort-on-bids-error
    """

    if config['gear-run-bids-validation']:

        command = ['bids-validator', '--verbose', '--json', bids_path]
        LOG.info(' Command:' + ' '.join(command))
        result = sp.run(command, stdout=sp.PIPE, stderr=sp.PIPE,
                        universal_newlines=True, env=environ)
        LOG.info(' bids-validator return code: ' + str(result.returncode))
        bids_output = json.loads(result.stdout)

        # show summary of valid BIDS stuff
        LOG.info(' bids-validator results:\n\nValid BIDS files summary:\n' + \
                 pprint.pformat(bids_output['summary'], indent=8) + '\n')

        num_bids_errors = len(bids_output['issues']['errors'])

        # show all errors
        for err in bids_output['issues']['errors']:
            err_msg = err['reason'] + '\n'
            for ff in err['files']:
                if ff["file"]:
                    err_msg += f'       {ff["file"]["relativePath"]}\n'
            LOG.error(' ' + err_msg)

        # show all warnings
        for warn in bids_output['issues']['warnings']:
            warn_msg = warn['reason'] + '\n'
            for ff in warn['files']:
                if ff["file"]:
                    warn_msg += f'       {ff["file"]["relativePath"]}\n'
            LOG.warning(' ' + warn_msg)

        if config['gear-abort-on-bids-error'] and num_bids_errors > 0:
            LOG.critical(f' {num_bids_errors} BIDS validation errors ' + \
                         'were detected: NOT running mriqc.')
            os.sys.exit(1)


# vi:set autoindent ts=4 sw=4 expandtab : See Vim, :help 'modeline'