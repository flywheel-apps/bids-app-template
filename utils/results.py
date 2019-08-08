#!/usr/bin/env python3

import os
import glob
import csv
import shutil
import subprocess as sp

from utils.G import *

def zip_html():
    """ Construct one index.html to rule them all 
        It will link to all .html files found in the output/ directory.
    """

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

    # get a list of all "group" html files
    html_files = glob.glob('*.html')

    lines = []
    for h_file in html_files:

        # First, add a link to that h_file file
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
    LOG.info(f' running "{cmd}"')
    result = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE, encoding='utf-8')
    LOG.info(' return code: ' + str(result.returncode))
    LOG.info(f' {cmd.split()[0]} output\n' + str(result.stdout))

# vi:set autoindent ts=4 sw=4 expandtab : See Vim, :help 'modeline'
