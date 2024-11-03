import json
import logging
import os

def get_logger():
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger("acme-challenge-dispatcher")
    logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

    class JSONFormatter(logging.Formatter):
        def format(self, record):
            self.datefmt = f'%Y-%m-%dT%H:%M:%S.{record.msecs:03.0f}Z'
            log_record = {
                'timestamp': self.formatTime(record, self.datefmt),
                'level': record.levelname,
                'service': 'acme-challenge-dispatcher',
                'version': os.getenv('VERSION', '1.0.0'),
                'message': record.getMessage(),
                'filename': record.filename,
                'function': record.funcName,
                'line': record.lineno
            }
            return json.dumps(log_record)

    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.propagate = False
    logger.addHandler(handler)
    return logger