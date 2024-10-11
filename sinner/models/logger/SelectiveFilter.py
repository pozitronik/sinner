import logging

from sinner.models.logger.LogDestination import LogDestination


class SelectiveFilter(logging.Filter):
    def __init__(self, destination):
        super().__init__()
        self.destination = destination

    def filter(self, record):
        if not hasattr(record, 'destinations'):
            record.destinations = LogDestination.BOTH
        return self.destination in record.destinations
