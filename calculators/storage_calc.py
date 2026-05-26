"""
存储空间需求计算器
根据单张图像大小(MB)和总张数计算所需总存储空间(GB)
"""


class StorageCalculator:
    def __init__(self):
        self.inputs = {
            "image_size": 50.0,
            "total_frames": 100,
        }
        self.results = {}

    def set_inputs(self, image_size, total_frames):
        self.inputs["image_size"] = image_size
        self.inputs["total_frames"] = total_frames

    def calculate(self):
        size = self.inputs["image_size"]
        frames = self.inputs["total_frames"]

        if size <= 0 or frames <= 0:
            self.results = {"error": "参数必须大于0"}
            return

        total_gb = size * frames / 1024

        self.results = {
            "total_gb": total_gb,
        }
