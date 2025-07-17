import logformat
import threading
import io
import re
import patch
import os

logger = logformat.get_logger()

KMSG_PATH = "/dev/kmsg"


def _kmsg_handle_line(line: str):
    rg = re.compile(r".*Direct firmware load for (.+?) failed.*")
    match = rg.search(line)
    if match is None:
        return
    filename = match.group(1)

    logger.warning(
        f"WARNING: kmsg listener found an error indicating the kernel failed to load a firmware file: {filename}"
    )
    logger.warning(
        f"Make sure this file exists in the {patch.PATCH_LOOKUP_DIRECTORY} directory!"
    )
    logger.warning(
        "This may indicate that firmware wasn't fully dumped from AOSP, or wmt-pyloader is picking the incorrect firmware for your device"
    )


def _kmsg_thread():
    try:
        with open(KMSG_PATH, "rt") as f:
            for line in f:
                _kmsg_handle_line(line)

    except Exception:
        logger.exception("kmsg listener error")
    except KeyboardInterrupt:
        return


def start_listener():
    """Listen for common warning lines on kmsg."""
    t = threading.Thread(target=_kmsg_thread)
    t.start()
