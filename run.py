#!/usr/bin/env python3

import json
import os
import subprocess as sp
import psutil

import flywheel

from utils.G import *
import utils.args
import utils.bids
import utils.results


def main():
    config = context.config

    LOG.setLevel(getattr(logging, config['gear-log-level']))

    LOG.debug(f'psutil.cpu_count()= {psutil.cpu_count()}')
    LOG.debug(f'psutil.virtual_memory().total= {psutil.virtual_memory().total / (1024 ** 3):4.1f} GiB')
    LOG.debug(f'psutil.virtual_memory().available= {psutil.virtual_memory().available / (1024 ** 3):4.1f} GiB')

    # grab environment for gear
    with open('/tmp/gear_environ.json', 'r') as f:
        environ = json.load(f)

    try:

        bids_path = utils.bids.download(context)

        utils.bids.tree(bids_path, environ)

        utils.bids.run_validation(config, bids_path, environ)

        # Build a parameter dictionary specific for COMMAND
        params = utils.args.build(config)

        # Validate the command parameter dictionary
        # Raises Exception on fail
        utils.args.validate(params)

        # Build command-line string for subprocess to execute
        command = utils.args.build_command(params, bids_path)

        # Run the actual command this gear was created for
        result = sp.run(command, stdout=sp.PIPE, stderr=sp.PIPE,
                        universal_newlines=True, env=environ)

        LOG.info(' return code: ' + str(result.returncode))
        LOG.info(f' {COMMAND} output\n' + result.stdout)

        if result.returncode != 0:
            LOG.error(' The command:\n ' +
                      ' '.join(command) +
                      '\nfailed. See log for debugging.')
            LOG.error(' ' + result.stderr)
            os.sys.exit(result.returncode)
        else:
            LOG.info(f' {COMMAND} successfully executed!')

    except Exception as e:
        # LOG.error(e)
        LOG.exception('Ruh row, there was a problem.')
        os.sys.exit(1)

    finally:
        # Cleanup, move all results to the output directory

        utils.results.zip_htmls()

        # possibly save ALL intermediate output
        if config['gear-save-all-output']:
            os.chdir(FLYWHEEL_BASE)
            cmd = f'zip -r -q {OUTPUT_DIR}/{COMMAND}_work.zip work'
            LOG.info(f' running "{cmd}"')
            result = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE, encoding='utf-8')
            LOG.info(' return code: ' + str(result.returncode))
            LOG.info(f' {cmd.split()[0]} output\n' + str(result.stdout))


if __name__ == '__main__':
    with flywheel.GearContext() as context:
        context.init_logging()
        context.log_config()
        main()


# vi:set autoindent ts=4 sw=4 expandtab : See Vim, :help 'modeline'
