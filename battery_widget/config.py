# -*- coding: utf-8 -*-
"""配置管理：读取/写入 JSON 配置，支持打包与源码两种运行环境。"""
import json
import os
import sys

APP_NAME = "DeviceBattery"
APP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# ---------- 默认配置 ----------
DEFAULTS = {
    "pos": None,                 # {"x": int, "y": int}，None = 默认右上角
    "autostart": False,          # 开机自启
    "refresh_normal": 30,        # 全部在线时的刷新间隔（秒）
    "refresh_fast": 5,           # 有设备离线时的快速轮询间隔（秒）
    "opacity": 0.95,             # 整体不透明度 0.3 ~ 1.0
    "theme": "dark",             # "dark" | "light"
    "show_mouse": True,
    "show_headset": True,
    "percent_on_top": True,      # 百分比放在设备名上方（更现代）
    "size": "normal",            # "compact" | "normal" | "large"
}


def config_path():
    """配置路径：打包版放 exe 同目录 data/，源码版放项目 data/。"""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "data", "config.json")


def load_config():
    cfg = dict(DEFAULTS)
    p = config_path()
    try:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
    except Exception:
        pass
    # 兜底：非法值回退
    cfg["refresh_normal"] = max(5, int(cfg.get("refresh_normal", 30)))
    cfg["refresh_fast"] = max(2, int(cfg.get("refresh_fast", 5)))
    try:
        cfg["opacity"] = max(0.3, min(1.0, float(cfg.get("opacity", 0.95))))
    except Exception:
        cfg["opacity"] = 0.95
    return cfg


def save_config(cfg):
    try:
        os.makedirs(os.path.dirname(config_path()), exist_ok=True)
        with open(config_path(), "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
