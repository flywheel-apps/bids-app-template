# bids-app-template
A Template for Gears running on BIDS formatted data.

This template has a complete set of features for to help convert 
[BIDS Apps](https://bids-apps.neuroimaging.io/about/) into 
[Flywheel Gears](https://github.com/flywheel-io/gears/tree/master/spec).

To develop a new BIDS App gear, clone this repository locally using the new name for your gear:

```bash
git clone git@github.com:flywheel-apps/bids-app-template.git my-gear
```

Then edit `run.py`, `manifest.json`, `Dockerfile` and other files as necessary to create
your gear.  Python modules in `utils/` provide features to help set up the data to run on,
call the BIDS App command, and then get the results into the output folder.  This template
was created specifically for gears that run on BIDS formatted data, but it can be a good start
to any gear.  The file `manifest.json` provides examples of inputs, configuration parameters, and
references.  This template can be uploaded as is and will run as a gear.

Run the tests in the top level directory with:

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