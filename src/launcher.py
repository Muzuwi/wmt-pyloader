import fcntl
import struct
import os
import argparse
import time
import threading


from ioctl import do_ioctl, ior, iow, iowr

WMT_IOC_MAGIC = 0xA0
WMT_IOCTL_SET_PATCH_NAME = iow(WMT_IOC_MAGIC, 4, "char*")
WMT_IOCTL_SET_STP_MODE = iow(WMT_IOC_MAGIC, 5, "int")
WMT_IOCTL_FUNC_ONOFF_CTRL = iow(WMT_IOC_MAGIC, 6, "int")
WMT_IOCTL_LPBK_POWER_CTRL = iow(WMT_IOC_MAGIC, 7, "int")
WMT_IOCTL_LPBK_TEST = iowr(WMT_IOC_MAGIC, 8, "char*")
WMT_IOCTL_GET_CHIP_INFO = ior(WMT_IOC_MAGIC, 12, "int")
WMT_IOCTL_SET_LAUNCHER_KILL = iow(WMT_IOC_MAGIC, 13, "int")
WMT_IOCTL_SET_PATCH_NUM = iow(WMT_IOC_MAGIC, 14, "int")
WMT_IOCTL_SET_PATCH_INFO = iow(WMT_IOC_MAGIC, 15, "char*")
WMT_IOCTL_PORT_NAME = iowr(WMT_IOC_MAGIC, 20, "char*")
WMT_IOCTL_WMT_CFG_NAME = iowr(WMT_IOC_MAGIC, 21, "char*")
WMT_IOCTL_WMT_QUERY_CHIPID = ior(WMT_IOC_MAGIC, 22, "int")
WMT_IOCTL_WMT_TELL_CHIPID = iow(WMT_IOC_MAGIC, 23, "int")
WMT_IOCTL_WMT_COREDUMP_CTRL = iow(WMT_IOC_MAGIC, 24, "int")
WMT_IOCTL_SEND_BGW_DS_CMD = iow(WMT_IOC_MAGIC, 25, "char*")
WMT_IOCTL_ADIE_LPBK_TEST = iowr(WMT_IOC_MAGIC, 26, "char*")
WMT_IOCTL_WMT_STP_ASSERT_CTRL = iow(WMT_IOC_MAGIC, 27, "int")
WMT_IOCTL_FW_DBGLOG_CTRL = ior(WMT_IOC_MAGIC, 29, "int")
WMT_IOCTL_DYNAMIC_DUMP_CTRL = ior(WMT_IOC_MAGIC, 30, "char*")
WMT_IOCTL_SET_ROM_PATCH_INFO = iow(WMT_IOC_MAGIC, 31, "char*")
WMT_IOCTL_GET_EMI_PHY_SIZE = ior(WMT_IOC_MAGIC, 33, "unsigned int")
WMT_IOCTL_FW_PATCH_UPDATE_RST = ior(WMT_IOC_MAGIC, 34, "int")
WMT_IOCTL_GET_VENDOR_PATCH_NUM = iow(WMT_IOC_MAGIC, 35, "int")
WMT_IOCTL_GET_VENDOR_PATCH_VERSION = ior(WMT_IOC_MAGIC, 36, "char*")
WMT_IOCTL_SET_VENDOR_PATCH_VERSION = iow(WMT_IOC_MAGIC, 37, "char*")
WMT_IOCTL_GET_CHECK_PATCH_STATUS = ior(WMT_IOC_MAGIC, 38, "int")
WMT_IOCTL_SET_CHECK_PATCH_STATUS = iow(WMT_IOC_MAGIC, 39, "int")
WMT_IOCTL_SET_ACTIVE_PATCH_VERSION = ior(WMT_IOC_MAGIC, 40, "char*")
WMT_IOCTL_GET_ACTIVE_PATCH_VERSION = ior(WMT_IOC_MAGIC, 41, "char*")
WMT_IOCTL_GET_DIRECT_PATH_EMI_SIZE = ior(WMT_IOC_MAGIC, 42, "unsigned int")


class WMTCHIN:
    CHIPID = 0
    HWVER = 1
    MAPPINGHWVER = 2
    FWVER = 3
    IPVER = 4
    ADIE = 5


WMT_DEV = "/dev/stpwmt"


class Launcher:
    def __init__(self) -> None:
        self.fd = -1

    def run(self) -> int:
        self.fd = os.open(WMT_DEV, os.O_CREAT | os.O_RDWR)
        if self.fd < 0:
            print(f"Failed to open {WMT_DEV}")
            print(f"Hint: {WMT_DEV} appears after performing the Loader step.")
            return 1

        while True:
            chipid = do_ioctl(self.fd, WMT_IOCTL_WMT_QUERY_CHIPID)
            if chipid != -1:
                break
            print(f"Launcher: WMT_IOCTL_WMT_QUERY_CHIPID failed! Retrying in 300ms..")
            time.sleep(0.3)
            continue
        print(f"Launcher: Chip ID={hex(chipid)}")
        fwver = do_ioctl(self.fd, WMT_IOCTL_GET_CHIP_INFO, WMTCHIN.MAPPINGHWVER)
        print(f"Launcher: Firmware Version={hex(fwver)}")

        weird_chip_id = (chipid - 0x6620) >> 1
        check_id = weird_chip_id | (chipid << 0x1F)
        print(f"check_id: {hex(check_id)}")
        if check_id < 10 and ((1 << (chipid) & 0x1F) & 0x311) != 0:
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
        do_ioctl(self.fd, WMT_IOCTL_SET_PATCH_NAME, g_wmt_cfg_name.encode())
        do_ioctl(self.fd, WMT_IOCTL_SET_STP_MODE, config)
        do_ioctl(self.fd, WMT_IOCTL_SET_LAUNCHER_KILL)

        t = threading.Thread(target=self._launcher_pwr_on_conn_thread)
        t.start()
        t = threading.Thread(target=self._launcher_response_thread)
        t.start()

        return 0

    def _launcher_pwr_on_conn_thread(self):
        magic_flag = False
        magic_value = 2 if magic_flag else 1
        count = 0
        while count < 0x14:
            err = do_ioctl(self.fd, WMT_IOCTL_LPBK_POWER_CTRL, magic_value)
            if err == 0:
                print("Power-on completed, closing..")
                break
            do_ioctl(self.fd, WMT_IOCTL_LPBK_POWER_CTRL, 0)
            print(f"Power-on failed! Retrying in 1s...")
            time.sleep(1.0)
            count += 1

    def _launcher_response_thread(self):
        import select

        print("Loader: waiting for patch request..")
        while True:
            r, _, _ = select.select([self.fd], [], [])
            if self.fd not in r:
                continue

            print("Loader: stpwmt contains data!")
            data = os.read(self.fd, 256)
            print(f"Loader: read data={data}")
            # FIXME: Implement!
            break


def do_launcher() -> int:
    launcher = Launcher()
    return launcher.run()
