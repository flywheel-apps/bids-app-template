# bids-app-template
A Template for Gears running on BIDS formatted data

To create a bids-app gear, follow these steps.

## Identify BIDS compatible open source code

* Check out https://github.com/BIDS-Apps.  Maybe it's already done.
* Note the open source license.  It need to be commercially friendly.

## Create GitHub Project

On https://github.com/flywheel-apps, hit the "new" button. 
  *  Create new repository with owner "flywheel-apps" and give it a lower-case-with-dashes name like "bids-freesurfer".  
  * Give it a description like, "Gear that runs freesurfer on BIDS-curated data".  
  * Keep it private for now, not that nobody should see it, but there's no need for a lot of intrusive questions about it before it is even released for the first time.  
  * Check the "Initialize this repository with a README", add a .gitignore for Python, and set the license to the same license as the open source code.
  * Press the "Create Repository" button.

At this point, you can continue on (below) to clone the project
localy and then copy in and edit the template files, or, even better,
clone [bids-app-template-test]
(https://github.com/flywheel-apps/bids-app-template-test), and it
will do that for you along with setting up a test environment for
your new BIDS App Gear.

## Clone the project locally and create "dev" branch locally and on Github:
```
git clone git@github.com:flywheel-apps/your-bids-app-name.git
cd your-bids-app-name
git checkout -b dev
git push -u origin dev
```

## Copy and edit the template files:
  * manifest.json
  * Dockerfile
  * requirements.txt
  * run.py
  
See [Building Gears](https://docs.flywheel.io/hc/en-us/articles/360015513653-Building-Gears) for more information.

As you develop new best practices for developing gears, be sure to add them here.

## To Do:
  * add continuous integration
  * change this GitHub project into a template?
