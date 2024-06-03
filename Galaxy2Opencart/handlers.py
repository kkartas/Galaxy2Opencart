import logging
import json

class JsonFileLogHandler(logging.Handler):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def emit(self, record):
        log_entry = {
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        
        with open(self.filename, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')