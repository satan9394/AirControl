import cv2


class Camera:
    def __init__(self, index=0, width=None, height=None):
        self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if width is not None:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        if height is not None:
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def read(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def release(self):
        if self.cap:
            self.cap.release()
