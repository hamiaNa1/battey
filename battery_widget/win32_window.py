# -*- coding: utf-8 -*-
"""Win32 窗口：真透明 layered window、左键拖动、右键菜单。"""
import ctypes
import json
import os
import sys
import threading
import winreg
from ctypes import wintypes

from . import config
from PIL import Image, ImageDraw

# ---------- 常量 ----------
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x1
FILE_SHARE_WRITE = 0x2
OPEN_EXISTING = 3

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

WS_EX_LAYERED = 0x80000
WS_EX_TOOLWINDOW = 0x80
WS_EX_TOPMOST = 0x8
WS_POPUP = 0x80000000
ULW_ALPHA = 0x2
AC_SRC_ALPHA = 1
SW_SHOWNOACTIVATE = 4
SM_CXSCREEN = 0
SM_CYSCREEN = 1
WM_LBUTTONDOWN = 0x201
WM_MOUSEMOVE = 0x200
WM_LBUTTONUP = 0x202
WM_RBUTTONUP = 0x205
WM_LBUTTONUP = 0x202
WM_CONTEXTMENU = 0x007B
WM_DESTROY = 0x2
WM_APP = 0x8000
WM_TRAYICON = WM_APP + 1
MF_CHECKED = 0x8
MF_SEPARATOR = 0x800

NIM_ADD = 0x0
NIM_MODIFY = 0x1
NIM_DELETE = 0x2
NIM_SETVERSION = 0x4
NIF_MESSAGE = 0x1
NIF_ICON = 0x2
NIF_TIP = 0x4
NIF_STATE = 0x8
NIF_SHOWTIP = 0x80
NIS_HIDDEN = 0x1
NOTIFYICON_VERSION_4 = 4

k32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
shell32 = ctypes.windll.shell32


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class SIZE(ctypes.Structure):
    _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]


class MSG(ctypes.Structure):
    _fields_ = [("hwnd", wintypes.HWND), ("message", ctypes.c_uint),
                ("wParam", wintypes.WPARAM), ("lParam", wintypes.LPARAM),
                ("time", wintypes.DWORD), ("pt", POINT)]


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("style", ctypes.c_uint),
                ("lpfnWndProc", ctypes.c_void_p), ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int), ("hInstance", wintypes.HINSTANCE),
                ("hIcon", wintypes.HANDLE), ("hCursor", wintypes.HANDLE),
                ("hbrBackground", wintypes.HANDLE), ("lpszMenuName", wintypes.LPCWSTR),
                ("lpszClassName", wintypes.LPCWSTR), ("hIconSm", wintypes.HANDLE)]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", ctypes.c_long),
                ("biHeight", ctypes.c_long), ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", ctypes.c_long),
                ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD)]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [("BlendOp", ctypes.c_byte), ("BlendFlags", ctypes.c_byte),
                ("SourceConstantAlpha", ctypes.c_byte), ("AlphaFormat", ctypes.c_byte)]


class ICONINFO(ctypes.Structure):
    _fields_ = [("fIcon", wintypes.BOOL), ("xHotspot", wintypes.DWORD),
                ("yHotspot", wintypes.DWORD), ("hbmMask", wintypes.HBITMAP),
                ("hbmColor", wintypes.HBITMAP)]


class GUID(ctypes.Structure):
    _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD), ("Data4", ctypes.c_ubyte * 8)]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("hWnd", wintypes.HWND),
                ("uID", wintypes.UINT), ("uFlags", wintypes.UINT),
                ("uCallbackMessage", wintypes.UINT), ("hIcon", wintypes.HICON),
                ("szTip", ctypes.c_wchar * 128), ("dwState", wintypes.DWORD),
                ("dwStateMask", wintypes.DWORD), ("szInfo", ctypes.c_wchar * 256),
                ("uTimeoutOrVersion", wintypes.UINT), ("szInfoTitle", ctypes.c_wchar * 64),
                ("dwInfoFlags", wintypes.DWORD), ("guidItem", GUID),
                ("hBalloonIcon", wintypes.HICON)]


