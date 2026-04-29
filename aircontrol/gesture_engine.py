import math
import time
import mediapipe as mp


class GestureEngine:
    def __init__(
        self,
        click_window_ms=250,
        double_click_window_ms=500,
        drag_hold_ms=200,
        pinch_thresh=0.05,
        right_tap_velocity=0.06,
        scroll_speed=60,
        menu_hold_ms=1000,
        screenshot_hold_ms=1000,
        refractory_ms=300,
    ):
        self.click_window_ms = click_window_ms
        self.double_click_window_ms = double_click_window_ms
        self.drag_hold_ms = drag_hold_ms
        self.pinch_thresh = pinch_thresh
        self.right_tap_velocity = right_tap_velocity
        self.scroll_speed = scroll_speed
        self.menu_hold_ms = menu_hold_ms
        self.screenshot_hold_ms = screenshot_hold_ms
        self.refractory_ms = refractory_ms
        self.pinch_active = False
        self.drag_active = False
        self.pinch_start_ms = 0
        self.last_click_ms = 0
        self.last_index_y = None
        self.last_right_tap_ms = 0
        self.scroll_last_y = None
        self.scroll_accum = 0.0
        self.mode = "move"
        self.menu_start_ms = 0
        self.calib_start_ms = 0
        self.screenshot_start_ms = 0
        self.screenshot_done = False
        self.dc_active = False
        self.dc_start_ms = 0
        self.right_tap_state = None

    def _dist(self, a, b):
        dx = a.x - b.x
        dy = a.y - b.y
        return math.hypot(dx, dy)

    def _extended(self, tip, pip):
        return tip.y < pip.y - 0.02

    def update(self, hand_landmarks, ts_ms):
        events = []
        lm = hand_landmarks.landmark
        thumb_tip = lm[mp.solutions.hands.HandLandmark.THUMB_TIP]
        thumb_ip = lm[mp.solutions.hands.HandLandmark.THUMB_IP]
        index_tip = lm[mp.solutions.hands.HandLandmark.INDEX_FINGER_TIP]
        index_pip = lm[mp.solutions.hands.HandLandmark.INDEX_FINGER_PIP]
        middle_tip = lm[mp.solutions.hands.HandLandmark.MIDDLE_FINGER_TIP]
        middle_pip = lm[mp.solutions.hands.HandLandmark.MIDDLE_FINGER_PIP]
        ring_tip = lm[mp.solutions.hands.HandLandmark.RING_FINGER_TIP]
        ring_pip = lm[mp.solutions.hands.HandLandmark.RING_FINGER_PIP]
        pinky_tip = lm[mp.solutions.hands.HandLandmark.PINKY_TIP]
        pinky_pip = lm[mp.solutions.hands.HandLandmark.PINKY_PIP]
        wrist = lm[mp.solutions.hands.HandLandmark.WRIST]

        pinch = self._dist(thumb_tip, index_tip) < self.pinch_thresh
        double_pinch = pinch and (self._dist(thumb_tip, middle_tip) < self.pinch_thresh)
        if pinch and not self.pinch_active:
            self.pinch_active = True
            self.pinch_start_ms = ts_ms
        if not pinch and self.pinch_active:
            hold = ts_ms - self.pinch_start_ms
            self.pinch_active = False
            if hold < self.drag_hold_ms and not self.drag_active:
                events.append("click")
                self.last_click_ms = ts_ms
            else:
                if self.drag_active:
                    events.append("drag_end")
                    self.drag_active = False
        if self.pinch_active and not self.drag_active:
            if ts_ms - self.pinch_start_ms >= self.drag_hold_ms:
                events.append("drag_start")
                self.drag_active = True

        if double_pinch and not self.dc_active and not self.drag_active:
            self.dc_active = True
            self.dc_start_ms = ts_ms
        if self.dc_active and not double_pinch:
            duration = ts_ms - self.dc_start_ms
            if 50 <= duration <= 350:
                events.append("double_click")
            self.dc_active = False

        two_extended = self._extended(index_tip, index_pip) and self._extended(middle_tip, middle_pip)
        others_curled = (not self._extended(ring_tip, ring_pip)) and (not self._extended(pinky_tip, pinky_pip))
        if two_extended and others_curled:
            if self.last_index_y is not None:
                vy = index_tip.y - self.last_index_y
                if self.right_tap_state is None and vy > self.right_tap_velocity:
                    self.right_tap_state = "down"
                elif self.right_tap_state == "down" and vy < -self.right_tap_velocity:
                    if ts_ms - self.last_right_tap_ms > self.refractory_ms:
                        events.append("right_click")
                        self.last_right_tap_ms = ts_ms
                    self.right_tap_state = None
            self.last_index_y = index_tip.y
        else:
            self.last_index_y = None
            self.right_tap_state = None

        none_extended = (
            (not self._extended(index_tip, index_pip))
            and (not self._extended(middle_tip, middle_pip))
            and (not self._extended(ring_tip, ring_pip))
            and (not self._extended(pinky_tip, pinky_pip))
        )
        if none_extended:
            y = wrist.y
            if self.scroll_last_y is not None:
                dy = y - self.scroll_last_y
                self.scroll_accum += dy
                threshold = 0.01
                if abs(self.scroll_accum) > threshold:
                    clicks = int(-self.scroll_accum * self.scroll_speed)
                    if clicks != 0:
                        events.append(("scroll", clicks))
                        self.scroll_accum = 0.0
            self.scroll_last_y = y
        else:
            self.scroll_last_y = None
            self.scroll_accum = 0.0

        open_palm = (
            self._extended(index_tip, index_pip)
            and self._extended(middle_tip, middle_pip)
            and self._extended(ring_tip, ring_pip)
            and self._extended(pinky_tip, pinky_pip)
        )
        if open_palm and not pinch:
            if self.menu_start_ms == 0:
                self.menu_start_ms = ts_ms
            elif ts_ms - self.menu_start_ms >= self.menu_hold_ms:
                events.append("menu")
                self.mode = "menu"
        else:
            self.menu_start_ms = 0

        ok_pose = pinch and self._extended(middle_tip, middle_pip) and self._extended(ring_tip, ring_pip) and self._extended(pinky_tip, pinky_pip)
        if ok_pose:
            if self.calib_start_ms == 0:
                self.calib_start_ms = ts_ms
            elif ts_ms - self.calib_start_ms >= self.menu_hold_ms:
                events.append("calibrate")
        else:
            self.calib_start_ms = 0

        three_fingers = (
            self._extended(index_tip, index_pip)
            and self._extended(middle_tip, middle_pip)
            and self._extended(ring_tip, ring_pip)
            and not self._extended(pinky_tip, pinky_pip)
        )
        if three_fingers:
            if self.screenshot_start_ms == 0 and not self.screenshot_done:
                self.screenshot_start_ms = ts_ms
            elif ts_ms - self.screenshot_start_ms >= self.screenshot_hold_ms and not self.screenshot_done:
                events.append("screenshot")
                self.mode = "screenshot"
                self.screenshot_start_ms = 0
                self.screenshot_done = True
        else:
            self.screenshot_start_ms = 0
            self.screenshot_done = False

        if self.drag_active:
            self.mode = "drag"
        elif none_extended:
            self.mode = "scroll"
        elif pinch:
            self.mode = "click"
        else:
            if self.mode not in ("menu", "screenshot"):
                self.mode = "move"

        return events
