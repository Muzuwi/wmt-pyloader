_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = 8
_IOC_SIZESHIFT = 16
_IOC_DIRSHIFT = 30
_IOC_WRITE = 1
_IOC_READ = 2


def ioc(dir: int, type: int, nr: int, size: str):
    actual_size = {
        "char*": 8,
        "int": 4,
        "unsigned int": 4,
    }[size]

    return (
        ((dir) << _IOC_DIRSHIFT)
        | ((type) << _IOC_TYPESHIFT)
        | ((nr) << _IOC_NRSHIFT)
        | ((actual_size) << _IOC_SIZESHIFT)
    )


def iow(type: int, nr: int, size: str):
    return ioc(_IOC_WRITE, type, nr, size)


def ior(type: int, nr: int, size: str):
    return ioc(_IOC_READ, type, nr, size)


def iowr(type: int, nr: int, size: str):
    return ioc(_IOC_READ | _IOC_WRITE, type, nr, size)


def do_ioctl(fd, ioctl: int, arg=0) -> int:
    import fcntl

    # Python is being a bit too clever and throws an exception based on the status code
    # The driver of course re-uses some values for it's own custom statuses.
    try:
        err = fcntl.ioctl(fd, ioctl, arg)
    except OSError as e:
        err = -e.errno
    if isinstance(err, bytes):
        print(f"wmt_pyloader: ioctl({hex(ioctl)}) bytes: {err}")
        return err
    print(f"wmt_pyloader: ioctl({hex(ioctl)}) returned err({hex(err)})")
    return err
