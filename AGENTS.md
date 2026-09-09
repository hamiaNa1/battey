# DeviceBattery 发布规则

- 每次完成源码更新后，优先运行语法检查和 `python -B test_tray.py`。
- 只有检查与 PyInstaller 构建成功时，才替换 `D:\gpt\Tools\DeviceBattery.exe`。
- 部署时只停止完整路径属于本项目的 `DeviceBattery.exe` 进程，保留 `D:\gpt\Tools\data`。
- 替换后从 `D:\gpt\Tools\DeviceBattery.exe` 启动，并确认所有 DeviceBattery 进程都从该路径运行。
- 部署失败时恢复先前可用版本；验证成功后删除临时回滚文件，不保留永久 EXE 备份。
- 多尺寸图标或其他尚未完成的实验不得提前部署。
