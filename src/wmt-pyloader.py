#!/usr/bin/env python3
import argparse

import loader
import launcher


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="wmt_pyloader", description="Mediatek WiFi Loader"
    )
    parser.add_argument(
        "--skip-loader",
        action="store_true",
        default=False,
        dest="skip_loader",
        help="Do not perform Loader step",
    )
    args = parser.parse_args()

    if not args.skip_loader:
        err = loader.do_loader()
        if err != 0:
            print(f"wmt_pyloader: Loader step returned err({hex(err)})")
            return err

    err = launcher.do_launcher()
    if err != 0:
        print(f"wmt_pyloader: Launcher step returned err({hex(err)})")
        return err

    print("wmt_pyloader: Done!")
    return 0


if __name__ == "__main__":
    exit(main())
