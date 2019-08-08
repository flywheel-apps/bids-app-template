#!/usr/bin/env python3

import os
import glob
import csv
import shutil
import subprocess as sp

from utils.G import *

def zip_html():
    """ Construct one index.html to rule them all so viewer can see them
        MRIQC outputs reports on subjects grouped by type of scan (T1,T2,dwi,func)
        They are html files in the output/ directory that link to each other.
        Each group .html file has a .tsv file that lists the individual subjects.
    """

    LOG.info(' Creating index.html')
    os.chdir(OUTPUT_DIR)

    # the first part of index.html
    html1 = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">\n' + \
            '<html>\n' + \
            '  <head>\n' + \
            '    <meta http-equiv="content-type" content="text/html; charset=UTF-8">\n' + \
            '    <title>MRIQC Output</title>\n' + \
            '  </head>\n' + \
            '  <body>\n' + \
            '    <b>MRIQC Output</b><br>\n' + \
            '    <br>\n' + \
            '    <tt>\n'

    # get a list of all "group" html files
    groups = glob.glob('group_*.html')

    lines = []
    for group in groups:

        # First, add a link to that group file
        s = '    <a href="./' + group + '">' + group[:-5] + '</a><br>\n'
        lines.append(s)

        # Then add a link each individual subject in that group
        s = '    <blockquote>\n'
        lines.append(s)

        # similarly named .tsv files tell the names of all individual subjects
        with open(group[:-5] + '.tsv') as tsvfile:

            reader = csv.reader(tsvfile, delimiter='\t')

            for rr, row in enumerate(reader):
                if rr > 0:
                    s = '      <a href="./' + row[0] + '.html' + '">' + row[0] + '</a><br>\n'
                    lines.append(s)

        s = '    </blockquote>\n'
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
    cmd = 'zip -q mriqc.html.zip *.html *.tsv'
    LOG.info(f' running "{cmd}"')
    result = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE, encoding='utf-8')
    LOG.info(' return code: ' + str(result.returncode))
    LOG.info(f' {cmd.split()[0]} output\n' + str(result.stdout))

# vi:set autoindent ts=4 sw=4 expandtab : See Vim, :help 'modeline'
