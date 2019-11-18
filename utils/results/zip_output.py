# If you edit this file, please consider updating bids-app-template

import os
import logging
import subprocess as sp


log = logging.getLogger(__name__)


def zip_output(context):
    """Create zipped results"""


    # This executes regardless of errors or exit status,

    # Zip file name has <subject> and <analysis>
    subject = context.gear_dict['subject_code']
    analysis_id = context.destination['id']
    file_name = 'fmriprep_' + subject + '_' + analysis_id + '.zip'
    dest_zip = os.path.join(context.output_dir,file_name)

    # The destination id is used as the subdirectory to put results into
    actual_dir = context.destination['id']
    full_path = context.output_dir + '/' + actual_dir

    if os.path.exists(full_path):

        log.debug('Output directory exists: ' + full_path)

        # fmriprep output went into output/analysis_id/...
        os.chdir(context.output_dir)

        log.info(
            'Zipping ' + actual_dir + ' directory to ' + dest_zip + '.'
        )
        command = ['zip', '-q', '-r', dest_zip, actual_dir]
        result = sp.run(command, check=True)

    else:

        log.error('Output directory does not exist: ' + full_path)

# vi:set autoindent ts=4 sw=4 expandtab : See Vim, :help 'modeline'
