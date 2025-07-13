import struct
import os
import time
import threading
import traceback
from typing import Optional
import patch


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

WMT_CHIPINFO_GET_CHIPID = 0
WMT_CHIPINFO_GET_HWVER = 1
WMT_CHIPINFO_GET_FWVER = 2
WMT_CHIPINFO_GET_IPVER = 3
WMT_CHIPINFO_GET_CHIP_TYPE = 4


class WMTCHIN:
    CHIPID = 0
    HWVER = 1
    MAPPINGHWVER = 2
    FWVER = 3
    IPVER = 4
    ADIE = 5


WMT_DEV = "/dev/stpwmt"
WMT_WIFI = "/dev/wmtWifi"
WMT_COMAMND_SRH_PATCH = b"srh_patch"
WMT_COMMAND_SRH_ROM_PATCH = b"srh_rom_patch"
ROM_PREFIXES = {
    "ROMv1": [0x6572, 0x6582, 0x6592, 0x6595],
    "ROMv2": [0x8127],
    "ROMv2_lm": [
        0x321,
        0x326,
        0x335,
        0x337,
        0x6735,
        0x6739,
        0x6752,
        0x6755,
        0x6757,
        0x6763,
    ],
    "ROMv3": [0x279],
    "ROMv4": [0x507, 0x6759],
    "ROMv4_be": [0x6771, 0x6775],
    "soc1_0": [0x6761, 0x6765, 0x6768, 0x6785, 0x3967, 0x8163],
    "soc2_0": [0x6779, 0x6853, 0x6873],
}
CHIP_RANGES_ROMv1 = range(0x6570, 0x6593)


def get_rom_patch_prefix(chip_id: int) -> str:
    """Determine the ROM patch prefix for srh_rom_patch commands."""
    prefix = "soc1_0"
    if chip_id == 0x6779 or chip_id == 0x6873 or chip_id == 0x6853:
        prefix = "soc2_0"
    elif chip_id == 0x6781:
        prefix = "soc2_2"
    elif chip_id == 0x6833:
        prefix = "soc2_2"
    return prefix


def get_patch_prefix(chip_id: int) -> str:
    """Determines the patch prefix for srh_patch commands."""
    for prefix, ids in ROM_PREFIXES.items():
        if chip_id in ids:
            return prefix

    if chip_id in CHIP_RANGES_ROMv1:
        if chip_id in ROM_PREFIXES["ROMv1"]:
            return "ROMv1"
        if chip_id in ROM_PREFIXES["ROMv2_lm"]:
            return "ROMv2_lm"
        if chip_id == 0x8127:
            return "ROMv2"
        if chip_id in [0x3967, 0x8163]:
            return "soc1_0"
        if chip_id in [0x6853, 0x6873]:
            return "soc2_0"

    known_prefix_ids = set(range(0x6736, 0x6797))
    if chip_id in known_prefix_ids:
        return f"mt{chip_id:x}"

    raise Exception(f"Don't know any patch prefix for chip_id {chip_id:x}")


def get_patch_suffix(chip_id: int) -> Optional[str]:
    # TODO: There's more logic to determining the suffix of the patch file.
    # This part uses the vendor.connsys.adie.chipid Android property, not
    # sure how that translates to the IDs you get from ioctl's.
    suffix = "1_1"
    return suffix


def create_set_rom_patch_request(patchinfo: bytes, patchfile: str) -> bytes:
    """Creates the request buffer to use during SET_ROM_PATCH_INFO ioctl."""
    if len(patchinfo) != 8:
        raise Exception(
            f"Invalid patchinfo length, expected 8 bytes, got {len(patchinfo)}"
        )
    if patchinfo[3] != 0xF0:
        raise Exception("Patchinfo byte 3 check failed")
    if patchinfo[7] >= 6:
        raise Exception(f"Patch info type invalid! ({patchinfo[7]} >= 6)")

    ioctlbuf = bytes()
    # 0..3: "type"
    ioctlbuf += struct.pack("<L", patchinfo[7])
    # 4..7: "addRess"
    # lowest byte is set to 0
    address = struct.pack(
        "<L",
        0x0 | patchinfo[1] << 8 | patchinfo[2] << 16 | patchinfo[3] << 24,
    )
    ioctlbuf += address
    # 8..264: "patchName"
    patchnameBytes = patchfile.encode()
    if len(patchnameBytes) > 255:
        raise Exception(f"Patch name exceeds max size ({len(patchnameBytes) > 255})")
    patchnameBytes += b"\x00" * (256 - len(patchnameBytes))
    ioctlbuf += patchnameBytes
    return ioctlbuf


