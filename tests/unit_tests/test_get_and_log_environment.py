import logging

from utils.fly.environment import get_and_log_environment


def test_get_and_log_environment_works(caplog, search_caplog):

    caplog.set_level(logging.DEBUG)

    environ = get_and_log_environment()
    print(environ)

    assert "PATH" in environ
    assert search_caplog(caplog, "Environment: ")
