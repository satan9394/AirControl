import time
import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import ctypes
from aircontrol.camera import Camera
from aircontrol.hand_tracker import HandTracker
from aircontrol.mapper import CoordinateMapper
from aircontrol.os_controller import OSController, get_screen_size
from aircontrol.gesture_engine import GestureEngine
from aircontrol.config import Config
from aircontrol.monitor import get_monitors, get_virtual_screen
from collections import deque
import random


def make_dpi_aware():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

def main():
    cv2.setUseOptimized(True)
    cfg = Config()
    make_dpi_aware()
    from aircontrol.ui import create_app, StatusWindow, create_settings
    cam = Camera(cfg.get("camera_index"), cfg.get("frame_width"), cfg.get("frame_height"))
    tracker = HandTracker(cfg.get("mediapipe_max_hands"), cfg.get("mediapipe_detection_confidence"), cfg.get("mediapipe_tracking_confidence"), cfg.get("model_complexity"))
    monitors = get_monitors()
    lock_to_monitor = cfg.get("lock_to_monitor")
    if lock_to_monitor and monitors:
        mi = monitors[cfg.get("target_monitor_index")]
        monitor_rect = (mi.left, mi.top, mi.width, mi.height)
        screen_size = (mi.width, mi.height)
    else:
        vx, vy, vw, vh = get_virtual_screen()
        monitor_rect = (vx, vy, vw, vh)
        screen_size = (vw, vh)
    mapper = CoordinateMapper(
        screen_size,
        cfg.get("mapper_alpha"),
        (cfg.get("deadzone_x"), cfg.get("deadzone_y")),
        (cfg.get("roi_width"), cfg.get("roi_height")),
        cfg.get("mirror_x"),
        cfg.get("min_cutoff"), cfg.get("beta"), cfg.get("derivative_cutoff"),
        cfg.get("pointer_gain"),
        monitor_rect,
        cfg.get("mirror_y"),
    )
    osctrl = OSController(cfg.get("use_win32_mouse"))
    engine = GestureEngine(cfg.get("click_window_ms"), cfg.get("double_click_window_ms"), cfg.get("drag_hold_ms"), cfg.get("pinch_thresh"), cfg.get("right_tap_velocity"), cfg.get("scroll_speed"), cfg.get("menu_hold_ms"))
    app = None
    win = None
    preferred_hand = cfg.get("preferred_hand", "right")
    dual_hand_zoom = bool(cfg.get("dual_hand_zoom"))
    zoom_sensitivity = float(cfg.get("zoom_sensitivity"))
    zoom_min_delta = float(cfg.get("zoom_min_delta"))
    use_ctrl_zoom = bool(cfg.get("use_ctrl_zoom"))
    no_hand_pause_frames = int(cfg.get("no_hand_pause_frames"))
    resume_grace_frames = int(cfg.get("resume_grace_frames"))
    log_interval_sec = float(cfg.get("log_interval_sec"))
    if cfg.get("ui_enabled"):
        app, win = create_app(cfg.get("ui_opacity"), cfg.get("ui_help_enabled"))
        settings = create_settings(app, cfg, mapper, engine, osctrl, monitors)
        from aircontrol.overlay import TrailOverlay
        overlay = TrailOverlay(
            monitor_rect,
            cfg.get("ui_help_enabled"),
            point_radius=int(cfg.get("hand_point_radius")),
            line_width=int(cfg.get("hand_line_width")),
            skeleton_scale=float(cfg.get("hand_skeleton_scale")),
            point_glow=bool(cfg.get("hand_point_glow")),
        )
        overlay.show()
    last = time.time()
    last_event = ""
    trail_enabled = bool(cfg.get("trail_enabled"))
    trail_len = int(cfg.get("trail_length"))
    trail_hue_speed = int(cfg.get("trail_hue_speed"))
    trail = deque(maxlen=trail_len)
    base_hue = random.randint(0, 180)
    zoom_prev = None
    no_hand_frames = 0
    paused = False
    resume_frames_left = 0
    last_log = time.time()
    try:
        while True:
            frame = cam.read()
            if frame is None:
                break
            result = tracker.process(frame)
            hand_list = []
            if result and result.multi_hand_landmarks:
                try:
                    if result.multi_handedness:
                        for i, hd in enumerate(result.multi_handedness):
                            lbl = hd.classification[0].label.lower()
                            hand_list.append((lbl, result.multi_hand_landmarks[i]))
                    else:
                        hand_list = [("unknown", h) for h in result.multi_hand_landmarks]
                except Exception:
                    hand_list = [("unknown", h) for h in result.multi_hand_landmarks]
            primary_hand = None
            secondary_hand = None
            if hand_list:
                def pick_hand(pref):
                    if pref == "any":
                        return hand_list[0]
                    for lbl, h in hand_list:
                        if lbl == pref:
                            return (lbl, h)
                    return hand_list[0]
                if preferred_hand:
                    primary_hand = pick_hand(preferred_hand)
                else:
                    primary_hand = hand_list[0]
                if dual_hand_zoom and len(hand_list) >= 2:
                    secondary_hand = hand_list[1] if hand_list[0] == primary_hand else hand_list[0]
            has_hand = primary_hand is not None
            if has_hand:
                if paused:
                    resume_frames_left = resume_grace_frames
                    paused = False
                no_hand_frames = 0
            else:
                zoom_prev = None
                no_hand_frames += 1
                if no_hand_frames >= no_hand_pause_frames:
                    paused = True
                tracker.draw(frame, result)
            if has_hand:
                hand = primary_hand[1]
                tip = hand.landmark[mp.solutions.hands.HandLandmark.INDEX_FINGER_TIP]
                ts = int(time.time() * 1000)
                x, y = mapper.map((tip.x, tip.y), ts)
                if resume_frames_left == 0 and not paused:
                    osctrl.move_to(x, y)
                if trail_enabled:
                    trail.append((x, y))
                if cfg.get("ui_enabled"):
                    lx = x - monitor_rect[0]
                    ly = y - monitor_rect[1]
                    overlay.update_trail([(px - monitor_rect[0], py - monitor_rect[1]) for (px, py) in list(trail)], (lx, ly))
                    hands_list = []
                    conns_src = mp.solutions.hands.HAND_CONNECTIONS
                    conns = []
                    for a, b in conns_src:
                        ai = getattr(a, "value", a)
                        bi = getattr(b, "value", b)
                        conns.append((int(ai), int(bi)))
                    for lbl, h in hand_list:
                        pts = []
                        for lm_i in range(len(h.landmark)):
                            sx, sy = mapper.to_screen_unfiltered((h.landmark[lm_i].x, h.landmark[lm_i].y))
                            pts.append((sx - monitor_rect[0], sy - monitor_rect[1]))
                        hands_list.append((pts, conns))
                    overlay.update_hands(hands_list)
                events = engine.update(hand, int(time.time() * 1000))
                if resume_frames_left == 0 and not paused:
                    for e in events:
                        if e == "click":
                            osctrl.click()
                            last_event = "Click"
                        elif e == "double_click":
                            osctrl.double_click()
                            last_event = "DoubleClick"
                        elif e == "right_click":
                            osctrl.right_click()
                            last_event = "RightClick"
                        elif e == "drag_start":
                            osctrl.mouse_down()
                            last_event = "DragStart"
                        elif e == "drag_end":
                            osctrl.mouse_up()
                            last_event = "DragEnd"
                        elif isinstance(e, tuple) and e[0] == "scroll":
                            osctrl.scroll(e[1])
                            last_event = "Scroll"
                        elif e == "menu":
                            last_event = "Menu"
                        elif e == "calibrate":
                            xs = [lm.x for lm in hand.landmark]
                            ys = [lm.y for lm in hand.landmark]
                            cx = min(max(sum(xs) / len(xs), 0.0), 1.0)
                            cy = min(max(sum(ys) / len(ys), 0.0), 1.0)
                            mapper.update_roi((cx, cy), (cfg.get("roi_width"), cfg.get("roi_height")))
                            last_event = "Calibrated"
                if dual_hand_zoom and secondary_hand:
                    h1 = primary_hand[1]
                    h2 = secondary_hand[1]
                    p1 = h1.landmark[mp.solutions.hands.HandLandmark.INDEX_FINGER_TIP]
                    p2 = h2.landmark[mp.solutions.hands.HandLandmark.INDEX_FINGER_TIP]
                    dist = ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5
                    if zoom_prev is not None:
                        delta = dist - zoom_prev
                        if abs(delta) > zoom_min_delta and resume_frames_left == 0 and not paused:
                            clicks = int(delta * zoom_sensitivity)
                            if clicks != 0:
                                osctrl.zoom(clicks, use_ctrl_zoom)
                                last_event = "ZoomIn" if clicks > 0 else "ZoomOut"
                    zoom_prev = dist
            tracker.draw(frame, result)
            if resume_frames_left > 0:
                resume_frames_left = max(resume_frames_left - 1, 0)
            now = time.time()
            fps = 1.0 / (now - last) if now > last else 0.0
            last = now
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            if last_event:
                cv2.putText(frame, last_event, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 255), 2)
            if paused:
                cv2.putText(frame, "Paused - no hands", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            elif resume_frames_left > 0:
                cv2.putText(frame, f"Resuming in {resume_frames_left}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)
            if app and win:
                win.update_status(engine.mode, last_event + (" (Paused)" if paused else ""), fps)
                if last_event == "Menu":
                    win.toggle_help(True)
                app.processEvents()
                overlay.set_help_visible(cfg.get("ui_help_enabled"))
                overlay.set_bounds(mapper.monitor_rect)
            rx = int((mapper.roi_cx - mapper.roi_w / 2.0) * frame.shape[1])
            ry = int((mapper.roi_cy - mapper.roi_h / 2.0) * frame.shape[0])
            rw = int(mapper.roi_w * frame.shape[1])
            rh = int(mapper.roi_h * frame.shape[0])
            cv2.rectangle(frame, (rx, ry), (rx + rw, ry + rh), (80, 80, 80), 2)
            if trail_enabled and len(trail) > 1:
                for i in range(1, len(trail)):
                    hue = (base_hue + i * trail_hue_speed) % 180
                    color = cv2.cvtColor(
                        (np.array([[[hue, 255, 255]]], dtype=np.uint8)),
                        cv2.COLOR_HSV2BGR
                    )[0,0].tolist()
                    c = (int(color[0]), int(color[1]), int(color[2]))
                    cv2.line(frame, trail[i-1], trail[i], c, 2)
            cv2.imshow("AirControl", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord("q"):
                break
            if app and key == ord("s"):
                settings.toggle()
            if now - last_log >= log_interval_sec:
                print(f"[AirControl] FPS={fps:.1f} mode={engine.mode} event={last_event} paused={paused} hands={len(hand_list) if hand_list else 0}")
                last_log = now
    finally:
        tracker.close()
        cam.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
