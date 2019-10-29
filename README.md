# bids-app-template
A Template for Gears running on BIDS formatted data

To create a bids-app gear, go to [bids-app-template-test](https://github.com/flywheel-apps/bids-app-template-test), and follow the steps.

As you develop new best practices for developing gears, be sure to add them in the code and describe them here.

# Best Gear Practices

## Logging

In `run.py`, initialize logging with 
```python
    log = custom_log.init(context)
``` 

Then, for all modules (each python file that is not the main "run.py"), 
add a separate child log at the top of the file with:
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
