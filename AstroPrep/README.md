# AstroPrep - 天文摄影前期计算器

基于python tkinter开发的用于天文摄影前期工作的计算工具，帮助快速计算视场、曝光时间、采样率等关键参数。

## 功能

### 星野
- **单张曝光时间**：支持 500 法则、NPF 法则、简化 NPF 法则计算最长曝光时间

### 深空
- **视场/分辨率**：根据焦距、传感器尺寸、像素尺寸计算视场角、像素比例和分辨率
- **采样率匹配**：根据焦距、光圈、像素尺寸计算像素比例与道斯极限的采样比，判断过采样/适中/欠采样

### 行星
- （待添加）

## 使用

```bash
# pip
pip install ttkbootstrap
python main.py

# Anaconda
conda install -c conda-forge ttkbootstrap
python main.py

# uv
uv add ttkbootstrap
uv run python main.py
```

## 版本

0.0.1_260525_alpha

## 作者

SkylarLuo
