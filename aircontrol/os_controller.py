import pyautogui
import ctypes


class OSController:
    def __init__(self, use_win32=False):
        pyautogui.FAILSAFE = False
        self.use_win32 = use_win32

    def move_to(self, x, y):
        if self.use_win32:
            ctypes.windll.user32.SetCursorPos(int(x), int(y))
        else:
            pyautogui.moveTo(x, y, duration=0)

    def click(self):
        pyautogui.click()

    def double_click(self):
        pyautogui.doubleClick()

    def right_click(self):
        pyautogui.rightClick()

    def mouse_down(self):
        pyautogui.mouseDown()

    def mouse_up(self):
        pyautogui.mouseUp()

    def scroll(self, clicks):
        pyautogui.scroll(clicks)

    def screenshot(self, save_dir=""):
        import os
        from datetime import datetime
        if not save_dir:
            save_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        os.makedirs(save_dir, exist_ok=True)
        filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(save_dir, filename)
        img = pyautogui.screenshot()
        img.save(filepath)
        return filepath

    def zoom(self, delta, use_ctrl=True):
        """
        Zoom by simulating ctrl + scroll (Windows-friendly).
        Positive delta zooms in, negative zooms out.
        """
        if use_ctrl:
            pyautogui.keyDown("ctrl")
        try:
            pyautogui.scroll(delta)
        finally:
            if use_ctrl:
                pyautogui.keyUp("ctrl")

def get_screen_size():
    try:
        ctypes.windll.user32.SetProcessDPIAware()
        w = ctypes.windll.user32.GetSystemMetrics(0)
        h = ctypes.windll.user32.GetSystemMetrics(1)
        return w, h
    except Exception:
        return pyautogui.size()
