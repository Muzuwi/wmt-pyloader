from ioctl import do_ioctl, ior, iow
import os
import struct
import logformat

logger = logformat.get_logger()


DETECT_NODE = "/dev/wmtdetect"
PROC_WMT_DBG = "/proc/driver/wmt_dbg"
PROC_WMT_AEE = "/proc/driver/wmt_aee"
CHIPID = "-1"
CHIPID_VALIDITY_BYTES = b"\x20\x66\x00\x00\x28\x66\x00\x00\x30\x66\x00\x00\x32\x66\x00\x00\x72\x65\x00\x00\x82\x65\x00\x00\x92\x65\x00\x00\x27\x81\x00\x00\x71\x65\x00\x00\x52\x67\x00\x00\x35\x67\x00\x00\x21\x03\x00\x00\x35\x03\x00\x00\x37\x03\x00\x00\x63\x81\x00\x00\x80\x65\x00\x00\x55\x67\x00\x00\x26\x03\x00\x00\x97\x67\x00\x00\x79\x02\x00\x00\x57\x67\x00\x00\x51\x05\x00\x00\x67\x81\x00\x00\x59\x67\x00\x00\x07\x05\x00\x00\x63\x67\x00\x00\x90\x06\x00\x00\x70\x65\x00\x00\x13\x07\x00\x00\x75\x67\x00\x00\x88\x07\x00\x00\x71\x67\x00\x00\x65\x67\x00\x00\x67\x39\x00\x00\x61\x67\x00\x00\x79\x67\x00\x00\x68\x67\x00\x00\x85\x67\x00\x00\x73\x68\x00\x00\x68\x81\x00\x00\x53\x68\x00\x00\x33\x68\x00\x00\x81\x67\x00\x00"
CHIPID_VALIDITY = struct.unpack(
    "<{}I".format(len(CHIPID_VALIDITY_BYTES) // 4), CHIPID_VALIDITY_BYTES
)

WMT_DETECT_IOC_MAGIC = ord("w")
COMBO_IOCTL_GET_CHIP_ID = ior(WMT_DETECT_IOC_MAGIC, 0, "int")
COMBO_IOCTL_SET_CHIP_ID = iow(WMT_DETECT_IOC_MAGIC, 1, "int")
COMBO_IOCTL_EXT_CHIP_DETECT = ior(WMT_DETECT_IOC_MAGIC, 2, "int")
COMBO_IOCTL_GET_SOC_CHIP_ID = ior(WMT_DETECT_IOC_MAGIC, 3, "int")
COMBO_IOCTL_DO_MODULE_INIT = ior(WMT_DETECT_IOC_MAGIC, 4, "int")
COMBO_IOCTL_MODULE_CLEANUP = ior(WMT_DETECT_IOC_MAGIC, 5, "int")
COMBO_IOCTL_EXT_CHIP_PWR_ON = ior(WMT_DETECT_IOC_MAGIC, 6, "int")
COMBO_IOCTL_EXT_CHIP_PWR_OFF = ior(WMT_DETECT_IOC_MAGIC, 7, "int")
COMBO_IOCTL_DO_SDIO_AUDOK = ior(WMT_DETECT_IOC_MAGIC, 8, "int")
COMBO_IOCTL_GET_ADIE_CHIP_ID = ior(WMT_DETECT_IOC_MAGIC, 9, "int")
COMBO_IOCTL_CONNSYS_SOC_HW_INIT = ior(WMT_DETECT_IOC_MAGIC, 10, "int")


def do_loader() -> int:
    global persist_vendor_connsys_chipid

    try:
        fd = open(DETECT_NODE, "wb")
    except:
        logger.error(f"Failed to open {DETECT_NODE}")
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
        logger.warning("Unimplemented branch ioctl(0x8004770a) with err(0)")

    chipid = None
    is_inited = False
    while True:
        chip_id_ioctl = None

        # Chip power on
        err = do_ioctl(fd, COMBO_IOCTL_EXT_CHIP_PWR_ON)
        if err == 0:
            logger.error(f"Unimplemented branch ioctl(0x8004770a) with err({err})")
            fd.close()
            return 1
        else:
            if err != -1:
                logger.error(f"External combo power-on failed with err({err})")
                fd.close()
                return 1

            is_inited = True
            chip_id_ioctl = COMBO_IOCTL_GET_SOC_CHIP_ID
            logger.debug("SOC chip no need do combo chip power on")

        # Read chip ID
        chipid = do_ioctl(fd, chip_id_ioctl, 0) & 0xFFFFFFFF
        logger.info(f"Detected chip ID: {hex(chipid)}")

        if is_inited:
            break

        # I guess then it tries to initialize other types of modules?
        # Below is untested, works on my machine (tm)

        # "do SDIO3.0 autok"
        # What does this even mean?
        err = do_ioctl(fd, COMBO_IOCTL_DO_SDIO_AUDOK, chipid)
        if err != 0:
            logger.error(f"COMBO_IOCTL_DO_SDIO_AUDOK ioctl failed with err({err})")
            fd.close()
            return 1
        logger.debug("SDIO3.0 autok done")

        # "external combo chip power off"
        err = do_ioctl(fd, COMBO_IOCTL_EXT_CHIP_PWR_OFF)
        if err != 0:
            logger.error("External combo chip power off failed")
            fd.close()
            return 1
        logger.info("External combo chip power off done")

    err = do_ioctl(fd, COMBO_IOCTL_SET_CHIP_ID, chipid & 0xFFFFFFFF)
    chip_type = identify_chip_type_magic(err, chipid & 0xFFFFFFFF)

    persist_vendor_connsys_chipid = chipid & 0xFFFFFFFF
    if chip_type is None:
        # Doesn't look fatal?
        logger.warning(f"Invalid loaderfd: {hex(err)}")
    else:
        err = do_ioctl(fd, COMBO_IOCTL_MODULE_CLEANUP, chip_type)
        if err == 0:
            err = do_ioctl(fd, COMBO_IOCTL_DO_MODULE_INIT, chip_type)
            if err == 0:
                logger.info("COMBO_IOCTL_DO_MODULE_INIT success!")
            else:
                logger.warning(f"COMBO_IOCTL_DO_MODULE_INIT failed: err{hex(err)}")
        else:
            logger.warning(f"COMBO_IOCTL_MODULE_CLEANUP call failed: err({hex(err)})")

    adie_chipid = do_ioctl(fd, COMBO_IOCTL_GET_ADIE_CHIP_ID, 0)
    if adie_chipid == -1:
        logger.error(f"Get ADIE chip ID failed: err({hex(adie_chipid)})")
        fd.close()
        return 1

    fd.close()

    logger.info(f"ADIE chip ID: {hex(adie_chipid)}")

    return 0


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
                logger.error(f"Chip ID error: err({hex(err)})")
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