def create_set_patch_request(patchinfo: bytes, patchfile: str) -> bytes:
    """Creates the request buffer to use during SET_ROM_PATCH ioctl."""
    ioctlbuf = bytes()
    # 0..3: "downloadSeq"
    ioctlbuf += struct.pack("<L", patchinfo[0] & 0xF)
    # 4..7: "addRess"
    # lowest byte is set to 0
    address = struct.pack(
        "<L",
        0x0 | patchinfo[1] << 8 | patchinfo[2] << 16 | patchinfo[3] << 24,
    )
    ioctlbuf += address
    # 8..264: "patchName"
    patchnameBytes = patchfile.encode()
    if len(patchnameBytes) > 255:
        raise Exception(f"Patch name exceeds max size ({len(patchnameBytes) > 255})")
    patchnameBytes += b"\x00" * (256 - len(patchnameBytes))
    ioctlbuf += patchnameBytes
    return ioctlbuf


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
        t = threading.Thread(target=self._launcher_wifi_enable_thread)
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

        print("launcher: Waiting for patch requests..")
        while True:
            r, _, _ = select.select([self.fd], [], [])
            if self.fd not in r:
                continue

            data = os.read(self.fd, 256)
            response = b"fail"
            try:
                self._handle_launcher_cmd(data)
                response = b"ok"
            except Exception as e:
                print("WARNING: Command handling failed with:", e)
                traceback.print_exception(e)
            print(f"launcher: response={response}")
            os.write(self.fd, response)

    def _launcher_wifi_enable_thread(self):
        while True:
            if not os.path.exists(WMT_WIFI):
                time.sleep(1.0)
                continue
            try:
                with open(WMT_WIFI, "wt") as f:
                    f.write("1")

                print("launcher: WiFi enabled")
                return
            except Exception as e:
                print("WARNING: Failed to enable WiFi:", e)
                traceback.print_exception(e)
                time.sleep(1.0)

    def _handle_launcher_cmd(self, cmd: bytes):
        print(f"launcher: Handling command={cmd}")
        if cmd == WMT_COMMAND_SRH_ROM_PATCH:
            self._handle_srh_rom_patch()
        elif cmd == WMT_COMAMND_SRH_PATCH:
            self._handle_srh_patch()
        else:
            raise Exception(f"Unknown launcher command={cmd}")

    def _handle_srh_rom_patch(self):
        chip_id = do_ioctl(self.fd, WMT_IOCTL_GET_CHIP_INFO, WMT_CHIPINFO_GET_CHIPID)
        fwver = do_ioctl(self.fd, WMT_IOCTL_GET_CHIP_INFO, WMT_CHIPINFO_GET_FWVER)
        print(f"srh_rom_patch: chip_id={hex(chip_id)} fw_ver={hex(fwver)}")

        prefix = get_rom_patch_prefix(chip_id)
        suffix = get_patch_suffix(chip_id)
        patchglob = f"{prefix}_ram_*_{suffix}*"
        print(f"srh_rom_patch: Looking for patch using glob: {patchglob}")

        patches = patch.patchglob(patchglob)
        for p in patches:
            if "ram_bt" in p.filename:
                btver = patch.find_bluetooth_fw_ver(p.contents)
                print("srh_rom_patch: BT firmware version:", btver)
            else:
                print(
                    "srh_rom_patch: Patch build:", patch.get_patch_build_id(p.contents)
                )

            print(f"srh_rom_patch: Read patch file length: {len(p.contents)}")
            patchinfo = patch.get_patch_info(p.contents)
            patchver = patch.get_patch_fwver(p.contents)
            print(f"srh_rom_patch: patchinfo={patchinfo}")
            print(f"srh_rom_patch: patchver={patchver}")
            if patchver != fwver:
                raise Exception(
                    f"Patch version mismatch... expected {patchver} got {fwver}"
                )

            req = create_set_rom_patch_request(patchinfo, p.filename)
            err = do_ioctl(self.fd, WMT_IOCTL_SET_ROM_PATCH_INFO, req)
            if err != 0:
                raise Exception(
                    f"srh_rom_patch: WMT_IOCTL_SET_ROM_PATCH_INFO failed (err={err})"
                )

    def _handle_srh_patch(self):
        chip_id = do_ioctl(self.fd, WMT_IOCTL_GET_CHIP_INFO, WMT_CHIPINFO_GET_CHIPID)
        fwver = do_ioctl(self.fd, WMT_IOCTL_GET_CHIP_INFO, WMT_CHIPINFO_GET_FWVER)
        print(f"srh_patch: chip_id={hex(chip_id)} fw_ver={hex(fwver)}")

        prefix = f"{get_patch_prefix(chip_id)}_patch"
        suffix = get_patch_suffix(chip_id)

        patchglob = f"{prefix}*{suffix}*"
        print(f"srh_patch: Looking for patch using glob: {patchglob}")

        patch_count_set = False
        patches = patch.patchglob(patchglob)
        for p in patches:
            patchinfo = patch.get_patch_info(p.contents)[:4]
            patchver = patch.get_patch_fwver(p.contents)
            print(f"srh_patch: patchinfo={patchinfo}")
            print(f"srh_patch: patchver={patchver}")
            if patchver != fwver:
                raise Exception(
                    f"Patch version mismatch... expected {patchver} got {fwver}"
                )
            # The first globbed patch determines the amount of patches to come.
            # Presumably all of them would have a matching number here.
            if not patch_count_set:
                err = do_ioctl(self.fd, WMT_IOCTL_SET_PATCH_NUM, patchinfo[0] >> 4)
                if err != 0:
                    raise Exception(f"Failed to set patch count (err={err})")
                patch_count_set = True

            req = create_set_patch_request(patchinfo, p.filename)
            err = do_ioctl(self.fd, WMT_IOCTL_SET_PATCH_INFO, req)
            if err != 0:
                raise Exception(
                    f"srh_patch: WMT_IOCTL_SET_PATCH_INFO failed (err={err})"
                )


def do_launcher() -> int:
    launcher = Launcher()
    return launcher.run()
