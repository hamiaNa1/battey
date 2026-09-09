from battery_widget.devices import BatteryState
from battery_widget.tray import (
    ACTIVE_COLOR,
    CRITICAL_COLORS,
    OFFLINE_COLORS,
    THEMES,
    WARNING_COLORS,
    device_color,
    device_tooltip,
    headset_icon_image,
    mouse_icon_image,
)


def test_modern_tray_icons():
    mouse = BatteryState()
    headset = BatteryState()
    mouse.update(82, False)
    headset.update(64, True)
    mouse_icon = mouse_icon_image(mouse, mode="dark")
    headset_icon = headset_icon_image(headset, mode="dark")
    assert mouse_icon.size == headset_icon.size == (64, 64)
    assert ACTIVE_COLOR in set(mouse_icon.get_flattened_data())
    assert ACTIVE_COLOR in set(headset_icon.get_flattened_data())
    assert "鼠标: 82%" in device_tooltip("鼠标", mouse)
    assert "耳机: 64%（充电中）" in device_tooltip("耳机", headset)

    headset.update(None, None, online=False)
    assert "未连接" in device_tooltip("耳机", headset)
    assert OFFLINE_COLORS["dark"] in set(headset_icon_image(headset, mode="dark").get_flattened_data())

    mouse.update(15, False)
    assert device_color(mouse, "purple", "dark") == WARNING_COLORS["dark"]
    mouse.update(7, False)
    assert device_color(mouse, "purple", "light") == CRITICAL_COLORS["light"]

    mouse.update(53, False)
    for key, theme in THEMES.items():
        assert device_color(mouse, key, "dark") == theme[1]
        assert device_color(mouse, key, "light") == theme[2]
        assert mouse_icon_image(mouse, key, "dark").getbbox() is not None
        assert headset_icon_image(mouse, key, "light").getbbox() is not None


if __name__ == "__main__":
    test_modern_tray_icons()
    print("modern dual tray icons check passed")
