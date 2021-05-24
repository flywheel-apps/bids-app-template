#! /usr/bin/env python3
"""Create a python script to re-run a job given the job ID for a gear that was run on Flywheel."""

import argparse
import os
import pprint
import stat

import flywheel


def main(job_id):

    fw = flywheel.Client("")
    print("Flywheel Instance", fw.get_config().site.api_url)

    analysis = None
    if args.analysis:
        analysis = fw.get_analysis(job_id)
        print(f"Getting job_id from analysis '{analysis.label}'")
        job_id = analysis.job.id

    print("Job ID", job_id)
    job = fw.get_job(job_id)
    gear = fw.get_gear(job.gear_id)
    print(f"gear.gear.name is {gear.gear.name}")
    destination_id = job.destination.id
    destination_type = job.destination.type
    print(f"job's destination_id is {destination_id} type {destination_type}")

    if job.destination.type == "analysis":
        analysis = fw.get_analysis(destination_id)
        destination_id = analysis.parent.id
        destination_type = analysis.parent.type
        print(f"job's analysis's parent id is {destination_id} type {destination_type}")

    destination = fw.get(destination_id)
    destination_label = destination.label
    print(f"new job's destination is {destination_label} type {destination_type}")

    group_id = destination.parents.group
    print(f"Group id: {group_id}")

    if destination_type == "project":
        project = destination
    else:
        project = fw.get_project(destination.parents.project)
    project_label = project.label
    print(f"Project label: {project.label}")

    script_name = f"{project_label}_{destination_type}_{destination.label}.py"
    script_name = script_name.replace(" ", "_")
    print(f"Creating script: {script_name} ...\n")

    container_path = "Invalid"

    if destination_type == "project":
        container_path = f"{group_id}/{project_label}"

    elif destination_type == "subject":
        container_path = f"{group_id}/{project_label}/{destination.label}"

    elif destination_type == "session":
        container_path = (
            f"{group_id}/{project_label}/{destination.subject.label}/"
            + f"{destination.label}"
        )

    elif destination_type == "acquisition":
        subject = fw.get_subject(destination.parents.subject)
        session = fw.get_session(destination.parents.session)
        container_path = (
            f"{group_id}/{project_label}/{subject.label}/{session.label}/"
            + f"{destination.label}"
        )

    else:
        print(f"Error: unknown destination type {destination_type}")

    input_files = dict()
    for key, val in job.config.get("inputs").items():
        if "hierarchy" in val:
            input_files[key] = {
                "hierarchy_id": val["hierarchy"]["id"],
                "location_name": val["location"]["name"],
            }

    lines = f"""#! /usr/bin/env python3
'''Run {gear.gear.name} on {destination_type} "{destination.label}"

    This script was created to run Job ID {job_id}
    In project "{group_id}/{project_label}"
    On Flywheel Instance {fw.get_config().site.api_url}
'''

import os
import argparse
from datetime import datetime


import flywheel


input_files = {pprint.pformat(input_files)}

def main(fw):

    gear = fw.lookup("gears/{gear.gear.name}")
    print("gear.gear.version for job was = {gear.gear.version}")"""

    sfp = open(script_name, "w")
    for line in lines.split("\n"):
        sfp.write(line + "\n")

    sfp.write('    print(f"gear.gear.version now = {gear.gear.version}")\n')
    sfp.write(f'    print("destination_id = {destination_id}")\n')
    sfp.write(f'    print("destination type is: {destination_type}")\n')

    sfp.write(f'    destination = fw.lookup("{container_path}")\n')

    sfp.write("\n")
    sfp.write("    inputs = dict()\n")
    sfp.write("    for key, val in input_files.items():\n")
    sfp.write("         container = fw.get(val['hierarchy_id'])\n")
    sfp.write("         inputs[key] = container.get_file(val['location_name'])\n")
    sfp.write("\n")
    sfp.write(f"    config = {pprint.pformat(job['config']['config'], indent=4)}\n")
    sfp.write("\n")

    if job.destination.type == "analysis":
        sfp.write("    now = datetime.now()\n")
        sfp.write("    analysis_label = (\n")
        sfp.write(
            "        f'{gear.gear.name} {now.strftime(\"%m-%d-%Y %H:%M:%S\")} SDK launched'\n"
        )
        sfp.write("    )\n")
        sfp.write("    print(f'analysis_label = {analysis_label}')\n")

        lines = f"""
    analysis_id = gear.run(
        analysis_label=analysis_label,
        config=config,
        inputs=inputs,
        destination=destination,
    )"""
        for line in lines.split("\n"):
            sfp.write(line + "\n")
        sfp.write("    print(f'analysis_id = {analysis_id}')\n")
        sfp.write("    return analysis_id\n")

    else:
        lines = f"""
    job_id = gear.run(
        config=config,
        inputs=inputs,
        destination=destination
    )"""
        for line in lines.split("\n"):
            sfp.write(line + "\n")
        sfp.write("    print(f'job_id = {job_id}')\n")
        sfp.write("    return job_id\n")

    lines = f"""
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args()

    fw = flywheel.Client('')
    print(fw.get_config().site.api_url)

    analysis_id = main(fw)"""

    for line in lines.split("\n"):
        sfp.write(line + "\n")

    sfp.write("\n")
    sfp.write("    os.sys.exit(0)\n")

    sfp.close()

    os.system(f"black {script_name}")

    st = os.stat(script_name)
    os.chmod(script_name, st.st_mode | stat.S_IEXEC)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("job_id", help="Flywheel job ID")
    parser.add_argument(
        "-a",
        "--analysis",
        action="store_true",
        help="ID provided is for the analysis (job destination)",
    )
    parser.add_argument("-v", "--verbose", action="count", default=0)

    args = parser.parse_args()

    main(args.job_id)

    os.sys.exit(0)
