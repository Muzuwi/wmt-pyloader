# wmt_detect

The `wmt_drv` module exposes a character device at `/dev/wmtdetect`.
The following ioctl's are supported:
```c
#define WMT_DETECT_IOC_MAGIC            'w'
#define COMBO_IOCTL_GET_CHIP_ID       _IOR(WMT_DETECT_IOC_MAGIC, 0, int)
#define COMBO_IOCTL_SET_CHIP_ID       _IOW(WMT_DETECT_IOC_MAGIC, 1, int)
#define COMBO_IOCTL_EXT_CHIP_DETECT   _IOR(WMT_DETECT_IOC_MAGIC, 2, int)
#define COMBO_IOCTL_GET_SOC_CHIP_ID   _IOR(WMT_DETECT_IOC_MAGIC, 3, int)
#define COMBO_IOCTL_DO_MODULE_INIT    _IOR(WMT_DETECT_IOC_MAGIC, 4, int)
#define COMBO_IOCTL_MODULE_CLEANUP    _IOR(WMT_DETECT_IOC_MAGIC, 5, int)
#define COMBO_IOCTL_EXT_CHIP_PWR_ON   _IOR(WMT_DETECT_IOC_MAGIC, 6, int)
#define COMBO_IOCTL_EXT_CHIP_PWR_OFF  _IOR(WMT_DETECT_IOC_MAGIC, 7, int)
#define COMBO_IOCTL_DO_SDIO_AUDOK     _IOR(WMT_DETECT_IOC_MAGIC, 8, int)
#define COMBO_IOCTL_GET_ADIE_CHIP_ID  _IOR(WMT_DETECT_IOC_MAGIC, 9, int)
#define COMBO_IOCTL_CONNSYS_SOC_HW_INIT   _IOR(WMT_DETECT_IOC_MAGIC, 10, int)
```

## COMBO_IOCTL_GET_CHIP_ID

This returns the chip identifier by calling `mtk_wcn_wmt_chipid_query`.
Handled in `mtk_wcn_stub_alps.c`, which just fetches this from a global variable.

## COMBO_IOCTL_SET_CHIP_ID

Sets the chip identifier by calling `mtk_wcn_wmt_set_chipid`.
Handled in `mtk_wcn_stub_alps.c`, which just persists this in a global variable.


`mtk_wcn_stub_alps.c` seems to be a dispatcher of sorts.
Function callbacks are registered dynamically.

## Regex for matching output of all WMT-related drivers from dmesg

BT-MOD-INIT|BWG|FM-MOD-INIT|GPS|GPS2|GPS-MOD-INIT|hif_sdio|HIF-SDIO|ICS-FW|LNA_CTL|MTK-BT|MTK-WIFI|%s|SDIO-DETECT|STP|STP SDIO|STP-BTIF|STP-BTM|STPDbg|STP-PSM|UART|user-trx|WCN-MOD-INIT|WIFI-FW|wlan|WLAN-MOD-INIT|WMT-CMB-HW|WMT-CONF|WMT-CONSYS-HW|WMT-CORE|WMT-CTRL|WMT-DETECT|WMT-DEV|WMT-DFT|WMT-EXP|WMT-FUNC|WMT-IC|WMT-LIB|WMT-MOD-INIT|WMT-PLAT|cmb_stub|mtk_wcn_cmb_sdio|mtk_stp_btm