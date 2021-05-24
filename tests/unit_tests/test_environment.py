import logging
from pathlib import Path
from unittest import TestCase

from run import get_and_log_environment

log = logging.getLogger(__name__)


def test_get_and_log_environment_works(caplog, search_caplog):

    # Skip this test in GitHub CI because it works locally and for real runs but not CI
    user_json = Path(Path.home() / ".config/flywheel/user.json")
    if not user_json.exists():
        TestCase.skipTest("", f"No API key available in {str(user_json)}")

    caplog.set_level(logging.DEBUG)

    environ = get_and_log_environment()

    assert environ["FLYWHEEL"] == "/flywheel/v0"
    assert environ["FREESURFER_HOME"] == "/opt/freesurfer"
    assert search_caplog(caplog, "FREESURFER_HOME=/opt/freesurfer")
    assert search_caplog(caplog, "Grabbing environment from /tmp/gear-temp-dir-")
