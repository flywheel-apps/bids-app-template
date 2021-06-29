[![CircleCI](https://circleci.com/gh/flywheel-apps/bids-app-template.svg?style=shield)](https://app.circleci.com/pipelines/github/flywheel-apps/bids-app-template)

## **Migrated to [GitLab](https://gitlab.com/flywheel-io/flywheel-apps/templates/bids-app-template)**

# bids-app-template
A Template for Gears running on BIDS formatted data.

This template has a complete set of features to help convert
[BIDS Apps](https://bids-apps.neuroimaging.io/about/) into
[Flywheel Gears](https://github.com/flywheel-io/gears/tree/master/spec).

To create a new BIDS App gear using this template click on "Use
this template" above and then edit `run.py`, `manifest.json`,
`Dockerfile` and other files as necessary to create your gear.  Most
of the changes you need to make are at the beginning of `run.py` and
`Dockerfile` (search for "editme").  Python modules in `utils/`
provide features to help set up the data to run on, call the BIDS
App command, and then get the results into the output folder.  This
template was created specifically for gears that run on BIDS formatted
data, but it can be a good start to any gear.  The file `manifest.json`
provides examples of inputs, configuration parameters, and references.
After running the tests (which builds the Docker container), this
template can be uploaded as is with `fw gear upload` and will run
as a gear.

## Quickstart

### Docker

Build the gear as a local [Docker](https://www.docker.com/) image
and run tests from the top level directory with:

```bash
./tests/bin/container-test.sh
```

By default, that will build the main docker image and a test image and then run
the tests inside the test docker container.

```pre
Usage:
    ./tests/bin/container-test.sh [OPTION...] [[--] TEST_ARGS...]
Run tests in a docker or singularity container.
Options:
    -h, --help         Print this help and exit
    -B, --no-build     Don't build the docker image (use existing)
    -C, --no-cache     Give Docker the --no-cache argument
    -s, --shell        Drop into the container with bash instead of normal entry
    -S, --singularity  Run in Singularity container instead of Docker
    -- TEST_ARGS       Arguments passed to tests.sh
```

After the docker image has been built, a convenient way to develop the gear is to
edit in one window and run tests inside the container in another window.  Do this
with:

```bash
./tests/bin/container-test.sh -B -s
```

The flag "-B" prevents building the docker images, and the "-s" flag drops into
a shell inside the docker container instead of running the tests.
Next, use this command to run the tests inside the container:

```bash
/src/tests/bin/tests.sh
```

This command runs docker and *inside the container* mounts `/src`
at the top level directory of the gear *outside the running container*.
This command runs tests inside the container while, in another
window outside the container, you can edit `run.py`, the modules
in `utils/`, and the tests in `tests/` and then use the above command
to make sure it works.  Running tests and editing code in this way
saves a lot of time because you don't have to re-build the docker
image after every change in the code.

To save even more time, you can run only a specific test by
adding `-- -k <testname>` to the end of the command, for example:

```bash
/src/tests/bin/tests.sh -- -k wet_run_errors
```

### Singularity

This template will build and test a [Singularity](https://sylabs.io/docs/)
image when you include the `-S` flag:

```bash
./tests/bin/container-test.sh -S
```

This builds the main gear's docker image, a test docker image, and then
builds a singularity test image using the docker test image.  It then runs
singularity on that test image to run all the tests.  The `-B` and `-s` flags
work as before to allow you to skip the builds and drop into a shell in the
running singularity container.

To run the tests from a shell inside the singularity container, use this:

```bash
./tests/bin/tests.sh
```

This is different from running the tests from inside the docker container because
by default, the singularity working directory is the top level directory of the gear.

In singularity, the main gear directory is not writeable so the first thing that
happens when executing the gear is to test if it is running in singularity and
to re-create the gear in `/tmp`.  For example:

```pre
Singularity> ls -lF /tmp/singularity-temp-lnppfbjd/flywheel/v0/
total 20
-rw-r--r-- 1 andy scien  613 Feb  2 19:52 config.json
drwxr-xr-x 2 andy scien 4096 Feb  2 19:52 freesurfer/
lrwxrwxrwx 1 andy scien   30 Feb  2 19:52 gear_environ.json -> /flywheel/v0/gear_environ.json
drwxr-xr-x 2 andy scien 4096 Feb  2 19:52 input/
lrwxrwxrwx 1 andy scien   26 Feb  2 19:52 manifest.json -> /flywheel/v0/manifest.json
drwxr-xr-x 3 andy scien 4096 Feb  2 19:52 output/
lrwxrwxrwx 1 andy scien   19 Feb  2 19:52 run.py -> /flywheel/v0/run.py*
lrwxrwxrwx 1 andy scien   18 Feb  2 19:52 tests -> /flywheel/v0/tests/
lrwxrwxrwx 1 andy scien   18 Feb  2 19:52 utils -> /flywheel/v0/utils/
drwxr-xr-x 3 andy scien 4096 Feb  2 19:52 work/
```

### Mimicking a running gear

Testing consists of unit tests and integration tests.  Unit tests test individual
functions in the modules in `utils/`.  The integration tests mimic a gear
running on a Flywheel instance by providing files and directories that are unzipped
inside the running docker container.  Here is what is added to `/flywheel/v0` for
the "dry_run" test:

```bash
    dry_run
    ├── config.json
    ├── input
    │   └── bidsignore
    │       └── bidsignore
    ├── output
    └── work
        └── bids
            ├── dataset_description.json
            └── sub-TOME3024
                └── ses-Session2
                    └── anat
                        ├── sub-TOME3024_ses-Session2_acq-MPR_T1w.json
                        └── sub-TOME3024_ses-Session2_acq-MPR_T1w.nii.gz
```

If you are logged in to a Flywheel instance on your local machine,
the integration tests can make SDK calls on that instance using
your api-key.

In the dry_run test shown above, BIDS formatted data is included
in the test so it does not need to be downloaded.  This gear won't
download data if `work/bids/` exists which saves a lot of time when
developing a BIDS App gear.  The "wet_run" test does download data
following a particular job id found in `config.json` just as the
job running on the platform would.  To make this test work for
you, change the "destination" ID in `config.json` to be the ID of
a valid Analysis container on your Flywheel instance.  Data will
be downloaded depending on the level where that analysis container
is attached (session, subject, or project).

The data for integration tests are stored in zip archives in
`tests/data/gear_tests`.  When creating or editing these integration
tests, the archives need to be unzipped.  When running the tests,
only the zipped files are used.  "Pack" and "unpack" commands are
provided in `tests/bin/` to create the zipped test files and to
allow editing of their contents.  From inside the `gear_tests`
directory, they can be run like this:

```bash
../../bin/pack-gear-tests.py all
../../bin/unpack-gear-tests.py dry_run.zip
```
Using the keyword "all", the first command zips all the *.zip
files in that directory and the second command above unzips only the
"dry_run" test.

### Final editing

To get the gear to work, you edit the Dockerfile and python scripts.
To add configuration parameters to pass to the algorithm inside
your gear, you edit the manifest.  It is important to provide good
descriptions of the gear and in each parameter in the manifest and
to document the maintainer of the gear (you) and the web links
because these things show up in the Flywheel interface.  Take a look
at the entire `manifest.json` file because there are examples of
all parts of the configuration and most will need to be changed
to be appropriate for your gear.

You also need to edit the version number of your gear.  The template
has its own version number but you should completely change that
to use the following convention.  Change the version number in the
manifest (in all three places) to be:

    MAJOR.MINOR.PATCH_MAJOR.MINOR.PATCH

Where the first MAJOR.MINOR.PATCH refers to the _gear_ version and the
second MAJOR.MINOR.PATCH refers to the _algorithm_ that the gear runs.

It is also important to put the appropriate information in the
README.md file of your gear.  The following is an example of that.

## Overview
This gear can only be run on datasets that have been BIDS curated
and can pass the tests of the [BIDS
Validator](https://github.com/bids-standard/bids-validator).
BIDS curation can be done before uploading data to the Flywheel
platform, or DICOM files can be uploaded and BIDS curation can be
done on the platform (see Setup below).

This Gear requires a (free) Freesurfer license. The license can be
provided to the Gear in 3 ways. See [How to include a Freesurfer
license file](https://docs.flywheel.io/hc/en-us/articles/360013235453).

This gear can run at the project, subject or session
level.  Because files are in the BIDS format, all the proper
files will be used for the given session, subject, or separately,
by subject, for the whole project.

## Setup: BIDS Curation
Before running BIDS curation on your data, you must first prepare
your data with the following steps:

1. Run the [SciTran: DICOM MR
Classifier](https://github.com/scitran-apps/dicom-mr-classifier)
gear on all the acquisitions in your dataset.  This step extracts
the DICOM header info, and store it as Flywheel Metadata.

1. Run the [DCM2NIIX: dcm2nii DICOM to NIfTI
converter](https://github.com/scitran-apps/dcm2niix) gear on all
the acquisitions in your dataset.  This step generates the Nifti
files that this gear needs from the DICOMS.  It also copies all
flywheel metadata from the DICOM to the Nifti file (In this case,
all the DICOM header information we extracted in step 1).

1. Run the [curate-bids gear](https://github.com/flywheel-apps/curate-bids)
on the project.  More information about BIDS Curation on Flywheel
can be found
[here](https://docs.flywheel.io/hc/en-us/articles/360008162154-BIDS-Overview),
and running the BIDS curation gear is described
[here](https://docs.flywheel.io/hc/en-us/articles/360009218434-BIDS-Curation-Gear).
If you need to rename sessions or subjects before curation, you may
find the gear helpful:
[bids-pre-curate](https://github.com/flywheel-apps/bids-pre-curate).

1. Run the gear on a session, subject, or project.

Steps 1 and 2 can be automatically carried out as [gear
rules](https://docs.flywheel.io/hc/en-us/articles/360008553133-Project-Gear-Rules).

These steps MUST be done in this order.  Nifti file headers have
significantly fewer fields than the DICOM headers.  File metadata
will be written to .json sidecars when the files are exported in
the BIDS format as expected by the BIDS App which is run by this gear.

## Running:
To run the gear, select a
[project](https://docs.flywheel.io/hc/en-us/articles/360017808354-EM-6-1-x-Release-Notes),
[subject](https://docs.flywheel.io/hc/en-us/articles/360038261213-Run-an-analysis-gear-on-a-subject)
or
[session](https://docs.flywheel.io/hc/en-us/articles/360015505453-Analysis-Gears).

Instead of running at the project level which will sequentially
step through each subject, you can launch multiple jobs on subjects
or sessions in parallel.  An example of running the gear on a subject
using the Flywheel SDK is in this [notebook](notebooks/run-gear.ipynb).
More details about running gears using the SDK can be found in this
[tutorial](https://gitlab.com/flywheel-io/public/flywheel-tutorials/-/blob/ad392d26131ef22408423b5a5c14104253d53cd6/python/batch-run-gears.ipynb).

# Inputs
### bidsignore (optional)
A list of patterns (like .gitignore syntax) defining files that should be ignored by the
bids validator.

### freesurfer_license (optional)
Your FreeSurfer license file. [Obtaining a license is free](https://surfer.nmr.mgh.harvard.edu/registration.html).
This file will be copied into the $FSHOME directory.  There are [three ways](https://docs.flywheel.io/hc/en-us/articles/360013235453-How-to-include-a-Freesurfer-license-file-in-order-to-run-the-fMRIPrep-gear-)
to provide the license to this gear.  A license is required for this gear to run.

# Run Level
This can run at the
[project](https://docs.flywheel.io/hc/en-us/articles/360017808354-EM-6-1-x-Release-Notes),
[subject](https://docs.flywheel.io/hc/en-us/articles/360038261213-Run-an-analysis-gear-on-a-subject) or
[session](https://docs.flywheel.io/hc/en-us/articles/360015505453-Analysis-Gears) level.

# Configuration Options
Note: arguments that start with "gear-" are not passed to the BIDS App.

### n_cpus (optional)
Number of CPUs/cores use.  The default is all available.

### verbose (optional)
Verbosity argument passed to the BIDS App.

### gear-run-bids-validation (optional)
Gear argument: Run bids-validator after downloading BIDS formatted data.  Default is true.

### gear-ignore-bids-errors (optional)
Gear argument: Run BIDS App even if BIDS errors are detected when gear runs bids-validator.

### gear-log-level (optional)
Gear argument: Gear Log verbosity level (INFO|DEBUG)

### gear-save-intermediate-output (optional)
Gear argument: The BIDS App is run in a "work/" directory.  Setting this will save ALL
contents of that directory including downloaded BIDS data.  The file will be named
"\<BIDS App>_work_\<run label>_\<analysis id>.zip"

### gear-intermediate-files (optional)
Gear argument: A space separated list of FILES to retain from the intermediate work
directory.  Files are saved into "\<BIDS App>_work_selected_\<run label>_\<analysis id>.zip"

### gear-intermediate-folders (optional)
Gear argument: A space separated list of FOLDERS to retain from the intermediate work
directory.  Files are saved into "\<BIDS App>_work_selected_\<run label>_\<analysis id>.zip"

### gear-dry-run (optional)
Gear argument: Do everything except actually executing the BIDS App.

### gear-keep-output (optional)
Gear argument: Don't delete output.  Output is always zipped into a single file for
easy download.  Choose this option to prevent output deletion after zipping.

### gear-FREESURFER_LICENSE (optional)
Gear argument: Text from license file generated during FreeSurfer registration.
Copy the contents of the license file and paste it into this argument.

# Workflow
This gear runs a short bash script that helps test the functionality of this
bids-app-template.

# Outputs
This gear produces some silly output that is not important just to
prove that it can.  It also adds some Custom Information to various
containers depending on the run level.

# Note

This gear was created from the Flywheel [BIDS App Template](https://github.com/flywheel-apps/bids-app-template) (version
major#_minor#_patch#).  See the
[bids-app-template/README](https://github.com/flywheel-apps/bids-app-template/blob/master/README.md)
for information on how to build this gear and run the tests.
