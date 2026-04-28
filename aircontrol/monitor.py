import ctypes


class MonitorInfo:
    def __init__(self, left, top, right, bottom, name):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
        self.width = right - left
        self.height = bottom - top
        self.name = name


def get_monitors():
    user32 = ctypes.windll.user32
    monitors = []

    MONITORINFOEXW = ctypes.create_unicode_buffer(40)
    LPMONITORINFOEXW = ctypes.c_void_p

    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

    class MONITORINFOEX(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.c_uint),
            ("rcMonitor", RECT),
            ("rcWork", RECT),
            ("dwFlags", ctypes.c_uint),
            ("szDevice", ctypes.c_wchar * 32),
        ]

    def callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
        info = MONITORINFOEX()
        info.cbSize = ctypes.sizeof(MONITORINFOEX)
        ctypes.windll.user32.GetMonitorInfoW(hMonitor, ctypes.byref(info))
        name = info.szDevice
        rect = info.rcMonitor
        monitors.append(MonitorInfo(rect.left, rect.top, rect.right, rect.bottom, name))
        return 1

    MONITORENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(RECT), ctypes.c_double)
    proc = MONITORENUMPROC(callback)
    user32.EnumDisplayMonitors(0, 0, proc, 0)
    return monitors


def get_virtual_screen():
    SM_XVIRTUALSCREEN = 76
    SM_YVIRTUALSCREEN = 77
    SM_CXVIRTUALSCREEN = 78
    SM_CYVIRTUALSCREEN = 79
    x = ctypes.windll.user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
    y = ctypes.windll.user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
    w = ctypes.windll.user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
    h = ctypes.windll.user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
    return x, y, w, h