# ---------- Win32 签名 ----------
user32.UpdateLayeredWindow.argtypes = [wintypes.HWND, wintypes.HDC, ctypes.POINTER(POINT),
                                       ctypes.POINTER(SIZE), wintypes.HDC, ctypes.POINTER(POINT),
                                       wintypes.DWORD, ctypes.POINTER(BLENDFUNCTION), wintypes.DWORD]
user32.UpdateLayeredWindow.restype = wintypes.BOOL
user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
                                   wintypes.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_int, wintypes.HWND, wintypes.HMENU,
                                   wintypes.HINSTANCE, wintypes.LPVOID]
user32.CreateWindowExW.restype = wintypes.HWND
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetWindowRect.restype = wintypes.BOOL
user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
user32.GetCursorPos.restype = wintypes.BOOL
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, wintypes.UINT]
user32.SetWindowPos.restype = wintypes.BOOL
user32.GetMessageW.argtypes = [ctypes.POINTER(MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = wintypes.BOOL
user32.RegisterClassExW.argtypes = [ctypes.POINTER(WNDCLASSEXW)]
user32.RegisterClassExW.restype = wintypes.ATOM
user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = ctypes.c_long
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL
user32.GetDC.argtypes = [wintypes.HWND]
user32.GetDC.restype = wintypes.HDC
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
user32.ReleaseDC.restype = ctypes.c_int
user32.SetCapture.argtypes = [wintypes.HWND]
user32.ReleaseCapture.argtypes = []
user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
user32.PostQuitMessage.argtypes = [ctypes.c_int]
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.GetSystemMetrics.argtypes = [ctypes.c_int]
user32.GetSystemMetrics.restype = ctypes.c_int
user32.LoadCursorW.argtypes = [wintypes.HINSTANCE, ctypes.c_void_p]
user32.LoadCursorW.restype = wintypes.HANDLE
user32.CreateIconIndirect.argtypes = [ctypes.POINTER(ICONINFO)]
user32.CreateIconIndirect.restype = wintypes.HICON
user32.DestroyIcon.argtypes = [wintypes.HICON]
user32.DestroyIcon.restype = wintypes.BOOL
user32.RegisterWindowMessageW.argtypes = [wintypes.LPCWSTR]
user32.RegisterWindowMessageW.restype = wintypes.UINT
user32.CreatePopupMenu.restype = wintypes.HMENU
user32.AppendMenuW.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes.c_size_t, wintypes.LPCWSTR]
user32.AppendMenuW.restype = wintypes.BOOL
user32.TrackPopupMenu.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes.c_int, ctypes.c_int,
                                  ctypes.c_int, wintypes.HWND, ctypes.c_void_p]
user32.TrackPopupMenu.restype = ctypes.c_int
user32.DestroyMenu.argtypes = [wintypes.HMENU]
user32.DestroyMenu.restype = wintypes.BOOL
gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.CreateDIBSection.argtypes = [wintypes.HDC, ctypes.POINTER(BITMAPINFO), wintypes.UINT,
                                   ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE, wintypes.DWORD]
gdi32.CreateDIBSection.restype = wintypes.HBITMAP
gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
gdi32.SelectObject.restype = wintypes.HGDIOBJ
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteDC.argtypes = [wintypes.HDC]
gdi32.CreateBitmap.argtypes = [ctypes.c_int, ctypes.c_int, wintypes.UINT, wintypes.UINT, ctypes.c_void_p]
gdi32.CreateBitmap.restype = wintypes.HBITMAP
shell32.Shell_NotifyIconW.argtypes = [wintypes.DWORD, ctypes.POINTER(NOTIFYICONDATAW)]
shell32.Shell_NotifyIconW.restype = wintypes.BOOL

WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_long, wintypes.HWND, ctypes.c_uint,
                            wintypes.WPARAM, wintypes.LPARAM)


def tray_tooltip(mouse, headset):
    """返回系统托盘悬停文本；仅展示当前支持的两个设备。"""
    def line(name, state):
        if not state.known:
            return f"{name}: 未连接"
        suffix = "（充电中）" if state.charging else ""
        return f"{name}: {state.level}%{suffix}"
    return "\n".join((line("鼠标", mouse), line("耳机", headset), "左键刷新 · 右键菜单"))


