AirControl 项目需求文档
1. 项目简介
核心目标：使用普通摄像头+MediaPipe Hands 实时识别手势，将指尖映射为鼠标/触控板输入，支持移动、单击、双击、右键、拖拽、滚轮、菜单呼出、校准等操作。
项目价值：免接触、可穿戴友好的桌面控制，力争达到触控板级流畅度与准确度；多显示器、自适应 ROI，保障全屏无死角操作。
最终体验标准：在常规笔记本/USB 摄像头上提供流畅（≥60FPS 目标）、低延迟（移动时延 <15ms 目标）的指针控制，抖动可感知度接近 1px/s 内。
2. 系统总体架构
摄像头输入管线（camera.py）：OpenCV 采集 BGR 帧，DShow 打开摄像头，支持配置宽高。
手部关键点识别（hand_tracker.py）：MediaPipe Hands，输出 21 关键点 + handedness；自带绘制骨架能力。
手势状态机（gesture_engine.py）：基于规则的事件生成器，支持 pinch 单击/拖拽、双 pinch 双击、两指弹击右键、握拳滚动、张掌菜单、OK 校准；内部模式优先级：拖拽 > 滚动 > 点击 > 移动（菜单为独立模式）。
坐标映射（mapper.py）：ROI + 死区裁剪 → One-Euro 滤波 → 速度自适应增益 → 多显示器/虚拟屏坐标输出；支持镜像 X/Y、非滤波坐标回显。
轨迹平滑算法：One-Euro（最小截止频率 min_cutoff + 自适应项 beta + 导数滤波 d_cutoff），叠加速度增益与裁剪，减少低速抖动、保持高速灵敏。
误触拒绝机制：死区裁剪（ROI 内 XY 边缘留白）、拖拽延时阈值、右键折返速度阈值、滚动累计阈值、菜单/校准长按判定、双击时间窗。
事件注入层（os_controller.py）：pyautogui 默认驱动，Win32 SetCursorPos 可选以降低移动延迟；封装 move/click/double/right/scroll/down/up。
UI 覆盖（ui.py + overlay.py）：PySide6 半透明状态窗、设置窗；全屏 Overlay 绘制指针、轨迹、骨架、帮助提示。
配置与监视（config.py, monitor.py）：从 config.json 读取/写入参数；枚举物理/虚拟屏，支持锁定目标显示器。
3. 关键技术要求
识别帧率 ≥60FPS（软目标；当前实现依赖 CPU，需按 ROI/分辨率调优）。
鼠标移动端到端时延 <15ms（需 Win32 直驱 + 轻量推理 + UI 解耦）。
轨迹漂移 <1px/s（One-Euro 低速收敛 + 死区裁剪）。
点击准确率 >95%，双击节奏自适应时间窗（默认 500ms，可配置）。
滚动/拖拽无抖动：One-Euro 数学描述
导数滤波：dx_hat = α_d * dx + (1-α_d) * dx_prev，α_d = 1 / (1 + τ_d/dt)，τ_d = 1/(2π·d_cutoff)
自适应截止频率：cutoff = min_cutoff + beta * |dx_hat|
值滤波：x_hat = α * x + (1-α) * x_prev，α = 1 / (1 + τ/dt)，τ = 1/(2π·cutoff)
速度增益：eff_gain = gain * (1 + vel_gain * |v|)，v 为归一坐标速度，裁剪至 vel_clip。
右键/菜单/校准需长按或速度折返判定，避免误触。
4. 手势体系设计
基础手势
Move：食指指尖位置 → 屏幕坐标（ROI + One-Euro + 速度增益）。
Click：拇指-食指距离 < pinch_thresh，短按释放。
DoubleClick：拇指同时夹食指+中指，50–350ms 弹起。
Drag：pinch 持续 ≥ drag_hold_ms 触发 drag_start，松开 drag_end。
Scroll：四指收拢（握拳），手腕 Y 轴累计超阈值 → scroll_speed 比例滚动。
专用手势（预留/部分实现）
Menu：四指张开手掌保持 menu_hold_ms。
Calibrate：OK 姿势保持 menu_hold_ms，刷新 ROI 中心与尺寸。
截图 / Alt+Tab / 音量：占位，需映射到状态机事件或热键层。
状态机（文字版）
Idle → (检测到手) Move
Move ↔ Click（pinch） ↔ Drag（pinch 超时）
Move ↔ Scroll（握拳）
任意 → Menu（张掌长按）
任意 → Calibrate（OK 长按）
DoubleClick 在 Click 短按双指判定阶段触发
RightClick 在两指伸直+上下折返速度窗内触发
误触判定逻辑
Click 与 Drag 通过时间阈值分离；双击窗口独立于拖拽。
RightClick 仅在食/中指伸直且环/小指卷曲时，检测上下折返速度。
Scroll 仅全指卷曲时激活，累计阈值 0.01；离开姿态即清零。
Menu/Calibrate 需长按 1s，且 pinch 释放。
5. 模块拆分
camera.py：摄像头采集与资源释放。
hand_tracker.py：MediaPipe Hands 初始化、推理、骨架绘制。
gesture_engine.py：手势规则、状态机、事件输出。
mapper.py：One-Euro 滤波、ROI/死区、镜像、速度增益、屏幕/显示器映射。
os_controller.py：pyautogui/Win32 光标与按键封装，DPI 感知。
monitor.py：多显示器/虚拟屏枚举，矩形信息封装。
overlay.py：全屏半透明轨迹+骨架渲染，帮助提示。
ui.py：状态窗/帮助文本；设置面板（镜像、平滑、增益、ROI、死区、轨迹、目标显示器），快捷键 s 切换。
config.py：config.json 读写，默认参数集中管理。
main.py：总线式集成（Cam → Tracker → Mapper → Gesture → OSController → UI/Overlay），主循环、事件分发、ROI 矩形回显。
6. 实现建议与技术优化
轨迹平滑对比
均值滤波：实现简单，延迟高，易拖尾。
One-Euro（当前）：低速稳，高速灵敏，自适应截止频率；需调参 min_cutoff/beta/d_cutoff。
卡尔曼：预测效果好，需噪声建模，适合高抖动场景，可在 Mapper 中替换/可选。
降低延迟
使用 Win32 SetCursorPos（已封装）替代 pyautogui 移动；MediaPipe 设 model_complexity=0，降低分辨率/ROI 域；UI 渲染与推理解耦线程。
提高鲁棒性
手型判定加入骨架尺度归一化（已按归一坐标）；可引入手掌朝向、角度补偿；右键/双击引入滞后消抖。
光照自适应：限定 ROI、自动白平衡（OpenCV）、曝光锁定、肤色失配时的置信度门控。
光照变化最小化
固定摄像头自动曝光；低光提高 min_detection_confidence；可用高斯模糊减噪后再投喂 MediaPipe。
全屏无死角
ROI 尺寸动态随手距离缩放；死区最小化但保留 2–6% 边缘；多显示器时锁定目标显示器或虚拟屏全域。
ROI 自适应
通过 Calibrate（OK 长按）记录当前手中心/大小更新 ROI；跟踪时依据手形尺度调整 ROI 宽高。
多显示器支持
复用 monitor.py 选定 target_monitor_index；虚拟屏模式映射所有屏；校准时应按照目标显示器分辨率重设 ROI。
7. 性能指标（必须达标）
FPS：推理+绘制 ≥60 FPS（默认 640×480，单手）；UI/Overlay 不得显著掉帧。
Latency：摄像头帧 → 光标移动 <15ms；点击事件触发滞后 <30ms。
Error rate：指针漂移 <1px/s；点击/双击误触率 <5%；右键/拖拽误触率 <5%。
Gesture Confidence/分布：统计 pinch 距离、速度分布；右键折返速度触发分布；滚动累计量分布，用于阈值自适应。
8. 未来扩展路线图
端侧推理：MediaPipe → TFLite/MNN/NCNN 模型替换，适配 ARM/移动端。
移动端触控板模式：Android 相机 + 本地手势 → 模拟触控板 HID。
VR/空间交互：3D 手势、姿态跟踪，映射为空间光标/抓取。
语音 + 手势协同：语音唤醒 + 手势执行复合命令。
触控板级模拟：加速度曲线、摩擦模型、Pointer Precision 模式开关。
热键/宏系统：手势到脚本映射，用户级可配置。
9. 自动补全与缺失修复
当前已实现：摄像头输入、MediaPipe 手部、One-Euro + 速度增益映射、多显示器、基础/菜单/校准手势、Win32 低延迟移动、UI/Overlay/设置面板、配置持久化。
未完成/待补：
专用热键（截图/Alt+Tab/音量）未绑定；双指缩放未实现；双手协同未用。
性能监测缺失：无 FPS/延迟日志落盘，无自动基准测试。
误触抑制可强化：右键/双击阈值需根据手尺寸自适应；滚动阈值固定 0.01 需归一尺度。
多平台：Linux/macOS 未适配事件注入、显示器枚举。
文本编码：UI/Overlay 帮助文本在部分终端显示为乱码，需统一 UTF-8 字体/编码。
TODO 列表（建议）
 为手势事件增加信号质量与置信度输出，写入调试 HUD/日志。
 引入 Kalman/多阶滤波选项与参数面板。
 增加缩放手势（双指距离变化）与快捷手势映射层。
 抽象 OSController 以适配 Linux/macOS（evdev/CGEvent）。
 分离推理/渲染线程，提升帧率与 UI 响应。
 提供自动热点校准：根据窗口分布优化 ROI/增益。
重构建议
将 gesture_engine 状态机拆分为“姿态判定层”和“事件节奏层”，便于扩展/学习型分类器接入。
mapper 增加采样频率自检测和 dt 平滑，避免时间戳抖动。
配置层增加版本号与迁移逻辑，防止老配置缺键。
潜在 Bug 隐患
双击手势与单击释放同源 pinch，阈值过短可能误判；需增加点击抑制窗口。
右键依赖上下速度折返，低帧率时可能漏判；可加入时长/加速度多重判据。
Menu 模式退出逻辑依赖姿态变化，缺少显式超时；可能卡在菜单模式。
Overlay/Qt 与 OpenCV 同时取事件，若 UI 失焦 waitKey 会阻塞；需考虑非阻塞事件轮询或纯 Qt 渲染路径。