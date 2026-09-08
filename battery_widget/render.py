# -*- coding: utf-8 -*-
"""UI 渲染：纯 PIL 逐像素绘制，多尺寸、深浅双主题、带电量环。"""
import os

from PIL import Image, ImageDraw, ImageFont

# ---------- 尺寸表（宽, 高, 圆角, 间距, 圆点直径, 名称字号, 数字字号） ----------
SIZES = {
    "compact": dict(W=230, H=44, radius=12, pad=14, dot=8, name=12, num=15, gap=8, ring=10),
    "normal":  dict(W=280, H=56, radius=15, pad=16, dot=12, name=14, num=18, gap=12, ring=14),
    "large":   dict(W=340, H=70, radius=18, pad=20, dot=15, name=16, num=22, gap=15, ring=18),
}

THEMES = {
    "dark": dict(
        card=(24, 24, 36),
        name=(196, 198, 212),
        num=(255, 255, 255),
        separator=(255, 255, 255),
        off=(110, 112, 128),
        ok=(88, 224, 136),
        warn=(255, 170, 60),
        low=(255, 90, 90),
        charge=(0, 224, 216),
        ring_track=(255, 255, 255),
    ),
    "light": dict(
        card=(245, 246, 250),
        name=(90, 92, 110),
        num=(30, 30, 40),
        separator=(0, 0, 0),
        off=(150, 152, 168),
        ok=(34, 160, 80),
        warn=(230, 140, 20),
        low=(225, 60, 60),
        charge=(0, 160, 170),
        ring_track=(0, 0, 0),
    ),
}

_FONTS_DIR = r"C:\Windows\Fonts"
_FONT_CACHE = {}


def _font(size, weight="regular"):
    key = (size, weight)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    candidates = {
        "regular": ["msyh.ttc", "msyh.ttf", "simhei.ttf", "segoeui.ttf"],
        "light": ["msyhl.ttc", "msyh.ttc", "simhei.ttf"],
        "bold": ["msyhbd.ttc", "msyh.ttc", "simhei.ttf"],
    }[weight]
    f = None
    for name in candidates:
        p = os.path.join(_FONTS_DIR, name)
        try:
            f = ImageFont.truetype(p, size)
            break
        except Exception:
            try:
                f = ImageFont.truetype(name, size)
                break
            except Exception:
                continue
    if f is None:
        f = ImageFont.load_default()
    _FONT_CACHE[key] = f
    return f


def status_color(theme, level, charging):
    if level is None:
        return theme["off"]
    if charging:
        return theme["charge"]
    if level <= 20:
        return theme["low"]
    if level <= 50:
        return theme["warn"]
    return theme["ok"]


def _draw_ring(d, cx, cy, r, pct, color, track, width=3):
    """电量圆环。pct None 时不画环只画小点。"""
    if pct is None:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
        return
    bbox = [cx - r, cy - r, cx + r, cy + r]
    d.ellipse(bbox, outline=track + (60,), width=width)
    d.arc(bbox, start=90, end=90 - 360 * pct / 100.0, fill=color, width=width)
    # 中心小点（充电时亮色）
    d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=color)


def build_card(cfg, mouse, headset):
    """cfg: 配置 dict；mouse/headset: BatteryState。返回 RGBA PIL Image。"""
    theme = THEMES.get(cfg.get("theme", "dark"), THEMES["dark"])
    s = SIZES.get(cfg.get("size", "normal"), SIZES["normal"])
    W, H = s["W"], s["H"]
    opacity = cfg.get("opacity", 0.95)

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 卡片底（带整体透明度）
    card_alpha = int(60 * opacity) if cfg.get("theme", "dark") == "dark" else int(210 * opacity)
    d.rounded_rectangle([2, 2, W - 2, H - 2], radius=s["radius"], fill=theme["card"] + (card_alpha,))

    def block(x, name, state, show):
        """画一个设备块。x 为块左侧。返回 (占用宽度, 居中Y)。"""
        if not show:
            return 0, H // 2
        cy = H // 2
        c = status_color(theme, state.level, state.charging)
        ring_r = s["ring"] // 2
        if state.known and s["ring"] > 0:
            _draw_ring(d, x + ring_r, cy, ring_r, state.level, c + (255,), theme["ring_track"])
        else:
            d.ellipse([x, cy - 4, x + 8, cy + 4], fill=theme["off"] + (255,))
        # 名称
        name_font = _font(s["name"], "light")
        d.text((x + ring_r * 2 + s["gap"], cy - (s["num"] + 4) // 2 + 2 if not cfg.get("percent_on_top", True) else cy + 6),
               name, font=name_font, fill=theme["name"] + (255,), anchor="lm")
        # 数值
        if state.known:
            txt = f"{state.level}%"
            if state.charging:
                txt += " ⚡"
            num_font = _font(s["num"], "bold")
            y = cy - 6 if cfg.get("percent_on_top", True) else cy + 6
            d.text((x + ring_r * 2 + s["gap"], y), txt, font=num_font, fill=theme["num"] + (255,), anchor="lm")
        else:
            num_font = _font(s["num"], "bold")
            d.text((x + ring_r * 2 + s["gap"], cy), "--", font=num_font, fill=theme["off"] + (255,), anchor="lm")
        return ring_r * 2 + s["gap"] + max(s["name"] * 4, s["num"] * 3), cy

    # 布局：两个块按实际宽度排布，分隔线在中间
    w1, cy1 = block(s["pad"], "鼠标", mouse, cfg.get("show_mouse", True))
    # 第二块起点：分隔线位置 = pad + w1 + 分隔线半宽
    sep_x = s["pad"] + w1 + 8
    d.line([(sep_x, 12), (sep_x, H - 12)], fill=theme["separator"] + (30,), width=1)
    w2, cy2 = block(sep_x + 8, "耳机", headset, cfg.get("show_headset", True))

    return img
