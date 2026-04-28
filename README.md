# AirControl — 空中手势桌面控制系统

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Hands-orange.svg)](https://mediapipe.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

使用普通摄像头 + MediaPipe Hands 实时手势识别，将指尖映射为鼠标/触控板输入。支持移动、单击、双击、右键、拖拽、滚轮、菜单呼出、校准等操作。

## ✨ 功能特性

- **光标控制**：食指指尖位置映射屏幕坐标（ROI + One-Euro 滤波 + 速度增益）
- **手势体系**：单击/双击/右键/拖拽/滚轮/菜单/校准，基于状态机避免手势冲突
- **多显示器**：自动枚举物理/虚拟屏，支持锁定目标显示器
- **透明 Overlay**：桌面覆盖层实时显示手部骨架、光标轨迹、当前手势
- **设置面板**：快捷键 `s` 呼出面板，可调 ROI、死区、平滑参数、镜像等
- **配置持久化**：参数写入 `config.json`，即时生效

## 🖐 手势操作

| 手势 | 操作 |
|------|------|
| 食指伸出 | 移动光标 |
| 拇指+食指闭合（短） | 单击 |
| 拇指+食指+中指闭合 | 双击 |
| 拇指+食指闭合（长按） | 拖拽 |
| 食指+中指伸出 + 下击上扬 | 右键 |
| 握拳上下移动 | 滚轮 |
| 四指张开保持 | 菜单 |
| OK 手势保持 | 校准 ROI |

## 🚀 快速开始

### 环境要求
- Python 3.8+
- 摄像头（笔记本内置或 USB，≥720p）

### 安装运行
```bash
pip install -r requirements.txt
python main.py
```

按 `s` 键打开设置面板，建议先做 OK 手势校准。

## 🏗 项目结构

```
AirControl/
├── main.py                  # 入口：摄像头循环 + 事件整合
├── requirements.txt         # Python 依赖
└── aircontrol/
    ├── camera.py            # OpenCV DShow 摄像头采集
    ├── hand_tracker.py      # MediaPipe Hands 21 关键点追踪
    ├── gesture_engine.py    # 手势状态机：姿态 → 事件
    ├── mapper.py            # One-Euro 滤波 + ROI/死区 + 屏幕映射
    ├── os_controller.py     # pyautogui/Win32 光标与按键注入
    ├── monitor.py           # 多显示器/虚拟屏枚举
    ├── overlay.py           # PySide6 全屏透明覆盖层
    ├── ui.py                # 状态窗口 + 设置面板
    └── config.py            # config.json 读写 + 默认参数
```

## 📝 文档

- `AirControl 项目需求文档.md` — 完整需求规格
- `STATUS.md` — 需求落实情况对比
- `操作指南.md` — 用户操作说明
- `项目报告.md` — 技术要点总结
- `project.md` — 总体架构与阶段规划

## 🤝 License

MIT
