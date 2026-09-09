# DeviceBattery 发布规则

- 用户已授权本项目的常规修改、功能增加、测试、构建、部署和启动；完成范围明确的任务时直接执行，无需逐项确认。
- 仅当操作超出本项目、需要新的账号/密钥、会删除不可恢复的数据或受系统权限限制时，才说明原因并请求方向。
- 每次完成源码更新后，优先运行语法检查和 `python -B test_tray.py`。
- 只有检查与 PyInstaller 构建成功时，才替换 `D:\gpt\Tools\DeviceBattery.exe`。
- 部署时只停止完整路径属于本项目的 `DeviceBattery.exe` 进程，保留 `D:\gpt\Tools\data`。
- 替换后从 `D:\gpt\Tools\DeviceBattery.exe` 启动，并确认所有 DeviceBattery 进程都从该路径运行。
- 部署失败时恢复先前可用版本；验证成功后删除临时回滚文件，不保留永久 EXE 备份。
- 多尺寸图标或其他尚未完成的实验不得提前部署。
