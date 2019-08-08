#!/usr/bin/env python3

import os.path as op
import logging

# These Gear basics global variables are in ALL CAPS

FLYWHEEL_BASE = '/flywheel/v0'
MANIFEST_FILE = op.join(FLYWHEEL_BASE, 'manifest.json')
CONFIG_FILE   = op.join(FLYWHEEL_BASE, 'config.json')
INPUT_DIR     = op.join(FLYWHEEL_BASE, 'input')
OUTPUT_DIR    = op.join(FLYWHEEL_BASE, 'output')
WORK_DIR      = op.join(FLYWHEEL_BASE, 'work')

COMMAND       = 'echo'

RESULT        = 'derivatives'

LOG = logging.getLogger('flywheel/bids-app-template')

# vi:set autoindent ts=4 sw=4 expandtab : See Vim, :help 'modeline'
