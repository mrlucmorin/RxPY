import logging
from datetime import datetime, timedelta

from rx.disposables import Disposable, SingleAssignmentDisposable, \
    CompositeDisposable
from rx.concurrency.scheduler import Scheduler
from rx.internal.basic import default_now

log = logging.getLogger("Rx")

class TwistedScheduler(Scheduler):
    """A scheduler that schedules work via the asyncio mainloop."""

    def __init__(self, reactor):
        self.reactor = reactor

    def schedule(self, action, state=None):
        return self.schedule_relative(0, action, state)
        
    def schedule_relative(self, duetime, action, state=None):
        """Schedules an action to be executed at duetime.

        Keyword arguments:
        duetime -- {timedelta} Relative time after which to execute the action.
        action -- {Function} Action to be executed.

        Returns {Disposable} The disposable object used to cancel the scheduled
        action (best effort)."""

        scheduler = self
        seconds = TwistedScheduler.normalize(duetime)
        
        disposable = SingleAssignmentDisposable()
        def interval():
            disposable.disposable = action(scheduler, state)

        log.debug("timeout: %s", seconds)
        handle = [self.reactor.callLater(seconds, interval)]

        def dispose():
            handle[0].cancel()

        return CompositeDisposable(disposable, Disposable(dispose))

    def schedule_absolute(self, duetime, action, state=None):
        """Schedules an action to be executed at duetime.

        Keyword arguments:
        duetime -- {datetime} Absolute time after which to execute the action.
        action -- {Function} Action to be executed.

        Returns {Disposable} The disposable object used to cancel the scheduled
        action (best effort)."""

        return self.schedule_relative(duetime - self.now(), action, state)

    def default_now(self):
        return self.reactor.seconds()
        
    @classmethod
    def normalize(cls, timespan):
        """Eventloop operates with seconds as floats"""
        nospan = 0

        if isinstance(timespan, timedelta):
            seconds = timespan.seconds+timespan.microseconds/1000000.0

        elif isinstance(timespan, datetime):
            seconds = timespan.totimestamp()
        else:
            seconds = timespan

        if not timespan or timespan < nospan:
            seconds = nospan

        return seconds

