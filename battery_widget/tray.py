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
ACTIVE_COLOR = (132, 218, 255, 240)
NUMBER_COLOR = (126, 255, 186, 255)
PANEL_COLOR = (8, 24, 40, 145)
DIGITS = {
    "0": ("111", "101", "101", "101", "111"),
    "1": ("010", "110", "010", "010", "111"),
    "2": ("111", "001", "111", "100", "111"),
    "3": ("111", "001", "111", "001", "111"),
    "4": ("101", "101", "111", "001", "001"),
    "5": ("111", "100", "111", "001", "111"),
    "6": ("111", "100", "111", "101", "111"),
    "7": ("111", "001", "010", "010", "010"),
    "8": ("111", "101", "111", "101", "111"),
    "9": ("111", "101", "111", "001", "111"),
    "-": ("000", "000", "111", "000", "000"),
}


def device_tooltip(name, state):
    if not state.known:
        status = "未连接"
    else:
        status = f"{state.level}%{'（充电中）' if state.charging else ''}"
    return f"DeviceBattery · {name}: {status}\n左键刷新 · 右键菜单"


def device_color(state, active):
    return active if state.known else (130, 138, 150, 230)


def draw_charge_mark(draw, state):
    if state.known and state.charging:
        draw.polygon(((14, 0), (11, 4), (13, 4), (11, 7), (15, 3), (13, 3)), fill=NUMBER_COLOR)


def draw_percent(draw, state, center, fill):
    label = str(min(100, max(0, state.level))) if state.known else "--"
    width = len(label) * 3 + len(label) - 1
    left = int(center[0] - width / 2)
    top = int(center[1] - 2.5)
    for index, digit in enumerate(label):
        offset = left + index * 4
        for row, bits in enumerate(DIGITS[digit]):
            for column, bit in enumerate(bits):
                if bit == "1":
                    draw.point((offset + column, top + row), fill=fill)


def mouse_icon_image(state):
    """在原生 16px 网格上绘制镂空鼠标和清晰百分比。"""
    image = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    color = device_color(state, ACTIVE_COLOR)
    draw.rounded_rectangle((3, 0, 13, 15), radius=5, outline=color, width=1)
    draw.line((8, 1, 8, 5), fill=color, width=1)
    draw.rectangle((7, 2, 8, 4), fill=color)
    draw.rounded_rectangle((3, 7, 13, 14), radius=2, fill=PANEL_COLOR)
    draw_percent(draw, state, (8, 11), NUMBER_COLOR if state.known else color)
    draw_charge_mark(draw, state)
    return image.resize((64, 64), Image.Resampling.NEAREST)


def headset_icon_image(state):
    """在原生 16px 网格上绘制连续耳机和清晰百分比。"""
    image = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    color = device_color(state, ACTIVE_COLOR)
    draw.arc((1, 0, 15, 14), 180, 360, fill=color, width=2)
    draw.rounded_rectangle((1, 7, 5, 15), radius=2, outline=color, width=1)
    draw.rounded_rectangle((11, 7, 15, 15), radius=2, outline=color, width=1)
    draw.rounded_rectangle((2, 8, 14, 15), radius=2, fill=PANEL_COLOR)
    draw_percent(draw, state, (8, 12), NUMBER_COLOR if state.known else color)
    draw_charge_mark(draw, state)
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
    """显示独立的鼠标和耳机任务栏通知图标。"""

    def __init__(self, cfg, manager):
        self.cfg = cfg
        self.manager = manager
        self.refresh_event = threading.Event()
        self.stop_event = threading.Event()
        self.mouse_icon = pystray.Icon("DeviceBatteryMouse", mouse_icon_image(manager.mouse),
                                       device_tooltip("鼠标", manager.mouse), self._menu())
        self.headset_icon = pystray.Icon("DeviceBatteryHeadset", headset_icon_image(manager.headset),
                                         device_tooltip("耳机", manager.headset), self._menu())

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
        self.mouse_icon.update_menu()
        self.headset_icon.update_menu()

    def _quit(self, icon, item):
        self.stop_event.set()
        self.refresh_event.set()
        self.mouse_icon.stop()
        self.headset_icon.stop()

    def _refresh(self):
        self.manager.refresh()
        self.mouse_icon.icon = mouse_icon_image(self.manager.mouse)
        self.mouse_icon.title = device_tooltip("鼠标", self.manager.mouse)
        self.headset_icon.icon = headset_icon_image(self.manager.headset)
        self.headset_icon.title = device_tooltip("耳机", self.manager.headset)

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
        self.mouse_icon.visible = True
        self.headset_icon.run_detached(setup=lambda headset: setattr(headset, "visible", True))
        threading.Thread(target=self._refresh_loop, daemon=True).start()

    def run(self):
        self.mouse_icon.run(setup=self._setup)
