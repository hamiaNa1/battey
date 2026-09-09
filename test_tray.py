from battery_widget.devices import BatteryState
from battery_widget.tray import (
    ACTIVE_COLOR,
    NUMBER_COLOR,
    device_tooltip,
    headset_icon_image,
    mouse_icon_image,
)


def test_modern_tray_icons():
    mouse = BatteryState()
    headset = BatteryState()
    mouse.update(82, False)
    headset.update(64, True)
    mouse_icon = mouse_icon_image(mouse)
    headset_icon = headset_icon_image(headset)
    assert mouse_icon.size == headset_icon.size == (64, 64)
    assert ACTIVE_COLOR in set(mouse_icon.get_flattened_data())
    assert ACTIVE_COLOR in set(headset_icon.get_flattened_data())
    assert NUMBER_COLOR in set(mouse_icon.get_flattened_data())
    assert NUMBER_COLOR in set(headset_icon.get_flattened_data())
    assert "鼠标: 82%" in device_tooltip("鼠标", mouse)
    assert "耳机: 64%（充电中）" in device_tooltip("耳机", headset)

    headset.update(None, None, online=False)
    assert "未连接" in device_tooltip("耳机", headset)
    assert NUMBER_COLOR not in set(headset_icon_image(headset).get_flattened_data())


if __name__ == "__main__":
    test_modern_tray_icons()
    print("modern dual tray icons check passed")
