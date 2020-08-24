# bids-app-template
A Template for Gears running on BIDS formatted data.

This template has a complete set of features for to help convert
[BIDS Apps](https://bids-apps.neuroimaging.io/about/) into
[Flywheel Gears](https://github.com/flywheel-io/gears/tree/master/spec).

To create a new BIDS App gear using this template click on "Use this template" above and
then edit `run.py`, `manifest.json`, `Dockerfile` and other files as necessary to create
your gear.  Python modules in `utils/` provide features to help set up the data to run on,
call the BIDS App command, and then get the results into the output folder.  This template
was created specifically for gears that run on BIDS formatted data, but it can be a good start
to any gear.  The file `manifest.json` provides examples of inputs, configuration parameters, and
references.  This template can be uploaded as is and will run as a gear.

Run the tests from the top level directory with:

```bash
./tests/bin/docker-test.sh
```

That will build the main docker image and a test image and then run
the tests inside the docker container.  Provide the flag "-B" to
prevent building the docker images and the "-s" flag to drop into
a shell inside the docker container instead of running the tests.
Once inside the container use this command to run the tests:

```bash
/src/tests/bin/tests.sh
```

The top level directory is mounted at `/src` so you can edit `run.py`, the modules in
`utils/`, and the tests in `tests/` and then use the above command to make sure it works.

Testing consists of unit tests and integration tests.  The integration tests mimic a gear
running on a Flywheel instance by providing files and directories that will be unzipped
inside the running docker container.  Here is the "dry_run" test:

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

If you are logged in to a Flywheel instance and have a fake api-key installed in `config.json`,
these integration tests can make SDK calls on that instance using your api-key.

In the dry_run test shown above, BIDS formatted data is included in the test so it does not need
to be downloaded.  This gear won't download data if `work/bids/` exists which saves a lot of time
when developing a BIDS App gear.  The "wet_run" test does download data following a particular
job id found in `config.json` just as the job running on that platform would.

The data for integration tests are stored in zip archives in `tests/data/gear_tests`.  When creating
or editing these integration tests, the archives need to be unzipped.  When running the tests,
only the zipped files are used.  "Pack" and "unpack" commands are provided in `tests/bin/` to
create the zipped test files and to allow editing of their contents.  From inside the `gear_tests`
directory, they can be run like this:

```bash
../../bin/pack-gear-tests.py all
../../bin/unpack-gear-tests.py dry_run.zip
```

Using the keyword "all", the first command zips all of the *.zip files in that directory and
the second command above unzips the "dry_run" test.

It is also important to put the appropriate information in the README.md file.  The following
is an example of that.

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
Gear argument: Gear Log verbosity level (ERROR|WARNING|INFO|DEBUG)

### gear-save-intermediate-output (optional)
Gear argument: The BIDS App is run in a "work/" directory.  Setting this will save ALL
contents of that directory including downloaded BIDS data.  The file will be named
"<BIDS App>_work_<run label>_<analysis id>.zip"

### gear-intermediate-files (optional)
Gear argument: A space separated list of FILES to retain from the intermediate work
directory.  Files are saved into "<BIDS App>_work_selected_<run label>_<analysis id>.zip"

### gear-intermediate-folders (optional)
Gear argument: A space separated list of FOLDERS to retain from the intermediate work
directory.  Files are saved into "<BIDS App>_work_selected_<run label>_<analysis id>.zip"

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
bids-app-teamplate.

# Outputs
This gear produces some silly output that is not important just to prove that it can.
