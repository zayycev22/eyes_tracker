import time

from aiortc import MediaStreamTrack
from av import VideoFrame

from gaze_tracking import GazeTracking


class EyesTracker(MediaStreamTrack):
    """
    MediaStreamTrack который контролирует глаза.
    """

    kind = "video"

    def __init__(self, track: MediaStreamTrack):
        super().__init__()
        self.track = track
        self.gaze = GazeTracking()
        self.last_processed = 0

    async def recv(self):
        frame = await self.track.recv()
        now = time.time()
        if now - self.last_processed < 1 / 15:
            return frame
        self.gaze.refresh(frame.to_ndarray(format="bgr24"))
        img = self.gaze.annotated_frame()
        new_frame = VideoFrame.from_ndarray(img, format="bgr24")
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base
        return new_frame
