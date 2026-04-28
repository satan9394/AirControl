from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QFont


class TrailOverlay(QWidget):
    def __init__(self, rect, show_help=True, point_radius=3, line_width=4, skeleton_scale=0.6, point_glow=True):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setWindowOpacity(1.0)
        self.setGeometry(QRect(rect[0], rect[1], rect[2], rect[3]))
        self.trail = []
        self.cursor = None
        self.hand_pts = None
        self.hand_conns = None
        self.hand_list = []
        self.help_visible = show_help
        self.help_text = "手势: 单击=拇指+食指短闭合; 双击=拇指+食指/中指; 拖拽=长按; 右键=两指轻敲; 滚动=握拳上下; 菜单=张开手掌; 校准=OK"
        self.font = QFont("Segoe UI", 10)
        self.point_radius = point_radius
        self.line_width = line_width
        self.skeleton_scale = skeleton_scale
        self.point_glow = point_glow
        self.finger_colors = [
            QColor(255, 165, 0),   # 拇指: 橙
            QColor(30, 144, 255),  # 食指: 蓝
            QColor(50, 205, 50),   # 中指: 绿
            QColor(255, 215, 0),   # 无名指: 金
            QColor(186, 85, 211),  # 小指: 紫
        ]

    def update_trail(self, pts, cursor):
        self.trail = pts
        self.cursor = cursor
        self.update()

    def set_help_visible(self, visible):
        self.help_visible = visible
        self.update()

    def set_bounds(self, rect):
        self.setGeometry(QRect(rect[0], rect[1], rect[2], rect[3]))

    def update_hand(self, pts, connections):
        self.update_hands([(pts, connections)])

    def update_hands(self, hands):
        self.hand_list = hands or []
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        if self.trail and len(self.trail) > 1:
            n = len(self.trail)
            for i in range(1, n):
                hue = (i * 3) % 360
                c = QColor.fromHsl(hue, 200, 130)
                alpha = int(255 * (i / n))
                c.setAlpha(alpha)
                pen = QPen(c, 2)
                p.setPen(pen)
                p.drawLine(self.trail[i - 1][0], self.trail[i - 1][1], self.trail[i][0], self.trail[i][1])
        if self.cursor:
            c = QColor(255, 220, 0)
            pen = QPen(c, 2)
            p.setPen(pen)
            p.setBrush(c)
            p.drawEllipse(self.cursor[0] - 6, self.cursor[1] - 6, 12, 12)
        if self.hand_list:
            for pts, conns in self.hand_list:
                xs = [x for x, _ in pts]
                ys = [y for _, y in pts]
                cx = sum(xs) / len(xs)
                cy = sum(ys) / len(ys)
                scaled = [(int(cx + (x - cx) * self.skeleton_scale), int(cy + (y - cy) * self.skeleton_scale)) for (x, y) in pts]
                def grp(i):
                    if 1 <= i <= 4:
                        return 0
                    if 5 <= i <= 8:
                        return 1
                    if 9 <= i <= 12:
                        return 2
                    if 13 <= i <= 16:
                        return 3
                    if 17 <= i <= 20:
                        return 4
                    return -1
                for a, b in (conns or []):
                    pa = scaled[a]
                    pb = scaled[b]
                    g = grp(a)
                    if g == grp(b) and g >= 0:
                        c = self.finger_colors[g]
                    else:
                        c = QColor(255, 255, 255, 180)
                    pen = QPen(c, self.line_width)
                    p.setPen(pen)
                    p.drawLine(pa[0], pa[1], pb[0], pb[1])
                for i, (x, y) in enumerate(scaled):
                    g = grp(i)
                    c = self.finger_colors[g] if g >= 0 else QColor(255, 255, 255, 200)
                    p.setPen(QPen(c, 1))
                    p.setBrush(c)
                    r = self.point_radius
                    if self.point_glow:
                        glow = QColor(c)
                        glow.setAlpha(120)
                        p.setBrush(glow)
                        p.drawEllipse(x - r*2, y - r*2, r * 4, r * 4)
                        p.setBrush(c)
                    p.drawEllipse(x - r, y - r, r * 2, r * 2)
        elif self.hand_pts:
            xs = [x for x, _ in self.hand_pts]
            ys = [y for _, y in self.hand_pts]
            cx = sum(xs) / len(xs)
            cy = sum(ys) / len(ys)
            scaled = [(int(cx + (x - cx) * self.skeleton_scale), int(cy + (y - cy) * self.skeleton_scale)) for (x, y) in self.hand_pts]
            def grp(i):
                if 1 <= i <= 4:
                    return 0
                if 5 <= i <= 8:
                    return 1
                if 9 <= i <= 12:
                    return 2
                if 13 <= i <= 16:
                    return 3
                if 17 <= i <= 20:
                    return 4
                return -1
            for a, b in (self.hand_conns or []):
                pa = scaled[a]
                pb = scaled[b]
                g = grp(a)
                if g == grp(b) and g >= 0:
                    c = self.finger_colors[g]
                else:
                    c = QColor(255, 255, 255, 180)
                pen = QPen(c, self.line_width)
                p.setPen(pen)
                p.drawLine(pa[0], pa[1], pb[0], pb[1])
            for i, (x, y) in enumerate(scaled):
                g = grp(i)
                c = self.finger_colors[g] if g >= 0 else QColor(255, 255, 255, 200)
                p.setPen(QPen(c, 1))
                p.setBrush(c)
                r = self.point_radius
                if self.point_glow:
                    glow = QColor(c)
                    glow.setAlpha(120)
                    p.setBrush(glow)
                    p.drawEllipse(x - r*2, y - r*2, r * 4, r * 4)
                    p.setBrush(c)
                p.drawEllipse(x - r, y - r, r * 2, r * 2)
        if self.help_visible:
            p.setFont(self.font)
            p.setPen(QColor(255, 255, 255))
            bg = QColor(0, 0, 0, 160)
            p.fillRect(10, 10, 780, 40, bg)
            p.drawText(20, 38, self.help_text)