#!/usr/bin/env python3

import datetime
import glob
import os
import subprocess as sp

from utils.G import *


def zip_it_zip_it_good(name):
    """ Compress html file into an appropriately named archive file
        *.html.zip files are automatically shown in another tab in the browser """

    cmd = f'zip -q {name}.zip index.html'
    LOG.debug(f' creating viewable archive "{name}.zip"')
    result = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE, encoding='utf-8')
    if result.returncode != 0:
        LOG.info(f' Problem running {cmd}')
        LOG.info(' return code: ' + str(result.returncode))
        LOG.info(f' {cmd.split()[0]} output\n' + str(result.stdout))
    else:
        LOG.debug(' return code: ' + str(result.returncode))
        LOG.debug(f' {cmd.split()[0]} output\n' + str(result.stdout))


def zip_htmls():
    """ Since zip_all_html() doesn't work, each html file must be
        converted into an archive individually.
        For each html file, rename it to be "index.html", then create a zip
        archive from it.
    """

    LOG.info(' Creating viewable archives for all html files')
    os.chdir(OUTPUT_DIR)

    html_files = glob.glob('*.html')

    # if there is an index.html, do it first and re-name it for safe keeping
    save_name = ''
    if op.exists('index.html'):
        zip_it_zip_it_good('index.html')

        now = datetime.datetime.now()
        save_name = now.strftime("%Y-%m-%d_%H-%M-%S") + '_index.html'
        os.rename('index.html', save_name)

        html_files.remove('index.html')  # don't do this one later

    for h_file in html_files:
        os.rename(h_file, 'index.html')
        zip_it_zip_it_good(h_file)
        os.rename('index.html', h_file)

    # reestore if necessary
    if save_name != '':
        os.rename(save_name, 'index.html')


def zip_all_htmls():
    """ If there is no index.html, construct one that links to all
        html files.
        Then make a zip archive that has all html files.

        NOTE: Creating a single html file with links to all html files
        DOES NOT WORK because the server won't serve the pages at the links.
        So do not use this function unless something changes.
    """

    if not op.exists('index.html'):  # create one if it does not exist

        LOG.info(' Creating index.html')
        os.chdir(OUTPUT_DIR)

        # the first part of index.html
        html1 = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">\n' + \
                '<html>\n' + \
                '  <head>\n' + \
                '    <meta http-equiv="content-type" content="text/html; charset=UTF-8">\n' + \
                f'    <title>{COMMAND} Output</title>\n' + \
                '  </head>\n' + \
                '  <body>\n' + \
                f'    <b>{COMMAND} Output</b><br>\n' + \
                '    <br>\n' + \
                '    <tt>\n'

        # get a list of all html files
        html_files = glob.glob('*.html')

        lines = []
        for h_file in html_files:
            # create a link to that h_file file
            s = '    <a href="./' + h_file + '">' + h_file[:-5] + '</a><br>\n'
            lines.append(s)

        # The final part of index.html
        html2 = '    <br>\n' + \
                '    </tt>\n' + \
                '  </body>\n' + \
                '</html>\n'

        # put all of that text into the actual file
        with open("index.html", "w") as text_file:
            text_file.write(html1)
            for line in lines:
                text_file.write(line)
            text_file.write(html2)

    # compress everything into an appropriately named archive file
    # *.html.zip file are automatically shown in another tab in the browser
    cmd = f'zip -q {COMMAND}.html.zip *.html'
    LOG.info(f' creating viewable html archive "{cmd}"')
    result = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE, encoding='utf-8')
    if result.returncode != 0:
        LOG.info(' return code: ' + str(result.returncode))
        LOG.info(f' {cmd.split()[0]} output\n' + str(result.stdout))

# vi:set autoindent ts=4 sw=4 expandtab : See Vim, :help 'modeline'
