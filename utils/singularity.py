"""Install Freesurfer license.txt file where algorithm expects it.
"""

import logging
import shutil
from pathlib import Path
import os
import tempfile

log = logging.getLogger(__name__)


def check_for_singularity():
    """If running in Singularity, copy gear to a temp dir and cd to there"""

    running_in = ""
    if "SINGULARITY_NAME" in os.environ:
        running_in = "Singularity"
        log.debug("SINGULARITY_NAME is %s", os.environ["SINGULARITY_NAME"])

        # remove any previous runs
        previous_runs = list(Path("/tmp").glob("singularity-temp-*"))
        log.debug("previous_runs = %s", previous_runs)
        for prev in previous_runs:
            log.debug("rm %s", prev)
            shutil.rmtree(prev)

        # Create temporary place to run gear
        WD=tempfile.mkdtemp(prefix="singularity-temp-", dir="/tmp")
        log.debug("Working directory is %s", WD)

        new_FWV0 = Path(WD + "/flywheel/v0/")
        new_FWV0.mkdir(parents=True)
        abs_path = Path(".").resolve()
        names = list(Path("/flywheel/v0/").glob("*"))
        for name in names:
            if name.name == "gear_environ.json":  # always use real one, not dev
                (new_FWV0 / name.name).symlink_to(Path("/flywheel/v0") / name.name)
            else:
                (new_FWV0 / name.name).symlink_to(abs_path / name.name)
        os.chdir(new_FWV0)
        log.debug("cwd is %s", Path().cwd())

    else:
        with open("/proc/self/cgroup") as fp:
            for line in fp:
                if re.search("/docker/", line):
                    running_in = "Docker"
                    break
    if running_in == "":
        log.debug("NOT running in Docker or Singularity")
    else:
        log.debug("Running in %s", running_in)
