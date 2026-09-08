# -*- coding: utf-8 -*-
"""DeviceBattery 桌面电量组件入口。"""
from .config import load_config
from .devices import DeviceManager
from .tray import BatteryTray


def main():
    cfg = load_config()
    manager = DeviceManager()
    BatteryTray(cfg, manager).run()


if __name__ == "__main__":
    main()
