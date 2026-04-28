# AirControl 需求落实情况

## 资料来源
- `project.md`（总体需求与阶段规划）
- `AirControl 项目概要文档.md`（架构、算法细节、已知缺口）
- `AirControl 使用指南.md`（快捷操作与参数调优）
- `通用开发提示 prompt.md`（目录/命名/实现优先级约束）
- 代码：`main.py` 与 `aircontrol/` 模块

## 技术栈与运行
- Python 3.x；依赖见 `requirements.txt`：OpenCV、MediaPipe、pyautogui/pynput、PySide6、numpy。
- 运行：`python main.py`（需摄像头）。Qt UI/Overlay 可用 `s` 快捷键弹出设置窗口；配置持久化到 `config.json`。

## 需求覆盖对比

| 功能/要求 | 状态 | 依据 |
| --- | --- | --- |
| 摄像头采集（DShow）、读帧、释放 | ✅ 已实现 | `camera.py` |
| MediaPipe Hands 21 关键点实时追踪 | ✅ 已实现 | `hand_tracker.py` |
| 光标映射：ROI、死区、镜像 X/Y、OneEuro 滤波、速度增益 | ✅ 已实现 | `mapper.py`; 参数来自 `config.json` |
| 多显示器/虚拟屏支持、锁定目标显示器 | ✅ 已实现 | `monitor.py` + `mapper.monitor_rect` |
| DPI 适配 | ✅ 已实现 | `main.py::make_dpi_aware` |
| 系统事件：移动、单击、双击、右键、滚轮、鼠标按下/抬起 | ✅ 已实现 | `os_controller.py` + `main.py` |
| 手势 → 事件：pinch 单击、双 pinch 双击、长按 pinch 拖拽、拳头上下滚轮 | ✅ 已实现 | `gesture_engine.py` |
| 右键：食/中指伸直，快速下-上甩动判定 | ✅ 已实现 | `gesture_engine.py` |
| 菜单：张开手保持 menu_hold_ms 触发 | ✅ 已实现（仅切换 UI 帮助） | `gesture_engine.py` + `main.py` |
| 校准：OK 手势保持刷新 ROI | ✅ 已实现 | `gesture_engine.py` + `main.py` |
| UI：状态窗显示模式/事件/FPS，帮助提示可切换 | ✅ 已实现 | `ui.py` |
| Overlay：全屏透明层绘制手部骨架、光标、彩色轨迹 | ✅ 已实现 | `overlay.py` |
| 设置面板：镜像、滤波参数、ROI、死区、增益、显示器、轨迹等实时调整并保存 | ✅ 已实现 | `ui.py::SettingsWindow` |
| 轨迹可开启/关闭、长度/色速可调 | ✅ 已实现 | `config.py` + `overlay.py` |
| 配置文件自动加载/保存 UTF-8 | ✅ 已实现 | `config.py` |
| 双手同时识别/左右手并行策略 | ⚪ 未实现（仅取第一个或右手） | `main.py` 选择右手优先 |
| 缩放（双指距离变化 Zoom in/out） | ⚪ 未实现 | 未见事件/映射 |
| 双指/双手特殊快捷（Alt+Tab、截图等） | ⚪ 未实现 | 文档提到“占位宏/快捷键”但代码无 |
| 误检/鲁棒性处理（空帧、遮挡退避、自动暂停） | ⚠️ 基础 try/except 有，未有状态机级停用/恢复 | `main.py`, `gesture_engine.py` |
| 性能监测与日志记录 | ⚪ 未实现 | 无日志/性能统计 |
| Linux/macOS 适配（输入/显示） | ⚪ 未实现 | 仅 Win32 优化 |
| 文案编码/字体统一（终端乱码问题） | ⚪ 未处理 | 终端显示中文仍乱码 |

## 主要差距摘要
- 高阶交互：暂无缩放、双手协同、系统快捷键映射。
- 跨平台：输入适配仅 Windows（pyautogui/Win32）。
- 健壮性：未实现“无手自动 idle/暂停”、“重新检测后恢复”等逻辑；滚轮/右键阈值仍为硬编码。
- 观测与调试：缺少日志、FPS/延迟指标输出，异常提示有限。
- 文案/编码：部分中文在控制台乱码，需统一 UTF-8 或 UI 字体。

## 建议的下一步
1) 补齐缩放手势与快捷键映射（可将两指距离映射到 `scroll` 或自定义热键）。
2) 增加手势/相机失效的保护状态（无手 N 帧即暂停事件、恢复时倒计时提示）。
3) 拓展跨平台输入封装（pyautogui/pynput/平台特定后端的选择）。
4) 提供日志/性能面板（FPS、gesture 命中率、阈值调试）。
5) 统一中文显示编码，或在 UI 中内置中文提示，不依赖控制台编码。
