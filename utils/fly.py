#!/usr/bin/env python3
"""
Functions that get info from Flywheel client, mmmmm helpful!
"""

import os


log = logging.getLogger(__name__)


def get_session_from_analysis_id(fw_client, input_analysis_id):
    """
    Returns the session associated with the input analysis id (if the parent is a session)
    :param fw_client: an instance of the flywheel client
    :type fw_client: flywheel.client.Client
    :param input_analysis_id: the id for the analysis container
    :type input_analysis_id: str
    :return: session, a flywheel session associated with the analysis
    :rtype: flywheel.models.session.Session
    """
    try:
        # Grab time for logging how long session get takes
        func_time_start = time.time()
        analysis = fw_client.get_analysis(input_analysis_id)
        session = fw_client.get_session(analysis.parent.id)

        log.info('Session ID is: {}'.format(session.get('_id')))
        if type(session) != flywheel.models.session.Session \
                or not session:
            log.error('{} is not a session. This gear must be run from the session level.'.format(analysis.parent.id))
            os.sys.exit(1)

        else:
            func_time_end = time.time()
            log.debug('It took {} seconds to get session'.format(func_time_end - func_time_start))
            return session

    except flywheel.ApiException as e:
        log.error('Exception encountered when getting session from analysis {}: {}'.format(input_analysis_id, e))
        os.sys.exit(1)


def set_session_label(context):
    """

    # This is used by args.make_session_directory() and 
    #                 results.zip_output()

    """
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


def get_session_uids(session, output_path):
    """
    Writes all unique UIDs for the input session to the output_path and returns the corresponding dictionary
    :param session: a flywheel session
    :type session: flywheel.models.session.Session
    :param output_path: the directory to which to write the json file containing session Study/SeriesInstanceUIDs
    :type output_path: str
    :param log: a Logger instance
    :type log: logging.Logger
    :return: session_dict, a dictionary containing session StudyInstanceUIDs and SeriesInstanceUIDs
    :rtype: dict
    """
    tag_list = ['SeriesInstanceUID', 'StudyInstanceUID']
    log.info('Getting UID info for session {} ({})'.format(session.id, session.label))
    session_dict = dict()

    for acquisition in session.acquisitions():
        log.info('Getting UID info for acquisition {} ({})'.format(acquisition.id, acquisition.label))
        acquisition = acquisition.reload()
        dicom_count = 0
        UID_entry_count = 0
        for file in acquisition.files:
            if file.type == 'dicom':
                log.debug('Processing DICOM: {}'.format(file.name))
                dicom_count += 1
                download_directory = tempfile.mkdtemp()
                try:
                    # Get a single image from the DICOM archive if possible
                    zip_member_file = file.get_zip_info().members[0]['path']
                    safe_file_name = make_file_name_safe(zip_member_file, log)
                    download_path = os.path.join(download_directory, safe_file_name)
                    file.download_zip_member(zip_member_file, download_path)
                    dicom_file_list = [download_path]
                # if can't get zip file member, download the whole archive
                except Exception as e:
                    log.warning('Could not access zip members:')
                    log.warning(e)
                    log.info('Downloading entire DICOM archive')
                    # Replace non-alphanumeric (or underscore) characters with x
                    safe_zip_name = make_file_name_safe(file.name, log)
                    download_path = os.path.join(download_directory, safe_zip_name)
                    file.download(download_path)
                    if zipfile.is_zipfile(download_path):
                        dicom_file_list = extract_return_path(download_path)
                    else:
                        dicom_file_list = [download_path]
                # import the dicom header info
                log.debug('Reading {}'.format(download_path))
                dicom_dict = import_dicom_header_as_dict(dicom_file_list[-1], tag_list, log)

                # Confirm that UIDs exist
                if not dicom_dict.get('StudyInstanceUID'):
                    log.error('No StudyInstanceUID present for file: {}'.format(file.name))
                if not dicom_dict.get('SeriesInstanceUID'):
                    log.error('No SeriesInstanceUID present for file: {}'.format(file.name))
                # Create key if it doesn't exist
                if dicom_dict.get('StudyInstanceUID'):
                    UID_entry_count += 1
                    if not session_dict.get(dicom_dict.get('StudyInstanceUID')):
                        session_dict[dicom_dict['StudyInstanceUID']] = list()
                    session_dict[dicom_dict['StudyInstanceUID']].append(dicom_dict['SeriesInstanceUID'])
                # Remove the extracted DICOM images
                shutil.rmtree(os.path.dirname(dicom_file_list[0]))
                # Remove the download zip
                if os.path.isdir(download_directory):
                    shutil.rmtree(download_directory)
                if session_dict:
                    with open(output_path, 'w') as f:
                        json.dump(session_dict, f, separators=(', ', ': '), indent=4)
        if dicom_count != UID_entry_count:
            log.error('expected {} StudyInstanceUIDs, found {}'.format(dicom_count, UID_entry_count))
            os.sys.exit(1)

    return session_dict


def get_root_client(fw_client):
    """
    Takes a flywheel client and gives it root mode if the user is site admin, otherwise just returns the input client
    :param fw_client: an instance of the flywheel client
    :type fw_client: flywheel.client.Client
    :param log: a Logger instance
    :type log: logging.Logger
    :return: fw_client: an instance of the flywheel client with root mode enabled if user is site admin
    """

    # parse the "url:" part of the api key from the site url
    site_url = fw_client.get_config().site.api_url
    site_patt = re.compile('https:\/\/(.*:).*')
    site_url = site_patt.match(site_url).group(1)
    user = fw_client.get_current_user()
    api_key = user.api_key.key
    # If the user is not admin, warn and return the input client
    if 'site_admin' in user.get('roles'):
        log.warning('User {} is not a site admin. Root mode will not be enabled.'.format(user.id))
        log.warning('User roles: {}'.format(user['roles']))
    else:
        fw_client = flywheel.Client(site_url+api_key, root=True)
    return fw_client


def load_manifest_json():
    """
    load the /flywheel/v0/manifest.json file as a dictionary
    :return: manifest_json
    :rtype: dict
    """
    config_file_path = '/flywheel/v0/manifest.json'
    with open(config_file_path) as manifest_data:
        manifest_json = json.load(manifest_data)
    return manifest_json


# vi:set autoindent ts=4 sw=4 expandtab : See Vim, :help 'modeline'