def tray_icon_image(mouse, headset):
    """生成 64px 双电池托盘图标，Windows 会按 DPI 缩放。"""
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    def battery(x, state):
        color = (80, 220, 130, 255) if state.known else (120, 126, 142, 255)
        if state.known and state.level <= 20:
            color = (245, 90, 80, 255)
        elif state.charging:
            color = (50, 205, 235, 255)
        draw.rounded_rectangle((x, 12, x + 20, 52), radius=4, outline=color, width=3)
        draw.rounded_rectangle((x + 6, 7, x + 14, 11), radius=2, fill=color)
        if state.known:
            height = max(3, int(33 * min(100, max(0, state.level)) / 100))
            draw.rounded_rectangle((x + 4, 48 - height, x + 16, 48), radius=2, fill=color)
        else:
            draw.line((x + 6, 32, x + 14, 32), fill=color, width=3)

    battery(6, mouse)
    battery(38, headset)
    return image


# ---------- 开机自启 ----------
def autostart_command():
    if getattr(sys, "frozen", False):
        return '"%s"' % sys.executable
    exe = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(exe):
        exe = sys.executable
    return '"%s" "%s"' % (exe, os.path.abspath(__file__))


def autostart_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            winreg.QueryValueEx(k, config.APP_NAME)
            return True
    except OSError:
        return False


def set_autostart(enable):
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
        if enable:
            winreg.SetValueEx(k, config.APP_NAME, 0, winreg.REG_SZ, autostart_command())
        else:
            try:
                winreg.DeleteValue(k, config.APP_NAME)
            except OSError:
                pass


