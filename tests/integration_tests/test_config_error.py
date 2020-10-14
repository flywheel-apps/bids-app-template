from pathlib import Path
from unittest import TestCase

import flywheel_gear_toolkit
from flywheel_gear_toolkit.utils.zip_tools import unzip_archive

import run


def test_dry_run_works(
    capfd, install_gear, print_captured, search_sysout,
):

    user_json = Path(Path.home() / ".config/flywheel/user.json")
    if not user_json.exists():
        TestCase.skipTest("", f"No API key available in {str(user_json)}")

    install_gear("config_error.zip")

    with flywheel_gear_toolkit.GearToolkitContext(input_args=[]) as gtk_context:

        status = run.main(gtk_context)

        captured = capfd.readouterr()
        print_captured(captured)

        assert status == 1
        assert search_sysout(captured, "It is 42")
        assert search_sysout(captured, "Error msg: A bad argument was found")
