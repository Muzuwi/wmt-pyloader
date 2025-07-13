import os
import sys
import dataclasses
import glob
import dataclasses
import os

PATCH_LOOKUP_DIRECTORY = "/lib/firmware/"


@dataclasses.dataclass
class Patch:
    # Patch file contents.
    contents: bytes
    # Full path to the patch file.
    path: str
    # Patch file name, used for ioctl's. This should be enough for
    # request_firmware to find the patch on its own.
    filename: str


def patchglob(pattern: str) -> list[Patch]:
    """Find patches with the specified glob-style pattern in the predefined
    firmware directories.

    This will throw an exception if no patch was found.
    """
    files = glob.glob(pattern, root_dir=PATCH_LOOKUP_DIRECTORY)
    if len(files) == 0:
        raise Exception(f"Failed to find patch with glob {pattern}")

    patches = []
    for filename in files:
        abspath = os.path.join(PATCH_LOOKUP_DIRECTORY, filename)
        with open(abspath, "rb") as f:
            filebytes = f.read()
        patches.append(Patch(filebytes, abspath, filename))

    return patches


def find_bluetooth_fw_ver(patchbytes: bytes):
    """Attempts to find the Bluetooth firmware version string inside a given
    patch file.
    """

    try:
        babeface_offset = patchbytes.index(b"BABEFACE")
    except:
        babeface_offset = None
    if babeface_offset is None:
        raise Exception("Could not find build info start magic")

    try:
        deadbabe_offset = patchbytes.index(b"DEADBEEF", babeface_offset)
    except:
        deadbabe_offset = None
    if deadbabe_offset is None:
        raise Exception("Could not find build info end magic")

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
    try:
        hex10offset = foundbytes.index(b"\x0A")
    except:
        hex10offset = None
    if hex10offset is None:
        raise Exception("Could not find firmware string 0xA terminator")

    return foundbytes[:hex10offset].decode()


def get_patch_info(patchbytes: bytes) -> bytes:
    """Get the patch information block.

    This seems to be common across patches (for patch_mcu_*, the patchinfo block
    is 4 bytes instead though).
    """
    # return struct.unpack("<Q", patchbytes[0x18 : (0x18 + 8)])[0]
    patchinfo = patchbytes[0x18 : (0x18 + 8)]
    if patchinfo[0] != 0x11:
        raise Exception(
            "patchinfo[0] is not 0x11, this might not be a valid patch file"
        )
    return patchinfo


def get_patch_fwver(patchbytes: bytes) -> int:
    """Get the patch fwver.

    This is checked against the FW_VER of the currently running combo chip to
    determine if the patch is compatible (?).
    """
    # get_patch_info call just for the validity check
    _ = get_patch_info(patchbytes)
    return patchbytes[0x16 + 0] << 8 | patchbytes[0x16 + 1]


def get_patch_build_id(patchbytes: bytes) -> str:
    """Get the patch build identifier.

    First 16 bytes of the patch files contain an ASCII identifier.
    """
    return patchbytes[0:0x10].decode()


if __name__ == "__main__":
    path = sys.argv[1]
    with open(path, "rb") as f:
        patchbytes = f.read()

    print(f"Patch file: {path}")
    print(f"Patch fwver: {hex(get_patch_fwver(patchbytes))}")
    print(f"Patch info: {get_patch_info(patchbytes)}")
    print(f"Patch build ID: {get_patch_build_id(patchbytes)}")
    if "ram_bt" in path:
        print(f"BT firmware version: {find_bluetooth_fw_ver(patchbytes)}")
