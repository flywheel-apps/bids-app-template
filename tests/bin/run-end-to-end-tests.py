#!/usr/bin/env python3
"""Run all tests in ./tests/end-to-end-tests and monitor results.

Example:
    tests/bin/run-end-to-end-tests.py

"""

import argparse
import os
from pathlib import Path


def main():

    exit_code = 0

    tests = list(Path("tests/end-to-end-tests").glob("*"))

    for test in tests:
        print("\n" + test.name)
        os.system(test)
        # use output of tests to set up monitor gear

    # launch gear to monitor tests and produce dashboard of results
    # - check result (succeed/fail) and log for specific outcomes
    # based on what is being tested, i.e. "asserts"

    return exit_code


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-v", "--verbose", action="count", default=0)

    args = parser.parse_args()

    os.sys.exit(main())