class BatteryWindow:
    """无窗口的系统托盘电量组件。"""

    def __init__(self, cfg, manager):
        self.cfg = cfg
        self.manager = manager
        self.hwnd = None
        self._dragging = False
        self._dx = 0
        self._dy = 0
        self.refresh_event = threading.Event()
        self._tray_icon = None
        self._tray_added = False
        self._taskbar_created = user32.RegisterWindowMessageW("TaskbarCreated")
        self._proc_ref = WNDPROC(self._wnd_proc)
        self._build_window()
        self._add_tray_icon()

    # ---------- 窗口创建 ----------
    def _build_window(self):
        try:
            user32.SetProcessDPIAware()
        except Exception:
            pass
        hInstance = k32.GetModuleHandleW(None)
        wc = WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wc.lpfnWndProc = ctypes.cast(self._proc_ref, ctypes.c_void_p)
        wc.hInstance = hInstance
        wc.hCursor = user32.LoadCursorW(None, 32512)
        wc.lpszClassName = "DeviceBatteryWnd"
        user32.RegisterClassExW(ctypes.byref(wc))

        x, y = self._load_pos()
        w, h = self._size()
        self.hwnd = user32.CreateWindowExW(
            WS_EX_LAYERED | WS_EX_TOOLWINDOW | WS_EX_TOPMOST, "DeviceBatteryWnd", "",
            WS_POPUP, x, y, w, h, 0, 0, hInstance, 0)
        if not self.hwnd:
            raise RuntimeError("创建窗口失败")

    def _notify_data(self, flags):
        data = NOTIFYICONDATAW()
        data.cbSize = ctypes.sizeof(data)
        data.hWnd = self.hwnd
        data.uID = 1
        data.uFlags = flags
        data.uCallbackMessage = WM_TRAYICON
        data.hIcon = self._tray_icon
        data.szTip = tray_tooltip(self.manager.mouse, self.manager.headset)
        return data

    def _icon_from_image(self, image):
        w, h = image.size
        rgba = image.tobytes("raw", "BGRA")
        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = w
        bmi.bmiHeader.biHeight = -h
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = 0
        bits = ctypes.c_void_p()
        color = gdi32.CreateDIBSection(0, ctypes.byref(bmi), 0, ctypes.byref(bits), 0, 0)
        if not color:
            return None
        mask = gdi32.CreateBitmap(w, h, 1, 1, None)
        try:
            ctypes.memmove(bits, rgba, len(rgba))
            info = ICONINFO(True, 0, 0, mask, color)
            return user32.CreateIconIndirect(ctypes.byref(info))
        finally:
            gdi32.DeleteObject(color)
            gdi32.DeleteObject(mask)

    def _add_tray_icon(self):
        if not self._tray_icon:
            self._tray_icon = self._icon_from_image(tray_icon_image(self.manager.mouse, self.manager.headset))
        if not self._tray_icon:
            return
        data = self._notify_data(NIF_MESSAGE | NIF_ICON | NIF_TIP | NIF_SHOWTIP | NIF_STATE)
        # 请求显示；Windows 仍由用户的托盘可见性设置决定最终位置。
        data.dwStateMask = NIS_HIDDEN
        if shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(data)):
            self._tray_added = True
            data.uTimeoutOrVersion = NOTIFYICON_VERSION_4
            shell32.Shell_NotifyIconW(NIM_SETVERSION, ctypes.byref(data))

    def _update_tray_icon(self):
        icon = self._icon_from_image(tray_icon_image(self.manager.mouse, self.manager.headset))
        if not icon:
            return
        old_icon = self._tray_icon
        self._tray_icon = icon
        data = self._notify_data(NIF_ICON | NIF_TIP | NIF_SHOWTIP)
        if not self._tray_added or not shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(data)):
            self._tray_added = False
            self._add_tray_icon()
        if old_icon:
            user32.DestroyIcon(old_icon)

    def _remove_tray_icon(self):
        if self._tray_added:
            data = self._notify_data(0)
            shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(data))
            self._tray_added = False
        if self._tray_icon:
            user32.DestroyIcon(self._tray_icon)
            self._tray_icon = None

    def _size(self):
        from .render import SIZES
        s = SIZES.get(self.cfg.get("size", "normal"), SIZES["normal"])
        return s["W"], s["H"]

    def _load_pos(self):
        p = self.cfg.get("pos")
        if p and isinstance(p, dict):
            try:
                x, y = int(p.get("x")), int(p.get("y"))
                sw = user32.GetSystemMetrics(SM_CXSCREEN)
                sh = user32.GetSystemMetrics(SM_CYSCREEN)
                w, h = self._size()
                return max(0, min(x, sw - w)), max(0, min(y, sh - h))
            except Exception:
                pass
        sw = user32.GetSystemMetrics(SM_CXSCREEN)
        sh = user32.GetSystemMetrics(SM_CYSCREEN)
        w, h = self._size()
        return sw - w - 24, 24

    def _save_pos(self):
        rect = wintypes.RECT()
        user32.GetWindowRect(self.hwnd, ctypes.byref(rect))
        self.cfg["pos"] = {"x": rect.left, "y": rect.top}
        config.save_config(self.cfg)

    # ---------- 窗口过程 ----------
    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == self._taskbar_created:
            self._tray_added = False
            self._add_tray_icon()
            return 0
        if msg == WM_TRAYICON:
            event = lparam & 0xFFFF
            if event in (WM_LBUTTONUP, WM_RBUTTONUP, WM_CONTEXTMENU):
                self._show_menu(hwnd)
            return 0
        if msg == WM_LBUTTONDOWN:
            pt = POINT()
            user32.GetCursorPos(ctypes.byref(pt))
            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            self._dx = pt.x - rect.left
            self._dy = pt.y - rect.top
            self._dragging = True
            user32.SetCapture(hwnd)
            return 0
        elif msg == WM_MOUSEMOVE and self._dragging:
            pt = POINT()
            user32.GetCursorPos(ctypes.byref(pt))
            user32.SetWindowPos(hwnd, None, pt.x - self._dx, pt.y - self._dy, 0, 0, 0x1 | 0x4)
            return 0
        elif msg == WM_LBUTTONUP:
            self._dragging = False
            user32.ReleaseCapture()
            self._save_pos()
            return 0
        elif msg == WM_RBUTTONUP:
            self._show_menu(hwnd)
            return 0
        elif msg == WM_DESTROY:
            self._remove_tray_icon()
            user32.PostQuitMessage(0)
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    # ---------- 右键菜单 ----------
    def _show_menu(self, hwnd):
        pt = POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        menu = user32.CreatePopupMenu()
        user32.AppendMenuW(menu, 0, 1, "立即刷新")
        flags = MF_CHECKED if autostart_enabled() else 0
        user32.AppendMenuW(menu, flags, 2, "开机自启")
        user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
        # 主题
        sub = user32.CreatePopupMenu()
        user32.AppendMenuW(sub, MF_CHECKED if self.cfg.get("theme") == "dark" else 0, 11, "深色")
        user32.AppendMenuW(sub, MF_CHECKED if self.cfg.get("theme") == "light" else 0, 12, "浅色")
        user32.AppendMenuW(menu, 0x10, sub, "主题")
        # 尺寸
        sub2 = user32.CreatePopupMenu()
        sizes = [("compact", "紧凑"), ("normal", "标准"), ("large", "大号")]
        for i, (key, label) in enumerate(sizes):
            user32.AppendMenuW(sub2, MF_CHECKED if self.cfg.get("size") == key else 0, 20 + i, label)
        user32.AppendMenuW(menu, 0x10, sub2, "尺寸")
        user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
        user32.AppendMenuW(menu, 0, 3, "退出")
        cmd = user32.TrackPopupMenu(menu, 0x102, pt.x, pt.y, 0, hwnd, None)
        user32.DestroyMenu(menu)
        if cmd == 1:
            self.refresh_event.set()
        elif cmd == 2:
            set_autostart(not autostart_enabled())
        elif cmd == 3:
            user32.PostMessageW(hwnd, WM_DESTROY, 0, 0)
        elif cmd in (11, 12):
            self.cfg["theme"] = "dark" if cmd == 11 else "light"
            config.save_config(self.cfg)
            self._apply_size()
            self.update()
        elif cmd in (20, 21, 22):
            self.cfg["size"] = sizes[cmd - 20][0]
            config.save_config(self.cfg)
            self._apply_size()
            self.update()

    def _apply_size(self):
        """窗口尺寸变化后重建窗口（简单起见：调整窗口大小并重绘）。"""
        w, h = self._size()
        # 先把窗口位置/尺寸定好，再重绘（update 用新尺寸）
        rect = wintypes.RECT()
        user32.GetWindowRect(self.hwnd, ctypes.byref(rect))
        user32.SetWindowPos(self.hwnd, None, rect.left, rect.top, w, h, 0x4)

    # ---------- 渲染 ----------
    def update(self):
        self._update_tray_icon()

    def _present(self, pil_img):
        w, h = pil_img.size
        rgba = pil_img.tobytes("raw", "BGRA")
        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = w
        bmi.bmiHeader.biHeight = -h
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = 0
        screen_dc = user32.GetDC(0)
        mem_dc = gdi32.CreateCompatibleDC(screen_dc)
        pvbits = ctypes.c_void_p()
        hbmp = gdi32.CreateDIBSection(screen_dc, ctypes.byref(bmi), 0, ctypes.byref(pvbits), 0, 0)
        ctypes.memmove(pvbits, rgba, len(rgba))
        old = gdi32.SelectObject(mem_dc, hbmp)
        blend = BLENDFUNCTION()
        blend.BlendOp = 0
        blend.SourceConstantAlpha = 255
        blend.AlphaFormat = AC_SRC_ALPHA
        rect = wintypes.RECT()
        user32.GetWindowRect(self.hwnd, ctypes.byref(rect))
        pos = POINT(rect.left, rect.top)
        size = SIZE(w, h)
        src = POINT(0, 0)
        user32.UpdateLayeredWindow(self.hwnd, screen_dc, ctypes.byref(pos), ctypes.byref(size),
                                   mem_dc, ctypes.byref(src), 0, ctypes.byref(blend), ULW_ALPHA)
        gdi32.SelectObject(mem_dc, old)
        gdi32.DeleteObject(hbmp)
        gdi32.DeleteDC(mem_dc)
        user32.ReleaseDC(0, screen_dc)

    # ---------- 消息循环 ----------
    def run(self):
        self.manager.refresh()
        self.update()
        threading.Thread(target=self._refresh_loop, daemon=True).start()
        msg = MSG()
        while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def _refresh_loop(self):
        while True:
            try:
                self.manager.refresh()
                self.update()
            except Exception:
                pass
            missing = self.manager.missing
            interval = self.cfg.get("refresh_fast", 5) if missing else self.cfg.get("refresh_normal", 30)
            self.refresh_event.wait(interval)
            self.refresh_event.clear()
