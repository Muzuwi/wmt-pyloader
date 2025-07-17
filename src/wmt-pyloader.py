#!/usr/bin/env python3
import argparse
import logformat

from targets.MT6765 import MT6765

logger = logformat.get_logger()


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="wmt_pyloader", description="Mediatek WiFi Loader"
    )
    # TODO: For now arguments are unused as there's one target.
    args = parser.parse_args()
    _ = args

    target = MT6765()
    try:
        target.boot()
    except Exception as e:
        logger.exception("Failed to boot network")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
