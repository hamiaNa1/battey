# DeviceBattery

Windows 2.4G 无线设备电量托盘组件。当前版本为鼠标和耳机分别显示一个常驻托盘图标，图标内直接显示电量，悬停可查看精确状态。

> 2.4G 接收器没有跨品牌统一的电量协议。本项目目前只支持下列两个已适配设备，不能自动读取任意品牌设备。

## 已支持设备

- Lunafury TYPE33 鼠标：VID `0x373E`，PID `0x0054` / `0x0084`
- SteelSeries Arctis Nova 5 耳机：VID `0x1038`，PID `0x2232`

## 功能

- 两个独立的 Windows 托盘图标，分别代表鼠标和耳机
- 图标内显示电量数字，悬停显示百分比、充电与连接状态
- 透明背景、冰蓝线框和薄荷绿数字，适配 TranslucentTB
- 在线时每 30 秒刷新；设备缺失时每 5 秒重试
- 右键菜单支持立即刷新、开机自启和退出
- 连续读取失败时使用短期缓存，减少设备休眠造成的闪烁

## 运行

需要 Windows 10/11 和 Python 3.10+：

```powershell
python -m pip install -r requirements.txt
python run.py
```

## 打包

```powershell
python -m PyInstaller --noconfirm --onefile --noconsole --name DeviceBattery --hidden-import hid --hidden-import pystray._win32 run.py
```

## 分支

- `main`：当前推荐的现代双图标版本
- `baseline-current`：初始双图标方案
- `experiment/dual-battery-tray`：单一双电量槽图标试验
- `experiment/modern-dual-icons`：适配透明任务栏的现代双图标方案

## 设备协议

### Lunafury TYPE33

- HID 接口：usage page `0xFFFF`，usage `0x0`
- Feature report 为 65 字节
- 请求：`[0]=report_id, [3]=2, [4]=2, [6]=0x83`
- 响应：`[7]` 为充电状态，`[8]` 为电量百分比

### SteelSeries Arctis Nova 5

- HID 接口：usage page `0xFFC0`，usage `1`
- 请求 output report：`[0]=0, [1]=0xB0`
- 响应：`[1]==0x02` 表示离线，`[3]` 为电量百分比，`[4]==1` 表示充电
- 协议参考：[HeadsetControl](https://github.com/Sapd/HeadsetControl)

## 许可证

[MIT](LICENSE)
