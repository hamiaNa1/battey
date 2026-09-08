# DeviceBattery 🍇

无线设备电量系统托盘组件 —— 实时显示鼠标 + 耳机电量。

## 功能

- 🖱️ **鼠标电量**（Lunafury TYPE33，HID feature report 协议）
- 🎧 **耳机电量**（SteelSeries Arctis Nova 5，output report 0xB0 协议）
- 🔋 **系统托盘**：双电池动态图标；悬停显示精确电量，左右键打开菜单
- 🔔 **动态刷新**：设备在线 30s 慢刷新，离线/开机 5s 快轮询，秒级恢复
- 🎨 **深浅双主题** + **三档尺寸**（紧凑/标准/大号）
- 🔘 **右键菜单**：立即刷新 / 开机自启 / 主题 / 尺寸 / 退出
- 📍 **位置记忆**：左键拖动，自动保存
- 💾 **配置持久化**：`data/config.json`

## 截图

（暂无）

## 快速开始

### 直接运行（打包版）
```powershell
# 把 exe 放到任意目录双击运行
E:\Tools\DeviceBattery.exe
```

### 源码运行
```bash
pip install -r requirements.txt
python run.py
```

## 配置

`data/config.json`（首次运行自动生成）：

| 字段 | 默认 | 说明 |
|------|------|------|
| `pos` | `null` | 窗口位置 `{x, y}` |
| `autostart` | `false` | 开机自启 |
| `refresh_normal` | `30` | 在线刷新间隔（秒） |
| `refresh_fast` | `5` | 离线快轮询间隔（秒） |
| `opacity` | `0.95` | 整体不透明度 0.3~1.0 |
| `theme` | `dark` | `dark` / `light` |
| `show_mouse` | `true` | 显示鼠标块 |
| `show_headset` | `true` | 显示耳机块 |
| `percent_on_top` | `true` | 百分比在名称上方 |
| `size` | `normal` | `compact` / `normal` / `large` |

## 打包

```bash
pyinstaller --noconfirm --onefile --noconsole --name DeviceBattery --hidden-import hid --hidden-import pystray._win32 run.py
```

## 项目结构

```
DeviceBattery/
├── battery_widget/
│   ├── __init__.py      # 入口
│   ├── config.py        # 配置读写
│   ├── devices.py       # HID 设备协议（鼠标/耳机）
│   ├── render.py        # PIL 渲染（主题/尺寸/电量环）
│   └── win32_window.py  # Win32 透明窗口 + 菜单
├── run.py               # 源码入口
├── requirements.txt
└── data/                # 运行时配置（gitignore）
```

## 设备协议（逆向笔记）

### 鼠标 Lunafury TYPE33
- VID `0x373E`，无线 PID `0x0054` / 有线 PID `0x0084`
- 接口：usage_page `0xFFFF`，usage `0x0`
- feature report **65 字节**（不是 64！）：发 `[0]=rid, [3]=2, [4]=2, [6]=0x83` → 等 200ms → 读 65 字节 → `[7]=充电`, `[8]=电量%`
- 来源：逆向 lunafury 网页驱动 JS

### 耳机 SteelSeries Arctis Nova 5
- VID `0x1038`，PID `0x2232`
- 接口：usage_page `0xFFC0`，usage `1`
- output report：`[0]=0, [1]=0xB0` → input report：`[1]==0x02` 离线，`[3]=电量%`, `[4]==1` 充电
- 来源：开源项目 [HeadsetControl](https://github.com/Sapd/HeadsetControl)

## 技术要点

- **透明窗口**：`WS_EX_LAYERED` + `UpdateLayeredWindow` + `AC_SRC_ALPHA` 逐像素 alpha
  - 坑：Win11 上 `SetLayeredWindowAttributes` 的 colorkey 不生效（返回 0），必须走 UpdateLayeredWindow
- **DPI**：`SetProcessDPIAware()`，否则窗口错位
- **光标**：`LoadCursorW(IDC_ARROW)`，否则拖动时转圈
- **单文件打包**：pyinstaller onefile，`--hidden-import hid` 必须
