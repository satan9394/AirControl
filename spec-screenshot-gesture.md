# Spec: 截图手势

## Objective
为 AirControl 添加"三指截图手势"：用户做出食指+中指+无名指三指伸出、小指弯曲、拇指不参与的手势，保持 1 秒后自动截屏，保存到桌面。

## Tech Stack
- Python 3.8+
- MediaPipe Hands（手势识别，已有）
- pyautogui（截图，已有依赖）
- 纯增量修改，不引入新依赖

## Commands
- 运行: `python main.py`
- 无测试框架（项目无 tests 目录）

## Project Structure
```
aircontrol/
├── gesture_engine.py   ← 新增截图手势识别 + hold 计时器
├── os_controller.py    ← 新增 screenshot() 方法
├── config.py           ← 新增 screenshot_hold_ms, screenshot_dir 配置项
└── main.py             ← 新增 "screenshot" 事件分发
```

## Code Style
遵循现有模式：
- GestureEngine：状态机 + hold 计时器（参考 menu/calibrate）
- OSController：平台操作封装（参考 click/scroll）
- Config：默认值 + config.json 读写

## Gesture Definition
- 三指伸出：index_tip.y < index_pip.y AND middle_tip.y < middle_pip.y AND ring_tip.y < ring_pip.y
- 小指弯曲：pinky_tip.y >= pinky_pip.y
- 拇指不参与（不检测 pinch）
- 保持 1000ms 触发截图

## Success Criteria
- [ ] 做出三指手势并保持 1 秒 → 截图保存到桌面
- [ ] 截图文件名格式: `screenshot_YYYYMMDD_HHMMSS.png`
- [ ] 截图后 event 显示 "Screenshot" 在画面和日志中
- [ ] 不与现有手势（menu=四指, calibrate=OK, right_click=两指）冲突
- [ ] screenshot_hold_ms 和 screenshot_dir 可通过 config.json 配置

## Boundaries
- Always: 遵循现有 GestureEngine 状态机模式，不重构
- Ask first: 修改手势冲突逻辑、添加新依赖
- Never: 改变现有手势行为、删除现有代码

## Open Questions
- 无 — 需求明确
