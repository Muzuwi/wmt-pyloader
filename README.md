# wmt-pyloader

Work in progress, reverse-engineered, Python reimplementation of the `wmt_loader` executable for a MT8768T target.
The script performs some work required to initialize the WiFi hardware on non-Android systems (such as [postmarketOS](https://postmarketos.org/)).

The goal of this project is to possibly have `wmt-pyloader` be usable as a generic replacement for the WiFi initialization executables across different MTK SoCs/WiFi HW.
This may be too optimistic, and for now the script only re-implements some of the logic done by the `wmt_loader` executable for an MT8768T target (or more precisely: SM-T225 / samsung-gta7litewifi tablet).

# Supported initialization methods

From what I can gather, there are multiple initialization methods for the WiFi HW.
The particular target this script is re-implementing utilizes the `/dev/wmtdetect` device available after loading the `wmt_drv` module.
There seem to be other methods of initialization as well (UART, SDIO?), which this script does not currently implement (some branches are missing, but the script will fail-exit when it hits one).

# Supported SoCs

- MT8768T

# Running

Python 3 is required, without any additional dependencies.
Simply run the script as root on the target:
```bash
sudo <path-to-wmt-pyloader.py>
```

# Current progress

All testing is done on a SM-T225 tablet running postmarketOS.
Running the script causes `/dev/wmtWifi` to appear, trying to enable it by running `echo 1 > /dev/wmtWifi` initially appears to work but fails after a timeout with:
```
[  229.608017]  (6)[3657:sh][HIF-SDIO][D]wmt_lib_put_act_op:osal_wait_for_signal_timeout:994
[  229.608052]  (6)[3657:sh][HIF-SDIO][W]wmt_lib_put_act_op:opId(3) result:-3
[  229.608089]  (6)[3657:sh][WMT-PLAT][D]wmt_plat_wake_lock_ctrl:WMT-PLAT: after wake_unlock(0), counter(0)
[  229.608125]  (6)[3657:sh][HIF-SDIO][W]mtk_wcn_wmt_func_ctrl:OPID(3) type(3) fail
[  229.608147]  (6)[3657:sh][MTK-WIFI] WIFI_write[E]: WMT turn on WIFI fail!
```
Currently unsure if this is caused by some initialization step missing, or if the kernel modules are somehow built incorrectly.

# Chain of initialization

Rough chain of initialization of the WiFi hardware on SM-T225:

1. *load wmt_drv module*
1. **wmt_loader**   <- partially reimplemented by wmt-pyloader
1. *load wmt_chrdev_wifi module*
1. *load wlan_drv_gen4m module*
1. **wlan_assistant**   <- writes NVRAM to `/dev/wmtWifi`, could theoretically be done by wmt-pyloader as well

The out-of-tree modules for this target can be found here: https://codeberg.org/lowendlibre/mt8768-modules

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
