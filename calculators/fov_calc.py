import math
from .base_calc import BaseCalculator


class FOVCalculator(BaseCalculator):
    category = "deepsky"

    def __init__(self):
        super().__init__()
        self.inputs = {
            "focal_length": 500,
            "sensor_width": 22.3,
            "sensor_height": 14.9,
            "pixel_size": 4.3,
            "binning": 1,
        }

    def calculate(self):
        fl = self.inputs["focal_length"]
        sw = self.inputs["sensor_width"]
        sh = self.inputs["sensor_height"]
        ps = self.inputs["pixel_size"]
        binning = self.inputs["binning"]

        if fl <= 0 or sw <= 0 or sh <= 0 or ps <= 0:
            self.results = {"error": "参数必须为正数"}
            return

        fov_h = 2 * math.degrees(math.atan(sw / (2 * fl)))
        fov_v = 2 * math.degrees(math.atan(sh / (2 * fl)))
        fov_d = 2 * math.degrees(math.atan(math.hypot(sw, sh) / (2 * fl)))
        pixel_scale = (ps * binning / fl) * 206.265
        resolution = ps / pixel_scale

        self.results = {
            "fov_h": fov_h,
            "fov_v": fov_v,
            "fov_d": fov_d,
            "pixel_scale": pixel_scale,
            "resolution": resolution,
        }
