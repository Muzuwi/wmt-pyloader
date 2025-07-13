import os
import sys
import struct
import dataclasses


def get_bt_fw_ver(patchbytes: bytes) -> str:
    # I will not even attempt to understand what this is trying to do
    try:
        babeface_offset = patchbytes.index(b"BABEFACE")
    except:
        babeface_offset = None
    if babeface_offset is None:
        raise Exception("Could not find start of firmware string!")

    try:
        deadbabe_offset = patchbytes.index(b"DEADBEEF", babeface_offset)
    except:
        deadbabe_offset = None
    if deadbabe_offset is None:
        raise Exception("Could not find end of firmware string!")

    startpos = 0
    endpos = 0
    try:
        t_neptune_offset = patchbytes.index(b"t-neptune", babeface_offset)
    except:
        t_neptune_offset = None
    try:
        debug_offset = patchbytes[babeface_offset:].index(b"= debug")
    except:
        debug_offset = None
    if t_neptune_offset is None:
        if debug_offset is None:
            raise Exception("Invalid firmware version")
        startpos = 0
        endpos = 0xE
    else:
        startpos = t_neptune_offset
        endpos = deadbabe_offset

    foundbytes = patchbytes[startpos:endpos]
    print(f"srh_rom_patch: spos={startpos:x}, epos={endpos:x}, bytes={foundbytes}")

    try:
        hex10offset = foundbytes.index(b"\x0A")
    except:
        hex10offset = None
    if hex10offset is None:
        raise Exception("Could not find firmware string 0xA terminator")
    return foundbytes[:hex10offset].decode()


def get_wifi_fw_ver(patchbytes: bytes) -> str:
    return patchbytes[0:0x10].decode()


def get_patch_info(patchbytes: bytes) -> int:
    # return struct.unpack("<Q", patchbytes[0x18 : (0x18 + 8)])[0]
    patchinfo = patchbytes[0x18 : (0x18 + 8)]
    if patchinfo[0] != 0x11:
        raise Exception(
            "patchinfo[0] is not 0x11, this might not be a valid patch file"
        )
    return patchinfo


def get_patch_version(patchbytes: bytes) -> int:
    # get_patch_info call just for the validity check
    _ = get_patch_info(patchbytes)
    return patchbytes[0x16 + 0] << 8 | patchbytes[0x16 + 1]


if __name__ == "__main__":
    path = sys.argv[1]
    with open(path, "rb") as f:
        patchbytes = f.read()

    print(f"Patch file: {path}")
    print(f"Patch version: {hex(get_patch_version(patchbytes))}")
    print(f"Patch info: {get_patch_info(patchbytes)}")
    if "ram_bt" in path:
        print(f"BT firmware version: {get_bt_fw_ver(patchbytes)}")
    elif "ram_mcu" in path:
        print(f"WiFi firmware version: {get_wifi_fw_ver(patchbytes)}")
