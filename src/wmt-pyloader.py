#!/usr/bin/env python3
import fcntl
import struct
import os
import argparse
import time
import threading

DEV_NODE = "/dev/wmtdetect"
LOADER_NODE = "/dev/stpwmt"
PROC_WMT_DBG = "/proc/driver/wmt_dbg"
PROC_WMT_AEE = "/proc/driver/wmt_aee"
CHIPID = "-1"
CHIPID_VALIDITY_BYTES = b"\x20\x66\x00\x00\x28\x66\x00\x00\x30\x66\x00\x00\x32\x66\x00\x00\x72\x65\x00\x00\x82\x65\x00\x00\x92\x65\x00\x00\x27\x81\x00\x00\x71\x65\x00\x00\x52\x67\x00\x00\x35\x67\x00\x00\x21\x03\x00\x00\x35\x03\x00\x00\x37\x03\x00\x00\x63\x81\x00\x00\x80\x65\x00\x00\x55\x67\x00\x00\x26\x03\x00\x00\x97\x67\x00\x00\x79\x02\x00\x00\x57\x67\x00\x00\x51\x05\x00\x00\x67\x81\x00\x00\x59\x67\x00\x00\x07\x05\x00\x00\x63\x67\x00\x00\x90\x06\x00\x00\x70\x65\x00\x00\x13\x07\x00\x00\x75\x67\x00\x00\x88\x07\x00\x00\x71\x67\x00\x00\x65\x67\x00\x00\x67\x39\x00\x00\x61\x67\x00\x00\x79\x67\x00\x00\x68\x67\x00\x00\x85\x67\x00\x00\x73\x68\x00\x00\x68\x81\x00\x00\x53\x68\x00\x00\x33\x68\x00\x00\x81\x67\x00\x00"
CHIPID_VALIDITY = struct.unpack(
    "<{}I".format(len(CHIPID_VALIDITY_BYTES) // 4), CHIPID_VALIDITY_BYTES
)

IOCTL_BASE_R = 0x80047700
IOCTL_BASE_W = 0x40047700
COMBO_IOCTL_GET_CHIP_ID = (IOCTL_BASE_R + 0) & 0xFFFFFFFF
COMBO_IOCTL_SET_CHIP_ID = (IOCTL_BASE_W + 1) & 0xFFFFFFFF
COMBO_IOCTL_EXT_CHIP_DETECT = (IOCTL_BASE_R + 2) & 0xFFFFFFFF
COMBO_IOCTL_GET_SOC_CHIP_ID = (IOCTL_BASE_R + 3) & 0xFFFFFFFF
COMBO_IOCTL_DO_MODULE_INIT = (IOCTL_BASE_R + 4) & 0xFFFFFFFF
COMBO_IOCTL_MODULE_CLEANUP = (IOCTL_BASE_R + 5) & 0xFFFFFFFF
COMBO_IOCTL_EXT_CHIP_PWR_ON = (IOCTL_BASE_R + 6) & 0xFFFFFFFF
COMBO_IOCTL_EXT_CHIP_PWR_OFF = (IOCTL_BASE_R + 7) & 0xFFFFFFFF
COMBO_IOCTL_DO_SDIO_AUDOK = (IOCTL_BASE_R + 8) & 0xFFFFFFFF
COMBO_IOCTL_GET_ADIE_CHIP_ID = (IOCTL_BASE_R + 9) & 0xFFFFFFFF
COMBO_IOCTL_CONNSYS_SOC_HW_INIT = (IOCTL_BASE_R + 10) & 0xFFFFFFFF

# FIXME: Made up names
IOCTL_STPWMT_PATCH = 0xC008A015
IOCTL_STPWMT_CONFIGURE_MODE = 0x4004A005
IOCTL_STPWMT_POWER_ON = 0x4004A007
IOCTL_STPWMT_CONFIGURE_FINI = 0x4004A00D
IOCTL_STPWMT_DUMP_FIRMWARE_LOG = 0x8004A01D

# Replacements for things that are passed via props
persist_vendor_connsys_chipid = None


def identify_chip_type_magic(err: int, chipid: int):
    """I have no idea what this does, it seems important

    Takes in err from SET_CHIP_ID and chipid used as arg for the ioctl
    """
    fallback = chipid & 0xFFFFFFFF

    if err < 0x507:
        if err < 0x321 + 0x17:
            if err in [0x321, 0x335, 0x337]:
                return 0x6735
            if err in [0x326]:
                return 0x6755
            return fallback
        else:
            if err == -1:
                print(f"wmt_pyloader: Chip ID error: err({hex(err)})")
                return None
            if err in [0x279]:
                return 0x6797
            return fallback
    elif err < 0x690:
        if err in [0x507]:
            return 0x6759
        if err in [0x551]:
            return 0x6757
        return fallback
    else:
        if err in [0x690]:
            return 0x6763
        if err in [0x713]:
            return 0x6775
        if err in [0x788]:
            return 0x6771
        return fallback


def do_ioctl(fd, ioctl: int, arg=0) -> int:
    # Python is being a bit too clever and throws an exception based on the status code
    # The driver of course re-uses some values for it's own custom statuses.
    try:
        err = fcntl.ioctl(fd, ioctl, arg)
    except OSError as e:
        err = -e.errno
    if isinstance(err, bytes):
        print(f"wmt_pyloader: ioctl({hex(ioctl)} bytes: {err}")
        return err
    print(f"wmt_pyloader: ioctl({hex(ioctl)}) returned err({hex(err)})")
    return err


def do_loader() -> int:
    global persist_vendor_connsys_chipid

    try:
        fd = open(DEV_NODE, "wb")
    except:
        print(f"Failed to open {DEV_NODE}")
        return 1

    # HW initialization
    err = do_ioctl(fd, COMBO_IOCTL_CONNSYS_SOC_HW_INIT)
    if err == 0:
        # This branch iterates over the CHIPID_VALIDITY array and compares the value of
        # persist.vendor.connsys.chipid trying to find a match.
        # FIXME: Implement this
        # For my SM-T225, the persist.vendor.connsys.chipid is -1, so this branch is irrelevant
        # But it actually does some ioctl's within here when it finds a match, so other devices
        # could require those ioctl's to function.
        print(f"FIXME: Unimplemented branch ioctl(0x8004770a) with err(0)")

    chipid = None
    is_inited = False
    while True:
        chip_id_ioctl = None

        # Chip power on
        err = do_ioctl(fd, COMBO_IOCTL_EXT_CHIP_PWR_ON)
        if err == 0:
            print(f"FIXME: Unimplemented branch ioctl(0x8004770a) with err({err})")
            fd.close()
            return 1
        else:
            if err != -1:
                print(f"wmt_pyloader: External combo power-on failed with err({err})")
                fd.close()
                return 1

            is_inited = True
            chip_id_ioctl = COMBO_IOCTL_GET_SOC_CHIP_ID
            print("wmt_pyloader: SOC chip no need do combo chip power on")

        # Read chip ID
        chipid = do_ioctl(fd, chip_id_ioctl, 0) & 0xFFFFFFFF
        print(f"wmt_pyloader: Detected chip ID: {hex(chipid)}")

        if is_inited:
            break

        # I guess then it tries to initialize other types of modules?
        # Below is untested, works on my machine (tm)

        # "do SDIO3.0 autok"
        # What does this even mean?
        err = do_ioctl(fd, COMBO_IOCTL_DO_SDIO_AUDOK, chipid)
        if err != 0:
            print("wmt_pyloader: 'do SDIO3.0 autok' failed!")
            fd.close()
            return 1
        print("wmt_pyloader: SDIO3.0 autok done")

        # "external combo chip power off"
        err = do_ioctl(fd, COMBO_IOCTL_EXT_CHIP_PWR_OFF)
        if err != 0:
            print("wmt_pyloader: External combo chip power off failed")
            fd.close()
            return 1
        print("wmt_pyloader: External combo chip power off done")

    err = do_ioctl(fd, COMBO_IOCTL_SET_CHIP_ID, chipid & 0xFFFFFFFF)
    chip_type = identify_chip_type_magic(err, chipid & 0xFFFFFFFF)

    persist_vendor_connsys_chipid = chipid & 0xFFFFFFFF
    if chip_type is None:
        # Doesn't look fatal?
        print(f"wmt_pyloader: Invalid loaderfd: {hex(err)}")
    else:
        err = do_ioctl(fd, COMBO_IOCTL_MODULE_CLEANUP, chip_type)
        if err == 0:
            err = do_ioctl(fd, COMBO_IOCTL_DO_MODULE_INIT, chip_type)
            if err == 0:
                print("wmt_pyloader: COMBO_IOCTL_DO_MODULE_INIT success!")
            else:
                print(f"wmt_pyloader: COMBO_IOCTL_DO_MODULE_INIT failed: err{hex(err)}")
        else:
            print(
                f"wmt_pyloader: COMBO_IOCTL_MODULE_CLEANUP call failed: err({hex(err)})"
            )

    adie_chipid = do_ioctl(fd, COMBO_IOCTL_GET_ADIE_CHIP_ID, 0)
    if adie_chipid == -1:
        print(f"wmt_pyloader: Get ADIE chip ID failed: err({hex(adie_chipid)})")
        fd.close()
        return 1

    fd.close()

    print(f"wmt_pyloader: ADIE chip ID: {hex(adie_chipid)}")
    try:
        os.chown(PROC_WMT_DBG, 2000, 1000)
    except Exception as e:
        print(f"wmt_pyloader: chown({PROC_WMT_DBG}, 2000, 1000) failed: {e}")
        return 1
    try:
        os.chown(PROC_WMT_AEE, 2000, 1000)
    except Exception as e:
        print(f"wmt_pyloader: chown({PROC_WMT_AEE}, 2000, 1000) failed: {e}")
        return 1

    return 0


def _launcher_pwr_on_conn_thread(stpwmt_fd: int, magic_flag: bool):
    print(f"Entering connsys power-on flow! Magic Flag={magic_flag}")
    magic_value = 2 if magic_flag else 1
    count = 0
    while count < 0x14:
        err = do_ioctl(stpwmt_fd, IOCTL_STPWMT_POWER_ON, magic_value)
        if err == 0:
            print("Power-on completed, closing..")
            break
        do_ioctl(stpwmt_fd, IOCTL_STPWMT_POWER_ON, 0)
        print(f"Power-on failed! Retrying in 1s...")
        time.sleep(1.0)
        count += 1


def _launcher_response_thread(stpwmt_fd: int):
    import select

    print("Loader: waiting for patch request..")
    while True:
        r, _, _ = select.select([stpwmt_fd], [], [])
        if stpwmt_fd not in r:
            continue

        print("Loader: stpwmt contains data!")
        data = os.read(stpwmt_fd, 256)
        print(f"Loader: read data={data}")
        # FIXME: Implement!
        break


def do_launcher() -> int:
    # O_CREAT | O_RDWR
    fd = os.open(LOADER_NODE, 0x102)
    if fd < 0:
        print(f"Failed to open {LOADER_NODE}")
        print(f"Hint: {LOADER_NODE} appears after performing the Loader step.")
        return 1

    used_chipid = None
    while True:
        if persist_vendor_connsys_chipid is not None:
            used_chipid = persist_vendor_connsys_chipid
            break
        print(f"WARNING: Chip ID was not set! Trying to retrieve chip ID from device")
        err = do_ioctl(fd, 0x8004A016, 0)
        if err == -1:
            print(
                f"WARNING: Get chip ID from {LOADER_NODE} failed! Retrying in 300ms.."
            )
            time.sleep(0.3)
            continue
        used_chipid = err
        break

    print(f"wmt_pyloader: Using chip ID: {hex(used_chipid)}")

    weird_chip_id = (used_chipid - 0x6620) >> 1
    check_id = weird_chip_id | (used_chipid << 0x1F)
    print(f"check_id: {hex(check_id)}")
    if check_id < 10 and ((1 << (used_chipid) & 0x1F) & 0x311) != 0:
        stp_mode = 4
        print("wmt_pyloader: FIXME: Unimplemented branch!")
        return 1
    else:
        stp_mode = 3
    fm_mode = 2

    baudrate = 4000000
    g_wmt_cfg_name = "WMT_SOC.cfg"
    patch_path = "/lib/firmware"

    if patch_path is None:
        print("wmt_pyloader: FIXME: Unimplemented branch! patch_path == null")
        return 1

    config = (baudrate << 8) | ((fm_mode & 0xF) << 4) | (stp_mode & 0xF)
    do_ioctl(fd, IOCTL_STPWMT_PATCH, g_wmt_cfg_name.encode())
    do_ioctl(fd, IOCTL_STPWMT_CONFIGURE_MODE, config)
    do_ioctl(fd, IOCTL_STPWMT_CONFIGURE_FINI)

    # FIXME: Magic flag passed from CLI arguments changes ioctl value for power on
    t = threading.Thread(
        target=_launcher_pwr_on_conn_thread,
        args=(
            fd,
            False,
        ),
    )
    t.start()

    # TODO: Log debug thread (but won't work on connsys)

    t = threading.Thread(target=_launcher_response_thread, args=(fd,))
    t.start()

    return 0


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
        err = do_loader()
        if err != 0:
            print(f"wmt_pyloader: Loader step returned err({hex(err)})")
            return err

    err = do_launcher()
    if err != 0:
        print(f"wmt_pyloader: Launcher step returned err({hex(err)})")
        return err

    print("wmt_pyloader: Done!")
    return 0


if __name__ == "__main__":
    exit(main())
