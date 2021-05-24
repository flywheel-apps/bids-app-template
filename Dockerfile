# editme: Change this to the BIDS App container
FROM python:3.9-buster as base

# editme: Change this to your email.
LABEL maintainer="support@flywheel.io"

ENV FLYWHEEL /flywheel/v0
WORKDIR ${FLYWHEEL}

# If it is not in the base image, install the algorithm you want to run
# in this gear:
COPY algorithm-to-gearify.sh ${FLYWHEEL}/algorithm-to-gearify.sh

# This is here to make gear code for Freesurfer to pass tests.
# You probably don't need it
ENV FREESURFER_HOME="/opt/freesurfer"
ENV SUBJECTS_DIR="/opt/freesurfer/subjects"

# Hopefully You won't need to change anything below this.

# Save docker environ here to keep it separate from the Flywheel gear environment
RUN python -c 'import os, json; f = open("/flywheel/v0/gear_environ.json", "w"); json.dump(dict(os.environ), f)'

RUN apt-get update && \
    curl -sL https://deb.nodesource.com/setup_10.x | bash - && \
    apt-get install -y \
    zip \
    nodejs \
    tree && \
    rm -rf /var/lib/apt/lists/* && \
    npm install -g bids-validator@1.5.7

# Set up python to run Flywheel SDK isolated from whatever is in the base image
RUN curl -sSLO \
    https://repo.continuum.io/miniconda/Miniconda3-py38_4.8.3-Linux-x86_64.sh && \
    bash Miniconda3-py38_4.8.3-Linux-x86_64.sh -b -p /usr/local/miniconda && \
    rm Miniconda3-py38_4.8.3-Linux-x86_64.sh

# Set CPATH for packages relying on compiled libs (e.g. indexed_gzip)
ENV PATH="/usr/local/miniconda/bin:$PATH" \
    CPATH="/usr/local/miniconda/include/:$CPATH" \
    LANG="C.UTF-8" \
    LC_ALL="C.UTF-8" \
    PYTHONNOUSERSITE=1

# Python 3.8.3 (default, May 19 2020, 18:47:26)
# [GCC 7.3.0] :: Anaconda, Inc. on linux
COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt && \
    rm -rf /root/.cache/pip

# Create symbolic link for Freesurfer license but delete the target because
# the gear's "freesurfer" directory will be created when the gear runs
RUN mkdir -p /opt/freesurfer/
RUN mkdir -p ${FLYWHEEL}/freesurfer
RUN touch ${FLYWHEEL}/freesurfer/license.txt
RUN ln -s ${FLYWHEEL}/freesurfer/license.txt /opt/freesurfer/license.txt
RUN rm -rf ${FLYWHEEL}/freesurfer

ENV PYTHONUNBUFFERED 1

COPY manifest.json ${FLYWHEEL}/manifest.json
COPY utils ${FLYWHEEL}/utils
COPY run.py ${FLYWHEEL}/run.py

RUN chmod a+x ${FLYWHEEL}/run.py
ENTRYPOINT ["/flywheel/v0/run.py"]
