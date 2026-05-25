import math
from .base_calc import BaseCalculator


class SamplingCalculator(BaseCalculator):
    category = "deepsky"

    def __init__(self):
        super().__init__()
        self.inputs = {
            "focal_length": 500,
            "aperture": 5.6,
            "pixel_size": 4.3,
        }

    def calculate(self):
        fl = self.inputs["focal_length"]
        ap = self.inputs["aperture"]
        ps = self.inputs["pixel_size"]

        if fl <= 0 or ap <= 0 or ps <= 0:
            self.results = {"error": "参数必须为正数"}
            return

        aperture_diameter = fl / ap
        pixel_scale = (ps / fl) * 206.265
        dawes_limit = 116 / aperture_diameter
        sampling_ratio = pixel_scale / dawes_limit

        if sampling_ratio > 1:
            status_key = "undersampled"
        elif sampling_ratio < 0.5:
            status_key = "oversampled"
        else:
            status_key = "optimal"

        self.results = {
            "pixel_scale": pixel_scale,
            "dawes_limit": dawes_limit,
            "sampling_ratio": sampling_ratio,
            "status_key": status_key,
        }
