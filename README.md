# bids-app-template
A Template for Gears running on BIDS formatted data

To create a bids-app gear, go to [bids-app-template-test](https://github.com/flywheel-apps/bids-app-template-test), and follow the steps.

As you develop new best practices for developing gears, be sure to add them in the code and describe them here.

# Best Gear Practices

## Logging

In `run.py`, initialize logging with something like this:

```python
    # Instantiate the Gear Context
    context = flywheel.GearContext()

    fmt = '%(asctime)s %(levelname)8s %(name)-8s - %(message)s'
    logging.basicConfig(level=context.config['gear-log-level'],format=fmt)

    log = logging.getLogger('[flywheel/bids-fmriprep]')

    log.info('log level is ' + context.config['gear-log-level'])

    context.log_config() # not configuring the log but logging the config
```
That is:
  - set log level using "gear-log-level" from the context/manifest
  - include the date/time in the format
  - get a logger for the run.py file.
  - log something into it to make sure it is working
  - add all of the configuration settings to the log

Then, for all modules (each python file that is not the main one, "run.py") in the gear, add a separate child log at the top of the file with:
```python
    log = logging.getLogger(__name__)
```

By using [logging in multiple modules](https://docs.python.org/3/howto/logging-cookbook.html#using-logging-in-multiple-modules) in this way, the log message will indicate which file generated the log message.

Finally, log information at the usual levels:
```python
    log.debug('very detailed information')
    log.info('informative text')
    log.warning('something that needs to be seen')
    log.error('something went wrong')
    log.critical('show stopper information')
    log.exception("something went wrong and here's a stack trace")
```

# To Do:
  * add continuous integration
  * change this GitHub project into a template?
