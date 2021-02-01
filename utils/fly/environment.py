import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)


def get_and_log_environment():
    """Grab and log environment to use when executing command lines.

    The shell environment is saved into a file at an appropriate place in the Dockerfile.

    Returns: environ (dict) the shell environment variables
    """
    environment_file = Path().cwd() / "gear_environ.json"

    with open(environment_file, "r") as f:
        environ = json.load(f)

        # Add environment to log if debugging
        kv = ""
        for k, v in environ.items():
            kv += k + "=" + v + " "
        log.debug("Environment: " + kv)

    return environ
