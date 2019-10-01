# bids-app-template
A Template for Gears running on BIDS formatted data

To create a bids-app gear, go to [bids-app-template-test](https://github.com/flywheel-apps/bids-app-template-test), and follow the steps.

As you develop new best practices for developing gears, be sure to add them in the code and describe them here.

# Best Practices

## Logging

In `run.py`, initialize logging with something like this

```python
    # Instantiate the Gear Context
    context = flywheel.GearContext()

    fmt = '%(asctime)s %(levelname)8s %(name)-8s - %(message)s'
    logging.basicConfig(level=context.config['gear-log-level'],format=fmt)

    log = logging.getLogger('[flywheel/bids-fmriprep]')

    log.info('log level is ' + context.config['gear-log-level'])

    context.log_config() # not configuring the log but logging the config
```

## To Do:
  * add continuous integration
  * change this GitHub project into a template?
