# AstroPrep – 天文摄影前期规划与计算工具

用于天文摄影前期工作的计算工具，为器材选购、拍摄规划提供参考。

## 功能

- **视场/分辨率**：根据焦距、传感器尺寸、像素尺寸计算视场角、像素比例和分辨率
- **采样率匹配**：根据焦距、光圈、像素尺寸计算像素比例与道斯极限的采样比，判断过采样/适中/欠采样
- **单张曝光时间**：支持 500 法则、NPF 法则、简化 NPF 法则计算最长曝光时间
- **靶面尺寸可视化**：选择多个传感器进行尺寸对比显示
- **存储空间需求**：根据单张大小和总张数计算存储需求
- **传感器/镜头列表**：内置常见传感器和镜头数据，支持自定义编辑
- **多语言支持**：中文 / English
- **主题切换**：支持多种 ttkbootstrap 主题

## 使用

### 直接运行

从 Releases下载最新版 `AstroPrep.exe` 直接运行，无需安装 Python。

### 源码运行

```bash
# uv（推荐）
uv sync
uv run python main.py

# pip
pip install ttkbootstrap matplotlib
python main.py
```

## 打包

```bash
uv add pyinstaller
uv run pyinstaller --onefile --windowed --icon=icon.ico --name=AstroPrep --add-data "locales;locales" --add-data "icon.ico;." --add-data "sensors.json;." --add-data "lenses.json;." main.py
```

打包产物在 `dist/AstroPrep.exe`，可直接分发运行。

## 更新日志

### v0.0.1.260525_alpha

- 软件基础框架实现

### v0.1.0.260526

- 新增靶面尺寸可视化功能
- 新增存储空间需求计算器
- 新增传感器/镜头列表编辑器
- 新增从传感器/镜头数据快速输入
- 修复了一些bug
- 优化 UI 布局和交互体验


## 作者

SkylarLuo
