# -*- coding: utf-8 -*-
"""设备电量读取：鼠标（Lunafury）+ 耳机（SteelSeries Nova 5）HID 协议。"""
import ctypes
import time
from ctypes import wintypes

import hid

MOUSE_VID = 0x373E
MOUSE_PIDS = [0x0054, 0x0084]
HEADSET_VID, HEADSET_PID = 0x1038, 0x2232

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x1
FILE_SHARE_WRITE = 0x2
OPEN_EXISTING = 3

k32 = ctypes.windll.kernel32
k32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                            ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
k32.CreateFileW.restype = wintypes.HANDLE
k32.CloseHandle.argtypes = [wintypes.HANDLE]
_hid = ctypes.windll.hid
_hid.HidD_SetFeature.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.ULONG]
_hid.HidD_SetFeature.restype = wintypes.BOOL
_hid.HidD_GetFeature.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.ULONG]
_hid.HidD_GetFeature.restype = wintypes.BOOL


def _mouse_try_once(pid):
    """Lunafury TYPE33 鼠标：feature report 65 字节协议。返回 (电量%, 是否充电) 或 None。"""
    path = None
    try:
        for d in hid.enumerate(MOUSE_VID, pid):
            if d.get("usage_page") == 0xFFFF and d.get("usage") == 0x0:
                path = d["path"]
                break
    except Exception:
        return None
    if not path:
        return None
    p = path.decode("utf-8", errors="replace") if isinstance(path, bytes) else str(path)
    h = k32.CreateFileW(p, GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE,
                        None, OPEN_EXISTING, 0, None)
    if h is None or h == wintypes.HANDLE(-1).value:
        return None
    try:
        sbuf = ctypes.create_string_buffer(65)
        ctypes.memset(sbuf, 0, 65)
        sbuf[0] = 0
        sbuf[3] = 2
        sbuf[4] = 2
        sbuf[6] = 131
        if not _hid.HidD_SetFeature(h, sbuf, 65):
            return None
        time.sleep(0.25)
        rbuf = ctypes.create_string_buffer(65)
        ctypes.memset(rbuf, 0, 65)
        if not _hid.HidD_GetFeature(h, rbuf, 65):
            return None
        b = bytes(rbuf.raw)
        if len(b) < 9 or b[6] != 131:
            return None
        return b[8], bool(b[7])
    finally:
        k32.CloseHandle(h)


def read_mouse_battery():
    for _ in range(3):
        for pid in MOUSE_PIDS:
            r = _mouse_try_once(pid)
            if r is not None:
                return r
        time.sleep(0.3)
    return None, None


def _headset_try_once():
    """SteelSeries Arctis Nova 5：output report 0xB0 查询，input report 应答。返回 (电量%, 充电, 在线) 或 None。"""
    path = None
    try:
        for d in hid.enumerate(HEADSET_VID, HEADSET_PID):
            if d.get("usage_page") == 0xFFC0 and d.get("usage") == 1:
                path = d["path"]
                break
    except Exception:
        return None
    if not path:
        return None
    try:
        dev = hid.device()
        dev.open_path(path)
        dev.set_nonblocking(True)
        try:
            dev.write(bytes([0, 0xB0]) + bytes(62))
            data = None
            for _ in range(25):
                try:
                    r = dev.read(128, timeout_ms=200)
                    if r:
                        data = bytes(r)
                        break
                except Exception:
                    pass
                time.sleep(0.04)
            if not data or len(data) < 5:
                return None
            if data[1] == 0x02:
                return None  # 离线
            return data[3], (data[4] == 0x01), True
        finally:
            dev.close()
    except Exception:
        return None


def read_headset_battery():
    for _ in range(3):
        r = _headset_try_once()
        if r is not None:
            return r
        time.sleep(0.3)
    return None, None, False


# ---------- 状态缓存（带失败计数，连续失败才清缓存，防闪断） ----------
class BatteryState:
    def __init__(self):
        self.level = None
        self.charging = False
        self.online = False
        self.fail_count = 0

    @property
    def known(self):
        return self.level is not None

    def update(self, level, charging, online=True):
        if level is not None:
            self.level = int(level)
            self.charging = bool(charging)
            self.online = bool(online)
            self.fail_count = 0
        else:
            self.fail_count += 1
            if self.fail_count > 6 or not online:
                self.level = None
                self.online = False


class DeviceManager:
    """统一管理所有设备的状态刷新。"""

    def __init__(self):
        self.mouse = BatteryState()
        self.headset = BatteryState()

    def refresh(self):
        mb, mc = read_mouse_battery()
        self.mouse.update(mb, mc)
        hb, hc, hp = read_headset_battery()
        self.headset.update(hb, hc, hp)

    @property
    def missing(self):
        return not self.mouse.known or not self.headset.known
