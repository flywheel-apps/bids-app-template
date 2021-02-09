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

    print("Job ID", job_id)
    job = fw.get_job(job_id)
    gear = fw.get_gear(job.gear_id)
    print(f"gear.gear.name is {gear.gear.name}")
    destination_id = job.config["destination"]["id"]
    print(f"job's analysis destination_id is {destination_id}")
    analysis = fw.get_analysis(destination_id)
    print(f"job's analysis's parent's type is {analysis.parent['type']}")
    project_id = analysis.parents["project"]
    project = fw.get_project(project_id)
    project_label = project.label
    print(f"Project label: {project.label}")
    destination = fw.get(analysis.parent["id"])
    print(f"job's destination is {destination.label}")
    script_name = f"{project_label}_{analysis.parent['type']}_{destination.label}.py"
    script_name = script_name.replace(" ", "_")
    print(f"Creating script: {script_name} ...\n")

    input_files = dict()
    for key, val in job.config.get("inputs").items():
        input_files[key] = {
            "hierarchy_id": val["hierarchy"]["id"],
            "location_name": val["location"]["name"],
        }

    lines = f"""#! /usr/bin/env python3
'''Run {gear.gear.name} on {analysis.parent['type']} "{destination.label}"

    This script was created to run Job ID {job_id}
    In project "{project_label}"
    On Flywheel Instance {fw.get_config().site.api_url}
'''

import os
import argparse
from datetime import datetime


import flywheel


input_files = {pprint.pformat(input_files)}

def main():

    fw = flywheel.Client('')
    print(fw.get_config().site.api_url)

    gear = fw.lookup("gears/{gear.gear.name}")
    print("gear.gear.version for job was = {gear.gear.version}")"""

    with open(script_name, "w") as sfp:
        for line in lines.split("\n"):
            sfp.write(line + "\n")
        sfp.write('    print(f"gear.gear.version now = {gear.gear.version}")\n')
        sfp.write(f"    print(\"destination_id = {analysis.parent['id']}\")\n")
        sfp.write(f"    print(\"destination type is: {analysis.parent['type']}\")\n")
        sfp.write(f"    destination = fw.get(\"{analysis.parent['id']}\")\n")
        sfp.write("\n")
        sfp.write("    inputs = dict()\n")
        sfp.write(f"    for key, val in input_files.items():\n")
        sfp.write("         container = fw.get(val['hierarchy_id'])\n")
        sfp.write("         inputs[key] = container.get_file(val['location_name'])\n")
        sfp.write("\n")
        sfp.write(f"    config = {pprint.pformat(job['config']['config'], indent=4)}\n")
        sfp.write("\n")
        sfp.write("    now = datetime.now()\n")
        sfp.write("    analysis_label = (\n")
        sfp.write(
            "        f'{gear.gear.name} {now.strftime(\"%m-%d-%Y %H:%M:%S\")} SDK launched'\n"
        )
        sfp.write("    )\n")
        sfp.write('    print(f"analysis_label = {analysis_label}")\n')
        sfp.write("\n")
        sfp.write("    analysis_id = gear.run(\n")
        sfp.write("        analysis_label=analysis_label,\n")
        sfp.write("        config=config,\n")
        sfp.write("        inputs=inputs,\n")
        sfp.write("        destination=destination,\n")
        sfp.write("    )\n")
        sfp.write("    return analysis_id\n")
        sfp.write("\n")
        sfp.write("\n")
        sfp.write("if __name__ == '__main__':\n")
        sfp.write("\n")
        sfp.write("    parser = argparse.ArgumentParser(description=__doc__)\n")
        sfp.write("    args = parser.parse_args()\n")
        sfp.write("\n")
        sfp.write("    analysis_id = main()\n")
        sfp.write("\n")
        sfp.write('    print(f"analysis_id = {analysis_id}")\n')
        sfp.write("\n")
        sfp.write("    os.sys.exit(0)\n")

    os.system(f"black {script_name}")

    st = os.stat(script_name)
    os.chmod(script_name, st.st_mode | stat.S_IEXEC)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("job_id", help="Flywheel job ID")
    parser.add_argument("-v", "--verbose", action="count", default=0)

    args = parser.parse_args()

    main(args.job_id)

    os.sys.exit(0)
