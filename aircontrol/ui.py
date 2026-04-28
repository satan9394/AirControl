from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QSlider, QCheckBox, QPushButton, QComboBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class StatusWindow(QWidget):
    def __init__(self, opacity=0.8, show_help=True):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(opacity)
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: white; background-color: rgba(0,0,0,160); padding:6px; border-radius:8px;")
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.help_label = QLabel("")
        self.help_label.setStyleSheet("color: white; background-color: rgba(0,0,0,160); padding:6px; border-radius:8px;")
        self.help_label.setFont(QFont("Segoe UI", 9))
        layout.addWidget(self.status_label)
        if show_help:
            layout.addWidget(self.help_label)
        self.setLayout(layout)
        self.resize(300, 140)
        self.move(20, 20)
        self.help_visible = show_help
        if show_help:
            self.help_label.setText(
                "Hint: pinch=click/double; long pinch=drag; fist up/down=scroll; "
                "two-finger flick=right click; open palm=menu; if you see garbled text, set console to UTF-8."
            )

    def update_status(self, mode, last_event, fps):
        self.status_label.setText(f"mode:{mode}  event:{last_event}  FPS:{fps:.1f}")

    def toggle_help(self, visible):
        self.help_visible = visible
        self.help_label.setVisible(visible)


def create_app(opacity=0.8, show_help=True):
    app = QApplication.instance() or QApplication([])
    win = StatusWindow(opacity, show_help)
    win.show()
    return app, win


