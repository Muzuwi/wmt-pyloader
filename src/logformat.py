import logging
import sys
import time


class LogFormatter(logging.Formatter):
    COLOR_MAP = {
        logging.WARNING: "\033[38;5;214m",
        logging.ERROR: "\033[38;5;196m",
    }
    RESET = "\033[0m"

    def formatPrefix(self, record: logging.LogRecord) -> str:
        pfx = self.COLOR_MAP.get(record.levelno, "")
        timestamp = time.strftime("%y-%m-%d %H:%M:%S", time.localtime(record.created))
        module = record.module
        level = record.levelname

        return f"[{timestamp}][{pfx}{level}{self.RESET}][{module}]"

    def formatLine(self, record: logging.LogRecord, line: str) -> str:
        return f"{self.formatPrefix(record)} {line}{self.RESET}"

    def format(self, record: logging.LogRecord):
        lines = [self.formatLine(record, record.getMessage())]
        if record.exc_info:
            exc = self.formatException(record.exc_info)
            for line in exc.splitlines():
                lines.append(self.formatLine(record, line))
        return "\n".join(lines)


def configure_logger():
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(LogFormatter())
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.handlers = [handler]


def get_logger():
    return logging.getLogger(__file__)


configure_logger()
