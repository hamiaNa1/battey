from battery_widget.devices import BatteryState
from battery_widget.tray import device_tooltip, headset_icon_image, mouse_icon_image


def test_tray_tooltip():
    mouse = BatteryState()
    headset = BatteryState()
    mouse.update(82, False)
    headset.update(64, True)
    assert "鼠标: 82%" in device_tooltip("鼠标", mouse)
    assert "耳机: 64%（充电中）" in device_tooltip("耳机", headset)
    assert mouse_icon_image(mouse).size == (64, 64)
    assert headset_icon_image(headset).size == (64, 64)


if __name__ == "__main__":
    test_tray_tooltip()
    print("tray tooltip check passed")
