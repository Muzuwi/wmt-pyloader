# wmt-pyloader

Work in progress, reverse-engineered, Python reimplementation of the `wmt_loader` executable for a MT8768T target.
The script performs some work required to initialize the WiFi hardware on non-Android systems (such as [postmarketOS](https://postmarketos.org/)).

The goal of this project is to possibly have `wmt-pyloader` be usable as a generic replacement for the WiFi initialization executables across different MTK SoCs/WiFi HW.
This may be too optimistic, so for now the script is focusing on supporting MT6765-based targets.

# Supported initialization methods

From what I can gather, there are multiple initialization methods for the WiFi HW.
The particular target this script is re-implementing utilizes the `/dev/wmtdetect` device available after loading the `wmt_drv` module.
There seem to be other methods of initialization as well (UART, SDIO?), which this script does not currently implement (some branches are missing, but the script will fail-exit when it hits one).

# Supported SoCs

- MT8768T
- Hopefully should work on other MT6765-based SoCs? Contributions welcome, even if just to say that it doesn't work on your particular device!

# Running

Python 3 is required, without any additional dependencies.
Copy the sources to the target and run the script as root:
```bash
sudo <path-to-wmt-pyloader.py>
```

# Current progress

`wmt-pyloader` can successfully initialize WiFi on a MT8768T-based device using MediaTek's out-of-tree connectivity modules.
FM/GPS/Bluetooth have not been investigated yet.

# Source of truth

The following executable extracted from an Android system image is used for reverse engineering the initialization logic (sha256sum):

`60f516c75b79bd4dc54a8abc7ecdb1c2e799c28adf76a91423d998944616817f wmt_loader`

# License

```
Copyright (C) 2024 Muzuwi

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```
