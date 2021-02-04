import logging
from pathlib import Path
from unittest import TestCase

from utils.fly.environment import get_and_log_environment


def test_get_and_log_environment_works(caplog, search_caplog):

    caplog.set_level(logging.DEBUG)

    user_json = Path(Path.home() / ".config/flywheel/user.json")
    if not user_json.exists():
        TestCase.skipTest("", f"No API key available in {str(user_json)}")

    environ = get_and_log_environment()
    print(environ)

    assert "PATH" in environ
    assert search_caplog(caplog, "Environment: ")
