from battery_widget.devices import BatteryState, DeviceManager
from battery_widget.tray import BatteryTray, dual_battery_icon_image, tray_tooltip


def test_tray_component():
    mouse = BatteryState()
    headset = BatteryState()
    mouse.update(100, False)
    headset.update(25, True)
    icon = dual_battery_icon_image(mouse, headset)
    assert icon.size == (64, 64)
    assert "鼠标: 100%" in tray_tooltip(mouse, headset)
    assert "耳机: 25%（充电中）" in tray_tooltip(mouse, headset)
    assert icon.getpixel((12, 24))[:3] == (90, 235, 255)
    assert icon.getpixel((44, 24))[:3] != (90, 235, 255)
    assert icon.getpixel((44, 56))[:3] == (90, 235, 255)
    tray = BatteryTray({}, DeviceManager())
    assert hasattr(tray, "icon")
    assert not hasattr(tray, "mouse_icon")
    assert not hasattr(tray, "headset_icon")


if __name__ == "__main__":
    test_tray_component()
    print("dual tray component check passed")
