from subprocess import check_call
import loader
import launcher


class MT6765:
    """Generic MT6765 target for Helio family SoC's."""

    COMPATIBLE_STRINGS = ["mediatek,MT6765"]

    def __init__(self):
        pass

    def boot(self):
        # First, wmt_drv must be loaded for wmtDetect to appear.
        check_call(["modprobe", "wmt_drv"])
        # Loader step.
        loader.do_loader()
        # Further modules MUST be loaded after loader finishes! This is a strict
        # requirement! As an example, the gen4m module relies on symbols
        # exported in other modules in its module_init function, so blindly
        # loading all of them at once leads to unexplainable failures.
        check_call(["modprobe", "wmt_chrdev_wifi"])
        check_call(["modprobe", "wlan_drv_gen4m"])
        # Launcher step - this will block.
        launcher.do_launcher()
