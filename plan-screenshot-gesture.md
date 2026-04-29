# Implementation Plan: 截图手势

## Overview
新增三指截图手势，在 4 个已有模块中各加少量代码，自底向上实现。

## Dependency Graph
```
Config (defaults)
    │
    ├── OSController (screenshot 方法)
    │       │
    │       └── main.py (事件分发 "screenshot")
    │
    └── GestureEngine (手势识别 + hold 计时)
            │
            └── main.py (调 engine.update)
```

## Task List

### Task 1: Config — 新增截图配置项
**Description:** 在 Config 默认字典和 GestureEngine/OSController 参数中增加截图相关配置。

**Acceptance criteria:**
- [ ] `screenshot_hold_ms` 默认 1000（ms）
- [ ] `screenshot_dir` 默认桌面路径
- [ ] 可通过 config.json 覆盖

**Verification:**
- [ ] `python -c "from aircontrol.config import Config; c=Config(); print(c.get('screenshot_hold_ms'), c.get('screenshot_dir'))"` 输出正确默认值

**Dependencies:** None
**Files:** `aircontrol/config.py`
**Scope:** XS (1 file)

### Task 2: OSController — 新增截图方法
**Description:** 在 OSController 中加 `screenshot(dir)` 方法，使用 pyautogui 截屏保存 PNG，文件名带时间戳。

**Acceptance criteria:**
- [ ] `screenshot(path)` 保存截图到指定目录
- [ ] 文件名格式 `screenshot_20260428_153045.png`
- [ ] 返回完整文件路径

**Verification:**
- [ ] `python -c "from aircontrol.os_controller import OSController; o=OSController(); print(o.screenshot('.'))"` 在当前目录生成截图

**Dependencies:** None（仅用已有 pyautogui）
**Files:** `aircontrol/os_controller.py`
**Scope:** XS (1 file)

### Task 3: GestureEngine — 新增三指手势识别
**Description:** 在 GestureEngine 中增加三指伸出检测（食+中+无名伸、小指弯、不检测拇指），hold 1000ms 后发出 "screenshot" 事件。参考现有 menu/calibrate 的 hold 计时器模式。

**Acceptance criteria:**
- [ ] 三指伸出+小指弯+hold 1s → 返回 `["screenshot"]`
- [ ] 手势中断后计时器重置
- [ ] 不与 menu（四指）、right_click（两指）冲突
- [ ] mode 设为 "screenshot"

**Verification:**
- [ ] 代码审查：确认三指检测逻辑与现有手势互斥
- [ ] 无测试框架，通过实际运行观察 event 输出

**Dependencies:** Task 1（screenshot_hold_ms 配置项）
**Files:** `aircontrol/gesture_engine.py`
**Scope:** S (1 file)

### Task 4: main.py — 事件连线
**Description:** 在 main.py 事件循环中增加 "screenshot" 事件处理，调用 osctrl.screenshot() 并更新 last_event。同时把 screenshot_hold_ms 传入 GestureEngine 构造。

**Acceptance criteria:**
- [ ] engine 构造传入 screenshot_hold_ms
- [ ] "screenshot" 事件 → 调用 osctrl.screenshot(screenshot_dir)
- [ ] last_event = "Screenshot"，显示在画面和日志中

**Verification:**
- [ ] 运行 `python main.py`，做三指手势保持 1 秒，桌面出现截图文件
- [ ] 画面显示 "Screenshot"，日志输出 `event=Screenshot`

**Dependencies:** Task 2, Task 3
**Files:** `aircontrol/main.py`
**Scope:** XS (1 file)

## Checkpoint: 全部完成
- [ ] 4 个文件修改完毕
- [ ] 三指手势 → 截图到桌面
- [ ] 现有手势不受影响（回归：click/double/right/drag/scroll/menu/calibrate）

## Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| 三指与四指 menu 手势冲突 | Low | 三指要求 pinky 弯曲，四指要求 pinky 伸展，互斥 |
| 两指右键手势干扰 | Low | 两指不含 ring，三指含 ring，互斥 |
