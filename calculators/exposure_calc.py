import math
from .base_calc import BaseCalculator


class ExposureCalculator(BaseCalculator):
    category = "starscape"

    def __init__(self):
        super().__init__()
        self.inputs = {
            "focal_length": 24,
            "aperture": 2.8,
            "pixel_size": 4.3,
            "crop_factor": 1.0,
            "rule": "500 Rule",
        }

    def calculate(self):
        fl = self.inputs["focal_length"]
        ap = self.inputs["aperture"]
        ps = self.inputs["pixel_size"]
        cf = self.inputs["crop_factor"]
        rule = self.inputs["rule"]

        if fl <= 0 or ap <= 0 or ps <= 0 or cf <= 0:
            self.results = {"error": "参数必须为正数"}
            return

        effective_fl = fl * cf

        if rule == "500 Rule":
            max_time = 500 / effective_fl
            detail = f"500 / (焦距 × 裁切系数) = 500 / ({fl} × {cf})"
        elif rule == "NPF Rule":
            max_time = (35 * ap + 30 * ps) / effective_fl
            detail = f"(35×光圈 + 30×像素尺寸) / (焦距×裁切系数)"
        elif rule == "Simplified NPF":
            max_time = (35 * ap + 30 * ps - ps * ap / 10) / effective_fl
            detail = f"简化 NPF 法则"
        else:
            self.results = {"error": f"未知法则: {rule}"}
            return

        self.results = {
            "max_time": max_time,
            "detail": detail,
        }
