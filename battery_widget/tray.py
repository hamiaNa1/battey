# -*- coding: utf-8 -*-
"""Windows 系统托盘电量组件。"""
import os
import sys
import threading
import winreg

from PIL import Image, ImageDraw
import pystray

from . import config

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
FRAME_COLOR = (55, 190, 255, 255)
FILL_COLOR = (90, 235, 255, 255)
UNKNOWN_COLOR = (130, 138, 150, 230)


def device_tooltip(name, state):
    if not state.known:
        status = "未连接"
    else:
        status = f"{state.level}%{'（充电中）' if state.charging else ''}"
    return f"{name}: {status}"


def tray_tooltip(mouse, headset):
    return "\n".join((
        "DeviceBattery",
        device_tooltip("鼠标", mouse),
        device_tooltip("耳机", headset),
        "左键刷新 · 右键菜单",
    ))


def _draw_level(draw, bounds, state, marker):
    """绘制一个电量槽；上方 marker 是设备类别的极简标识。"""
    left, top, right, bottom = bounds
    color = FRAME_COLOR if state.known else UNKNOWN_COLOR
    draw.rounded_rectangle(bounds, radius=1, outline=color, width=1)
    marker(draw, color, left, top)
    if not state.known:
        draw.line((left + 1, (top + bottom) // 2, right - 1, (top + bottom) // 2), fill=color, width=1)
        return
    height = max(1, round((bottom - top - 1) * min(100, max(0, state.level)) / 100))
    draw.rectangle((left + 1, bottom - height, right - 1, bottom - 1), fill=FILL_COLOR)


def _mouse_marker(draw, color, left, top):
    draw.rectangle((left + 2, top - 4, left + 3, top - 3), fill=color)
    draw.point((left + 2, top - 2), fill=color)


def _headset_marker(draw, color, left, top):
    draw.arc((left, top - 4, left + 5, top + 1), 180, 360, fill=color, width=1)


def dual_battery_icon_image(mouse, headset):
    """在原生 16px 网格绘制鼠标和耳机的双电量槽。"""
    image = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    _draw_level(draw, (1, 5, 6, 15), mouse, _mouse_marker)
    _draw_level(draw, (9, 5, 14, 15), headset, _headset_marker)
    return image.resize((64, 64), Image.Resampling.NEAREST)


def autostart_command():
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    executable = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(executable):
        executable = sys.executable
    return f'"{executable}" "{os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "run.py"))}"'


def autostart_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.QueryValueEx(key, config.APP_NAME)
            return True
    except OSError:
        return False


def set_autostart(enable):
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if enable:
            winreg.SetValueEx(key, config.APP_NAME, 0, winreg.REG_SZ, autostart_command())
        else:
            try:
                winreg.DeleteValue(key, config.APP_NAME)
            except OSError:
                pass


class BatteryTray:
    """显示鼠标和耳机电量的单一任务栏通知图标。"""

    def __init__(self, cfg, manager):
        self.cfg = cfg
        self.manager = manager
        self.refresh_event = threading.Event()
        self.stop_event = threading.Event()
        self.icon = pystray.Icon("DeviceBattery", dual_battery_icon_image(manager.mouse, manager.headset),
                                 tray_tooltip(manager.mouse, manager.headset), self._menu())

    def _menu(self):
        return pystray.Menu(
            pystray.MenuItem("立即刷新", self._refresh_now, default=True),
            pystray.MenuItem("开机自启", self._toggle_autostart,
                             checked=lambda item: autostart_enabled()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self._quit),
        )

    def _refresh_now(self, icon, item):
        self.refresh_event.set()

    def _toggle_autostart(self, icon, item):
        set_autostart(not autostart_enabled())
        self.icon.update_menu()

    def _quit(self, icon, item):
        self.stop_event.set()
        self.refresh_event.set()
        self.icon.stop()

    def _refresh(self):
        self.manager.refresh()
        self.icon.icon = dual_battery_icon_image(self.manager.mouse, self.manager.headset)
        self.icon.title = tray_tooltip(self.manager.mouse, self.manager.headset)

    def _refresh_loop(self):
        while not self.stop_event.is_set():
            try:
                self._refresh()
            except Exception:
                pass
            interval = self.cfg.get("refresh_fast", 5) if self.manager.missing else self.cfg.get("refresh_normal", 30)
            self.refresh_event.wait(interval)
            self.refresh_event.clear()

    def _setup(self, icon):
        self.icon.visible = True
        threading.Thread(target=self._refresh_loop, daemon=True).start()

    def run(self):
        self.icon.run(setup=self._setup)