class SettingsWindow(QWidget):
    def __init__(self, cfg, mapper, engine, osctrl, monitors):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setWindowTitle("AirControl Settings")
        layout = QVBoxLayout()

        self.mirror = QCheckBox("mirror X")
        self.mirror.setChecked(bool(cfg.get("mirror_x")))
        layout.addWidget(self.mirror)

        self.mirror_y = QCheckBox("mirror Y")
        self.mirror_y.setChecked(bool(cfg.get("mirror_y")))
        layout.addWidget(self.mirror_y)

        self.alpha = QSlider(Qt.Horizontal)
        self.alpha.setRange(0, 100)
        self.alpha.setValue(int(cfg.get("mapper_alpha") * 100))
        layout.addWidget(QLabel("smooth alpha"))
        layout.addWidget(self.alpha)

        self.min_cutoff = QSlider(Qt.Horizontal)
        self.min_cutoff.setRange(5, 300)
        self.min_cutoff.setValue(int(cfg.get("min_cutoff") * 100))
        layout.addWidget(QLabel("min_cutoff"))
        layout.addWidget(self.min_cutoff)

        self.beta = QSlider(Qt.Horizontal)
        self.beta.setRange(0, 300)
        self.beta.setValue(int(cfg.get("beta") * 100))
        layout.addWidget(QLabel("beta"))
        layout.addWidget(self.beta)

        self.gain = QSlider(Qt.Horizontal)
        self.gain.setRange(50, 200)
        self.gain.setValue(int(cfg.get("pointer_gain") * 100))
        layout.addWidget(QLabel("pointer gain"))
        layout.addWidget(self.gain)

        self.dead_x = QSlider(Qt.Horizontal)
        self.dead_x.setRange(0, 100)
        self.dead_x.setValue(int(cfg.get("deadzone_x") * 100))
        layout.addWidget(QLabel("deadzone X"))
        layout.addWidget(self.dead_x)

        self.dead_y = QSlider(Qt.Horizontal)
        self.dead_y.setRange(0, 100)
        self.dead_y.setValue(int(cfg.get("deadzone_y") * 100))
        layout.addWidget(QLabel("deadzone Y"))
        layout.addWidget(self.dead_y)

        self.roi_w = QSlider(Qt.Horizontal)
        self.roi_w.setRange(10, 100)
        self.roi_w.setValue(int(cfg.get("roi_width") * 100))
        layout.addWidget(QLabel("ROI width %"))
        layout.addWidget(self.roi_w)

        self.roi_h = QSlider(Qt.Horizontal)
        self.roi_h.setRange(10, 100)
        self.roi_h.setValue(int(cfg.get("roi_height") * 100))
        layout.addWidget(QLabel("ROI height %"))
        layout.addWidget(self.roi_h)

        self.monitor = QComboBox()
        for i, m in enumerate(monitors or []):
            self.monitor.addItem(f"{i}:{m.name} {m.width}x{m.height}")
        self.monitor.setCurrentIndex(int(cfg.get("target_monitor_index")))
        layout.addWidget(QLabel("target monitor"))
        layout.addWidget(self.monitor)

        self.lock_monitor = QCheckBox("lock to monitor")
        self.lock_monitor.setChecked(bool(cfg.get("lock_to_monitor")))
        layout.addWidget(self.lock_monitor)

        self.trail_enabled = QCheckBox("enable trail")
        self.trail_enabled.setChecked(bool(cfg.get("trail_enabled")))
        layout.addWidget(self.trail_enabled)

        self.trail_len = QSlider(Qt.Horizontal)
        self.trail_len.setRange(10, 600)
        self.trail_len.setValue(int(cfg.get("trail_length")))
        layout.addWidget(QLabel("trail length"))
        layout.addWidget(self.trail_len)

        self.trail_hue = QSlider(Qt.Horizontal)
        self.trail_hue.setRange(1, 20)
        self.trail_hue.setValue(int(cfg.get("trail_hue_speed")))
        layout.addWidget(QLabel("trail hue speed"))
        layout.addWidget(self.trail_hue)

        # Hand preference and zoom controls
        self.preferred_hand = QComboBox()
        for opt in ["right", "left", "any"]:
            self.preferred_hand.addItem(opt)
        try:
            idx = ["right", "left", "any"].index(str(cfg.get("preferred_hand", "right")).lower())
        except Exception:
            idx = 0
        self.preferred_hand.setCurrentIndex(idx)
        layout.addWidget(QLabel("preferred hand"))
        layout.addWidget(self.preferred_hand)

        self.dual_zoom = QCheckBox("enable dual-hand zoom")
        self.dual_zoom.setChecked(bool(cfg.get("dual_hand_zoom")))
        layout.addWidget(self.dual_zoom)

        self.ctrl_zoom = QCheckBox("Ctrl + wheel zoom")
        self.ctrl_zoom.setChecked(bool(cfg.get("use_ctrl_zoom")))
        layout.addWidget(self.ctrl_zoom)

        self.zoom_sense = QSlider(Qt.Horizontal)
        self.zoom_sense.setRange(100, 2000)
        self.zoom_sense.setValue(int(cfg.get("zoom_sensitivity")))
        layout.addWidget(QLabel("zoom sensitivity"))
        layout.addWidget(self.zoom_sense)

        self.zoom_delta = QSlider(Qt.Horizontal)
        self.zoom_delta.setRange(1, 20)
        self.zoom_delta.setValue(int(cfg.get("zoom_min_delta") * 1000))
        layout.addWidget(QLabel("zoom min delta (x/1000)"))
        layout.addWidget(self.zoom_delta)

        self.apply_btn = QPushButton("apply settings")
        layout.addWidget(self.apply_btn)
        self.setLayout(layout)
        self.resize(380, 620)

        def apply():
            cfg.data["mirror_x"] = self.mirror.isChecked()
            cfg.data["mapper_alpha"] = self.alpha.value() / 100.0
            cfg.data["min_cutoff"] = self.min_cutoff.value() / 100.0
            cfg.data["beta"] = self.beta.value() / 100.0
            cfg.data["pointer_gain"] = self.gain.value() / 100.0
            cfg.data["deadzone_x"] = self.dead_x.value() / 100.0
            cfg.data["deadzone_y"] = self.dead_y.value() / 100.0
            cfg.data["roi_width"] = self.roi_w.value() / 100.0
            cfg.data["roi_height"] = self.roi_h.value() / 100.0
            cfg.data["target_monitor_index"] = self.monitor.currentIndex()
            cfg.data["mirror_y"] = self.mirror_y.isChecked()
            cfg.data["lock_to_monitor"] = self.lock_monitor.isChecked()
            cfg.data["trail_enabled"] = self.trail_enabled.isChecked()
            cfg.data["trail_length"] = int(self.trail_len.value())
            cfg.data["trail_hue_speed"] = int(self.trail_hue.value())
            cfg.data["preferred_hand"] = self.preferred_hand.currentText()
            cfg.data["dual_hand_zoom"] = self.dual_zoom.isChecked()
            cfg.data["zoom_sensitivity"] = int(self.zoom_sense.value())
            cfg.data["zoom_min_delta"] = max(self.zoom_delta.value() / 1000.0, 0.001)
            cfg.data["use_ctrl_zoom"] = self.ctrl_zoom.isChecked()
            cfg.save()

            mi = (monitors or [None])[self.monitor.currentIndex()] if (monitors and len(monitors) > 0) else None
            mapper.mirror_x = cfg.get("mirror_x")
            mapper.mirror_y = cfg.get("mirror_y")
            mapper.roi_w = cfg.get("roi_width")
            mapper.roi_h = cfg.get("roi_height")
            mapper.deadzone_x = cfg.get("deadzone_x")
            mapper.deadzone_y = cfg.get("deadzone_y")
            mapper.filter_x.min_cutoff = cfg.get("min_cutoff")
            mapper.filter_x.beta = cfg.get("beta")
            mapper.filter_y.min_cutoff = cfg.get("min_cutoff")
            mapper.filter_y.beta = cfg.get("beta")
            mapper.gain = cfg.get("pointer_gain")
            if self.lock_monitor.isChecked() and mi:
                mapper.monitor_rect = (mi.left, mi.top, mi.width, mi.height)
            else:
                from aircontrol.monitor import get_virtual_screen
                vx, vy, vw, vh = get_virtual_screen()
                mapper.monitor_rect = (vx, vy, vw, vh)

        self.apply_btn.clicked.connect(apply)

    def toggle(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()


def create_settings(app, cfg, mapper, engine, osctrl, monitors):
    win = SettingsWindow(cfg, mapper, engine, osctrl, monitors)
    return win
