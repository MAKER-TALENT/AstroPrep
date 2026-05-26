"""
靶面尺寸可视化计算器
用 matplotlib 嵌入主窗口绘制传感器尺寸对比图
"""

import json
import os
import sys

def _sensors_path():
    try:
        base = sys._MEIPASS
    except AttributeError:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "sensors.json")


def load_sensors():
    path = _sensors_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}


def save_sensors(data):
    try:
        with open(_sensors_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"保存传感器数据失败: {e}")


class SensorCalculator:
    def __init__(self):
        self.inputs = {
            "sensor_width": 36.0,
            "sensor_height": 24.0,
        }
        self.results = {}

    def set_inputs(self, sensor_width, sensor_height):
        self.inputs["sensor_width"] = sensor_width
        self.inputs["sensor_height"] = sensor_height
