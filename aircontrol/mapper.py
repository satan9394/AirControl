import math


class OneEuro:
    def __init__(self, min_cutoff=1.0, beta=0.0, d_cutoff=1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_prev = None
        self.dx_prev = 0.0
        self.t_prev = None

    def _alpha(self, cutoff, dt):
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt) if dt > 0 else 1.0

    def filter(self, t_ms, x):
        if self.t_prev is None:
            self.t_prev = t_ms
            self.x_prev = x
            return x
        dt = max((t_ms - self.t_prev) / 1000.0, 1e-3)
        dx = x - self.x_prev
        a_d = self._alpha(self.d_cutoff, dt)
        dx_hat = a_d * dx + (1 - a_d) * self.dx_prev
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        a = self._alpha(cutoff, dt)
        x_hat = a * x + (1 - a) * self.x_prev
        self.t_prev = t_ms
        self.dx_prev = dx_hat
        self.x_prev = x_hat
        return x_hat


class CoordinateMapper:
    def __init__(self, screen_size, alpha=0.4, deadzone=(0.04, 0.04), roi_size=(1.0, 1.0), mirror_x=False, min_cutoff=1.5, beta=0.4, d_cutoff=1.0, gain=1.0, monitor_rect=None, mirror_y=False, vel_gain=0.8, vel_clip=3.0):
        self.screen_w, self.screen_h = screen_size
        self.alpha = alpha
        self.prev = None
        self.deadzone_x, self.deadzone_y = deadzone
        self.roi_cx, self.roi_cy = 0.5, 0.5
        self.roi_w, self.roi_h = roi_size
        self.mirror_x = mirror_x
        self.mirror_y = mirror_y
        self.filter_x = OneEuro(min_cutoff, beta, d_cutoff)
        self.filter_y = OneEuro(min_cutoff, beta, d_cutoff)
        self.gain = gain
        self.monitor_rect = monitor_rect
        self.prev_norm = None
        self.vel_gain = vel_gain
        self.vel_clip = vel_clip

    def update_roi(self, center, size):
        self.roi_cx, self.roi_cy = center
        self.roi_w, self.roi_h = size

    def _apply_roi_deadzone(self, x, y):
        x = 1.0 - x if self.mirror_x else x
        y = 1.0 - y if self.mirror_y else y
        rx = max(self.roi_cx - self.roi_w / 2.0, 0.0)
        ry = max(self.roi_cy - self.roi_h / 2.0, 0.0)
        rxe = min(self.roi_cx + self.roi_w / 2.0, 1.0)
        rye = min(self.roi_cy + self.roi_h / 2.0, 1.0)
        x = min(max(x, rx + self.deadzone_x), rxe - self.deadzone_x)
        y = min(max(y, ry + self.deadzone_y), rye - self.deadzone_y)
        nx = (x - rx) / max(rxe - rx, 1e-6)
        ny = (y - ry) / max(rye - ry, 1e-6)
        return nx, ny

    def map(self, norm_xy, t_ms):
        nx, ny = self._apply_roi_deadzone(norm_xy[0], norm_xy[1])
        fx = self.filter_x.filter(t_ms, nx)
        fy = self.filter_y.filter(t_ms, ny)
        if self.prev_norm is not None:
            dt = max((t_ms - self.filter_x.t_prev), 1e-3)
            vx = (nx - self.prev_norm[0]) / (dt / 1000.0)
            vy = (ny - self.prev_norm[1]) / (dt / 1000.0)
            speed = min((vx * vx + vy * vy) ** 0.5, self.vel_clip)
        else:
            speed = 0.0
        eff_gain = self.gain * (1.0 + self.vel_gain * speed)
        fx = min(max(fx * eff_gain, 0.0), 1.0)
        fy = min(max(fy * eff_gain, 0.0), 1.0)
        self.prev_norm = (nx, ny)
        if self.monitor_rect:
            left, top, width, height = self.monitor_rect
            x = int(left + fx * width)
            y = int(top + fy * height)
        else:
            x = int(fx * self.screen_w)
            y = int(fy * self.screen_h)
        return x, y

    def to_screen_unfiltered(self, norm_xy):
        nx, ny = self._apply_roi_deadzone(norm_xy[0], norm_xy[1])
        nx = min(max(nx * self.gain, 0.0), 1.0)
        ny = min(max(ny * self.gain, 0.0), 1.0)
        if self.monitor_rect:
            left, top, width, height = self.monitor_rect
            x = int(left + nx * width)
            y = int(top + ny * height)
        else:
            x = int(nx * self.screen_w)
            y = int(ny * self.screen_h)
        return x, y
