import json
import os


class Config:
    def __init__(self, path="config.json"):
        self.path = path
        self.data = {
            "camera_index": 0,
            "frame_width": 640,
            "frame_height": 480,
            "mediapipe_max_hands": 2,
            "mediapipe_detection_confidence": 0.5,
            "mediapipe_tracking_confidence": 0.5,
            "model_complexity": 0,
            "mapper_alpha": 0.4,
            "deadzone_x": 0.02,
            "deadzone_y": 0.02,
            "roi_width": 1.0,
            "roi_height": 1.0,
            "pinch_thresh": 0.05,
            "click_window_ms": 250,
            "double_click_window_ms": 500,
            "drag_hold_ms": 200,
            "right_tap_velocity": 0.06,
            "scroll_speed": 60,
            "menu_hold_ms": 1000,
            "calib_hold_ms": 1000,
            "min_cutoff": 1.5,
            "beta": 0.4,
            "derivative_cutoff": 1.0,
            "pointer_gain": 1.1,
            "use_win32_mouse": True,
            "mirror_x": False,
            "target_monitor_index": 0,
            "lock_to_monitor": True,
            "trail_enabled": True,
            "trail_length": 60,
            "trail_hue_speed": 3,
            "mirror_y": False,
            "hand_point_radius": 3,
            "hand_line_width": 4,
            "hand_skeleton_scale": 0.45,
            "hand_point_glow": True,
            "ui_enabled": True,
            "ui_opacity": 0.8,
            "ui_help_enabled": True,
            "preferred_hand": "right",  # right/left/any
            "dual_hand_zoom": True,
            "zoom_sensitivity": 800,
            "zoom_min_delta": 0.005,
            "use_ctrl_zoom": True,
            "no_hand_pause_frames": 20,
            "resume_grace_frames": 8,
            "log_interval_sec": 5.0,
        }
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                self.data.update(loaded)
            except Exception:
                pass

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get(self, key, default=None):
        return self.data.get(key, default)
