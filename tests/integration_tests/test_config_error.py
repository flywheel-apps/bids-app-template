import logging
from pathlib import Path
from unittest import TestCase

import flywheel_gear_toolkit

import run


def test_config_error_errors(caplog, install_gear, search_caplog):
    caplog.set_level(logging.DEBUG)

    user_json = Path(Path.home() / ".config/flywheel/user.json")
    if not user_json.exists():
        TestCase.skipTest("", f"No API key available in {str(user_json)}")

    install_gear("config_error.zip")

    with flywheel_gear_toolkit.GearToolkitContext(input_args=[]) as gtk_context:

        status = run.main(gtk_context)

        assert status == 1
        assert search_caplog(caplog, "It is 42")
        assert search_caplog(caplog, "Error msg: A bad argument was found")
