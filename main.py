"""
AstroPrep - 天文摄影前期计算器
主界面程序，使用独立的计算器模块
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import json
import os
import sys
from tkinter import filedialog, messagebox
import tkinter as tk

from calculators.fov_calc import FOVCalculator
from calculators.exposure_calc import ExposureCalculator
from calculators.sampling_calc import SamplingCalculator
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from calculators.sensor_calc import SensorCalculator, load_sensors, save_sensors
from calculators.storage_calc import StorageCalculator

SETTINGS_FILE = "astro_settings.json"
LENSES_FILE = "lenses.json"


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def load_lenses():
    path = resource_path(LENSES_FILE)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}


def save_lenses(data):
    try:
        with open(LENSES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"保存镜头数据失败: {e}")

_locales_cache = {}

def load_locale(lang):
    path = resource_path(os.path.join("locales", f"{lang}.json"))
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def tr(key, lang):
    if lang not in _locales_cache:
        _locales_cache[lang] = load_locale(lang)
    return _locales_cache[lang].get(key, key)

ALL_CALCULATORS = [
    ("tab_fov", FOVCalculator),
    ("tab_sampling", SamplingCalculator),
    ("tab_sensor", SensorCalculator),
    ("tab_exposure", ExposureCalculator),
    ("tab_storage", StorageCalculator),
]


class MainApplication(ttk.Window):
    def __init__(self):
        self.app_settings = self.load_settings()
        init_theme = self.app_settings.get("theme", "darkly")
        self.lang = self.app_settings.get("lang", "zh")
        self.font_size = self.app_settings.get("font_size", 10)

        super().__init__(themename=init_theme)
        self.title(tr("app_title", self.lang))
        try:
            self.iconbitmap("icon.ico")
        except:
            pass

        win_size = self.app_settings.get("window_size", "750x600")
        self.geometry(win_size)
        self.resizable(True, True)

        self.tab_pages = []

        self._create_menu()
        self._build_notebook()

        self.bind("<Destroy>", self._on_destroy)

    def _create_menu(self):
        menubar = ttk.Menu(self)

        output_menu = ttk.Menu(menubar, tearoff=False)
        output_menu.add_command(label=tr("menu_export", self.lang),
                                command=self.export_current_calculation)
        menubar.add_cascade(label=tr("menu_output", self.lang), menu=output_menu)

        view_menu = ttk.Menu(menubar, tearoff=False)

        theme_menu = ttk.Menu(view_menu, tearoff=False)
        themes = ttk.Style().theme_names()
        self.theme_var = ttk.StringVar(value=self.app_settings.get("theme", "darkly"))
        for theme in themes:
            theme_menu.add_radiobutton(label=theme, variable=self.theme_var,
                                       value=theme, command=lambda t=theme: self.change_theme(t))
        view_menu.add_cascade(label=tr("menu_theme", self.lang), menu=theme_menu)

        font_menu = ttk.Menu(view_menu, tearoff=False)
        self.font_size_var = ttk.IntVar(value=self.font_size)
        font_menu.add_radiobutton(label=tr("font_small", self.lang), variable=self.font_size_var,
                                  value=8, command=lambda: self.set_font_size(8))
        font_menu.add_radiobutton(label=tr("font_medium", self.lang), variable=self.font_size_var,
                                  value=10, command=lambda: self.set_font_size(10))
        font_menu.add_radiobutton(label=tr("font_large", self.lang), variable=self.font_size_var,
                                  value=12, command=lambda: self.set_font_size(12))
        view_menu.add_cascade(label=tr("menu_font_size", self.lang), menu=font_menu)

        lang_menu = ttk.Menu(view_menu, tearoff=False)
        self.lang_var = ttk.StringVar(value=self.lang)
        lang_menu.add_radiobutton(label=tr("lang_zh", self.lang), variable=self.lang_var,
                                  value="zh", command=lambda: self.set_language("zh"))
        lang_menu.add_radiobutton(label=tr("lang_en", self.lang), variable=self.lang_var,
                                  value="en", command=lambda: self.set_language("en"))
        view_menu.add_cascade(label=tr("menu_lang", self.lang), menu=lang_menu)

        menubar.add_cascade(label=tr("menu_ui", self.lang), menu=view_menu)

        calc_menu = ttk.Menu(menubar, tearoff=False)
        for label_key, calc_class in ALL_CALCULATORS:
            if calc_class is not None:
                calc_menu.add_command(
                    label=tr(label_key, self.lang),
                    command=lambda lk=label_key, cc=calc_class: self.switch_tab(lk, cc)
                )
            else:
                calc_menu.add_command(
                    label=tr(label_key, self.lang),
                    command=lambda lk=label_key: self.show_placeholder(lk)
                )
        menubar.add_cascade(label=tr("menu_calc", self.lang), menu=calc_menu)

        settings_menu = ttk.Menu(menubar, tearoff=False)
        settings_menu.add_command(label=tr("menu_sensor_list", self.lang),
                                  command=self.show_sensor_editor)
        settings_menu.add_command(label=tr("menu_lens_list", self.lang),
                                  command=self.show_lens_editor)
        menubar.add_cascade(label=tr("menu_settings", self.lang), menu=settings_menu)

        about_menu = ttk.Menu(menubar, tearoff=False)
        about_menu.add_command(label=tr("menu_about", self.lang), command=self.show_about)
        menubar.add_cascade(label=tr("menu_about", self.lang), menu=about_menu)

        self.config(menu=menubar)

    def switch_tab(self, label_key, calc_class):
        for i, (lk, _, cc, _, _) in enumerate(self.tab_pages):
            if lk == label_key and type(cc) is type(calc_class()):
                self.notebook.select(i)
                return
        self._add_tab(label_key, calc_class)
        self.notebook.select(len(self.tab_pages) - 1)

    def show_placeholder(self, label_key):
        messagebox.showinfo(tr(label_key, self.lang), tr("placeholder_msg", self.lang))

    def _build_notebook(self):
        if hasattr(self, 'notebook'):
            self.notebook.destroy()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=BOTH, expand=YES, padx=10, pady=10)
        self.tab_pages.clear()

        if self.notebook.tabs():
            self.notebook.select(0)

    def _add_tab(self, label_key, calc_class):
        if not self.tab_pages:
            self.notebook.pack(fill=BOTH, expand=YES, padx=10, pady=10)

        frame = ttk.Frame(self.notebook)
        calc = calc_class()

        top_bar = ttk.Frame(frame)
        top_bar.pack(fill=X, padx=5, pady=(5, 0))
        close_btn = ttk.Button(top_bar, text=tr("close_tab", self.lang), padding=(4, 0),
                               command=self._close_current_tab)
        close_btn.pack(side=RIGHT)

        if isinstance(calc, FOVCalculator):
            self._build_fov_ui(frame, calc, label_key)
        elif isinstance(calc, ExposureCalculator):
            self._build_exposure_ui(frame, calc, label_key)
        elif isinstance(calc, SamplingCalculator):
            self._build_sampling_ui(frame, calc, label_key)
        elif isinstance(calc, SensorCalculator):
            self._build_sensor_ui(frame, calc, label_key)
        elif isinstance(calc, StorageCalculator):
            self._build_storage_ui(frame, calc, label_key)

        self._set_widget_font(frame, self.font_size)

        self.notebook.add(frame, text=tr(label_key, self.lang))

    def _close_current_tab(self):
        idx = self.notebook.index(self.notebook.select())
        if idx is None:
            return
        self.notebook.forget(idx)
        del self.tab_pages[idx]
        if not self.tab_pages:
            self.notebook.pack_forget()

    def _pick_sensor(self, entries, keys):
        sensors = load_sensors()
        if not sensors:
            return
        win = tk.Toplevel(self)
        win.title(tr("sensor_pick_title", self.lang))
        win.transient(self)
        win.grab_set()
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 400) // 2
        y = self.winfo_y() + (self.winfo_height() - 350) // 2
        win.geometry(f"400x350+{x}+{y}")

        listbox = tk.Listbox(win, selectmode=SINGLE)
        listbox.pack(fill=BOTH, expand=YES, padx=10, pady=10)
        for k, (w, h, p) in sensors.items():
            listbox.insert(END, f"{k}  ({w:.1f}x{h:.1f}mm, {p:.2f}μm)")

        def confirm():
            sel = listbox.curselection()
            if not sel:
                return
            text = listbox.get(sel[0])
            name = text.split("  (")[0]
            data = sensors[name]
            if "sensor_width" in keys:
                entries["sensor_width"].set(str(data[0]))
            if "sensor_height" in keys:
                entries["sensor_height"].set(str(data[1]))
            if "pixel_size" in keys:
                entries["pixel_size"].set(str(data[2]))
            win.destroy()

        ttk.Button(win, text=tr("sensor_pick_confirm", self.lang),
                   command=confirm).pack(pady=(0, 10))

    def _pick_lens(self, entries, keys):
        lenses = load_lenses()
        if not lenses:
            return
        win = tk.Toplevel(self)
        win.title(tr("lens_pick_title", self.lang))
        win.transient(self)
        win.grab_set()
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 400) // 2
        y = self.winfo_y() + (self.winfo_height() - 350) // 2
        win.geometry(f"400x350+{x}+{y}")

        listbox = tk.Listbox(win, selectmode=SINGLE)
        listbox.pack(fill=BOTH, expand=YES, padx=10, pady=10)
        for k, (fl, ap) in lenses.items():
            listbox.insert(END, f"{k}  ({fl}mm, f/{ap})")

        def confirm():
            sel = listbox.curselection()
            if not sel:
                return
            text = listbox.get(sel[0])
            name = text.split("  (")[0]
            data = lenses[name]
            if "focal_length" in keys:
                entries["focal_length"].set(str(data[0]))
            if "aperture" in keys:
                entries["aperture"].set(str(data[1]))
            win.destroy()

        ttk.Button(win, text=tr("sensor_pick_confirm", self.lang),
                   command=confirm).pack(pady=(0, 10))

    def _build_fov_ui(self, frame, calc, label_key):
        input_frame = ttk.Labelframe(frame, text=tr("fov_title_input", self.lang), padding=15)
        input_frame.pack(fill=X, padx=10, pady=10)

        fields = [
            ("fov_label_fl", "focal_length"),
            ("fov_label_sw", "sensor_width"),
            ("fov_label_sh", "sensor_height"),
            ("fov_label_ps", "pixel_size"),
            ("fov_label_bin", "binning"),
        ]
        entries = {}
        for i, (label_key, input_key) in enumerate(fields):
            ttk.Label(input_frame, text=tr(label_key, self.lang)).grid(row=i, column=0, sticky=W, pady=5)
            var = ttk.StringVar(value=str(calc.inputs[input_key]))
            entry = ttk.Entry(input_frame, textvariable=var, width=15)
            entry.grid(row=i, column=1, padx=(10, 0), pady=5, sticky=W)
            entries[input_key] = var

        lens_btn = ttk.Button(input_frame, text=tr("lens_pick_btn", self.lang),
                              command=lambda: self._pick_lens(entries, ["focal_length"]))
        lens_btn.grid(row=0, column=2, padx=(10, 0), sticky=W)
        sensor_btn = ttk.Button(input_frame, text=tr("sensor_pick_btn", self.lang),
                                command=lambda: self._pick_sensor(entries, ["sensor_width", "sensor_height", "pixel_size"]))
        sensor_btn.grid(row=1, column=2, padx=(10, 0), sticky=W)

        output_vars = {
            "fov_h": ttk.StringVar(value="---"),
            "fov_v": ttk.StringVar(value="---"),
            "fov_d": ttk.StringVar(value="---"),
            "pixel_scale": ttk.StringVar(value="---"),
            "resolution": ttk.StringVar(value="---"),
        }

        calc_btn = ttk.Button(input_frame, text=tr("fov_btn_calc", self.lang),
                              bootstyle=PRIMARY, command=lambda c=calc: self._fov_calculate(c, entries, output_vars))
        calc_btn.grid(row=len(fields), column=0, columnspan=2, pady=10)

        output_frame = ttk.Labelframe(frame, text=tr("fov_title_output", self.lang), padding=15)
        output_frame.pack(fill=X, padx=10, pady=10)

        result_labels = [
            ("fov_result_h", output_vars["fov_h"]),
            ("fov_result_v", output_vars["fov_v"]),
            ("fov_result_d", output_vars["fov_d"]),
            ("fov_result_scale", output_vars["pixel_scale"]),
            ("fov_result_res", output_vars["resolution"]),
        ]
        for i, (label_key, var) in enumerate(result_labels):
            ttk.Label(output_frame, text=tr(label_key, self.lang)).grid(row=i, column=0, sticky=W, pady=3)
            ttk.Label(output_frame, textvariable=var, foreground="#0072B5").grid(
                row=i, column=1, sticky=W, padx=(20, 0), pady=3)

        self.tab_pages.append((label_key, frame, calc, entries, output_vars))

    def _fov_calculate(self, calc, entries, output_vars):
        try:
            calc.set_inputs(
                focal_length=float(entries["focal_length"].get()),
                sensor_width=float(entries["sensor_width"].get()),
                sensor_height=float(entries["sensor_height"].get()),
                pixel_size=float(entries["pixel_size"].get()),
                binning=int(entries["binning"].get())
            )
            calc.calculate()
            res = calc.results
            if "error" in res:
                raise ValueError(res["error"])
            output_vars["fov_h"].set(f"{res['fov_h']:.2f}°")
            output_vars["fov_v"].set(f"{res['fov_v']:.2f}°")
            output_vars["fov_d"].set(f"{res['fov_d']:.2f}°")
            output_vars["pixel_scale"].set(f"{res['pixel_scale']:.2f} arcsec/px")
            output_vars["resolution"].set(f"{res['resolution']:.2f} μm/arcsec")
        except Exception as e:
            output_vars["fov_h"].set("Error")
            output_vars["fov_v"].set("Error")
            output_vars["fov_d"].set("Error")
            output_vars["pixel_scale"].set("Error")
            output_vars["resolution"].set(str(e))

    def _build_exposure_ui(self, frame, calc, label_key):
        lang = self.lang
        input_frame = ttk.Labelframe(frame, text=tr("exp_title_input", lang), padding=15)
        input_frame.pack(fill=X, padx=10, pady=10)

        fields = [
            ("exp_label_fl", "focal_length"),
            ("exp_label_ap", "aperture"),
            ("exp_label_ps", "pixel_size"),
            ("exp_label_cf", "crop_factor"),
        ]
        entries = {}
        for i, (label_key, input_key) in enumerate(fields):
            ttk.Label(input_frame, text=tr(label_key, lang)).grid(row=i, column=0, sticky=W, pady=5)
            var = ttk.StringVar(value=str(calc.inputs[input_key]))
            entry = ttk.Entry(input_frame, textvariable=var, width=15)
            entry.grid(row=i, column=1, padx=(10, 0), pady=5, sticky=W)
            entries[input_key] = var

        lens_btn = ttk.Button(input_frame, text=tr("lens_pick_btn", self.lang),
                              command=lambda: self._pick_lens(entries, ["focal_length", "aperture"]))
        lens_btn.grid(row=0, column=2, padx=(10, 0), sticky=W)
        sensor_btn = ttk.Button(input_frame, text=tr("sensor_pick_btn", self.lang),
                                command=lambda: self._pick_sensor(entries, ["pixel_size"]))
        sensor_btn.grid(row=1, column=2, padx=(10, 0), sticky=W)

        ttk.Label(input_frame, text=tr("exp_label_rule", lang)).grid(row=len(fields), column=0, sticky=W, pady=5)
        rules = tr("exp_rules", lang)
        if not rules:
            rules = ["500 Rule", "NPF Rule", "Simplified NPF"]
        rule_var = ttk.StringVar(value=rules[0])
        rule_combo = ttk.Combobox(input_frame, textvariable=rule_var, values=rules, state="readonly", width=15)
        rule_combo.grid(row=len(fields), column=1, padx=(10, 0), pady=5, sticky=W)
        entries["rule"] = rule_var

        output_vars = {
            "max_time": ttk.StringVar(value="---"),
            "detail": ttk.StringVar(value=""),
        }

        calc_btn = ttk.Button(input_frame, text=tr("fov_btn_calc", lang),
                              bootstyle=PRIMARY, command=lambda c=calc: self._exp_calculate(c, entries, output_vars))
        calc_btn.grid(row=len(fields)+1, column=0, columnspan=2, pady=10)

        output_frame = ttk.Labelframe(frame, text=tr("exp_title_output", lang), padding=15)
        output_frame.pack(fill=X, padx=10, pady=10)

        ttk.Label(output_frame, text=tr("exp_result_max", lang)).pack(anchor=W)
        ttk.Label(output_frame, textvariable=output_vars["max_time"],
                  font=("", 12, "bold"), foreground="#D93B3B").pack(anchor=W, pady=5)
        ttk.Label(output_frame, textvariable=output_vars["detail"], wraplength=350).pack(anchor=W)

        self.tab_pages.append((label_key, frame, calc, entries, output_vars))

    def _exp_calculate(self, calc, entries, output_vars):
        try:
            calc.set_inputs(
                focal_length=float(entries["focal_length"].get()),
                aperture=float(entries["aperture"].get()),
                pixel_size=float(entries["pixel_size"].get()),
                crop_factor=float(entries["crop_factor"].get()),
                rule=entries["rule"].get()
            )
            calc.calculate()
            res = calc.results
            if "error" in res:
                raise ValueError(res["error"])
            output_vars["max_time"].set(f"{res['max_time']:.1f} s")
            output_vars["detail"].set(res["detail"])
        except Exception as e:
            output_vars["max_time"].set("Error")
            output_vars["detail"].set(str(e))

    def _build_sampling_ui(self, frame, calc, label_key):
        input_frame = ttk.Labelframe(frame, text=tr("sampling_title_input", self.lang), padding=15)
        input_frame.pack(fill=X, padx=10, pady=10)

        fields = [
            ("sampling_label_fl", "focal_length"),
            ("sampling_label_ap", "aperture"),
            ("sampling_label_ps", "pixel_size"),
        ]
        entries = {}
        for i, (label_key, input_key) in enumerate(fields):
            ttk.Label(input_frame, text=tr(label_key, self.lang)).grid(row=i, column=0, sticky=W, pady=5)
            var = ttk.StringVar(value=str(calc.inputs[input_key]))
            entry = ttk.Entry(input_frame, textvariable=var, width=15)
            entry.grid(row=i, column=1, padx=(10, 0), pady=5, sticky=W)
            entries[input_key] = var

        lens_btn = ttk.Button(input_frame, text=tr("lens_pick_btn", self.lang),
                              command=lambda: self._pick_lens(entries, ["focal_length", "aperture"]))
        lens_btn.grid(row=0, column=2, padx=(10, 0), sticky=W)
        sensor_btn = ttk.Button(input_frame, text=tr("sensor_pick_btn", self.lang),
                                command=lambda: self._pick_sensor(entries, ["pixel_size"]))
        sensor_btn.grid(row=1, column=2, padx=(10, 0), sticky=W)

        output_vars = {
            "pixel_scale": ttk.StringVar(value="---"),
            "dawes_limit": ttk.StringVar(value="---"),
            "sampling_ratio": ttk.StringVar(value="---"),
            "status": ttk.StringVar(value="---"),
        }

        calc_btn = ttk.Button(input_frame, text=tr("fov_btn_calc", self.lang),
                              bootstyle=PRIMARY, command=lambda c=calc: self._sampling_calculate(c, entries, output_vars))
        calc_btn.grid(row=len(fields), column=0, columnspan=2, pady=10)

        output_frame = ttk.Labelframe(frame, text=tr("sampling_title_output", self.lang), padding=15)
        output_frame.pack(fill=X, padx=10, pady=10)

        result_labels = [
            ("sampling_result_scale", output_vars["pixel_scale"]),
            ("sampling_result_dawes", output_vars["dawes_limit"]),
            ("sampling_result_ratio", output_vars["sampling_ratio"]),
            ("sampling_result_status", output_vars["status"]),
        ]
        for i, (label_key, var) in enumerate(result_labels):
            ttk.Label(output_frame, text=tr(label_key, self.lang)).grid(row=i, column=0, sticky=W, pady=3)
            ttk.Label(output_frame, textvariable=var, foreground="#0072B5").grid(
                row=i, column=1, sticky=W, padx=(20, 0), pady=3)

        self.tab_pages.append((label_key, frame, calc, entries, output_vars))

    def _sampling_calculate(self, calc, entries, output_vars):
        try:
            calc.set_inputs(
                focal_length=float(entries["focal_length"].get()),
                aperture=float(entries["aperture"].get()),
                pixel_size=float(entries["pixel_size"].get()),
            )
            calc.calculate()
            res = calc.results
            if "error" in res:
                raise ValueError(res["error"])
            output_vars["pixel_scale"].set(f"{res['pixel_scale']:.2f} arcsec/px")
            output_vars["dawes_limit"].set(f"{res['dawes_limit']:.2f} arcsec")
            output_vars["sampling_ratio"].set(f"{res['sampling_ratio']:.2f}")
            status_key = f"sampling_status_{res['status_key']}"
            output_vars["status"].set(tr(status_key, self.lang))
        except Exception as e:
            output_vars["pixel_scale"].set("Error")
            output_vars["dawes_limit"].set("Error")
            output_vars["sampling_ratio"].set("Error")
            output_vars["status"].set(str(e))

    def _build_sensor_ui(self, frame, calc, label_key):
        top_frame = ttk.Frame(frame)
        top_frame.pack(fill=X, padx=10, pady=10)

        compare_frame = ttk.Labelframe(top_frame, text=tr("sensor_label_compare", self.lang), padding=10)
        compare_frame.pack(fill=X, expand=YES)

        canvas = tk.Canvas(compare_frame, height=150, highlightthickness=0)
        scrollbar = ttk.Scrollbar(compare_frame, orient=VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor=NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        canvas.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)

        sensors = load_sensors()
        self.sensor_vars = {}
        for k in sensors:
            var = ttk.BooleanVar(value=False)
            cb = ttk.Checkbutton(scrollable_frame, text=f"{k} ({sensors[k][0]:.1f}x{sensors[k][1]:.1f}mm)",
                                 variable=var)
            cb.pack(anchor=W)
            self.sensor_vars[k] = var

        plot_btn = ttk.Button(top_frame, text=tr("sensor_btn_plot", self.lang),
                              bootstyle=PRIMARY, command=lambda: self._sensor_plot(calc))
        plot_btn.pack(pady=(10, 0))

        canvas_frame = ttk.Frame(frame)
        canvas_frame.pack(fill=BOTH, expand=YES, padx=10, pady=(0, 10))

        fig = Figure(figsize=(6, 4), dpi=80)
        self.sensor_ax = fig.add_subplot(111)
        self.sensor_canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        self.sensor_canvas.get_tk_widget().pack(fill=BOTH, expand=YES)

        self.tab_pages.append((label_key, frame, calc, {}, {}))

    def _sensor_plot(self, calc):
        sensors = load_sensors()
        compare_list = []
        for name, var in self.sensor_vars.items():
            if var.get() and name in sensors:
                compare_list.append((name, sensors[name][0], sensors[name][1]))

        ax = self.sensor_ax
        ax.clear()

        all_dims = []
        for _, cw, ch in compare_list:
            all_dims.extend([cw, ch])
        if not all_dims:
            self.sensor_canvas.draw()
            return
        max_dim = max(all_dims) * 1.4
        ax.set_xlim(-max_dim / 2, max_dim / 2)
        ax.set_ylim(-max_dim / 2, max_dim / 2)
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.3)
        ax.axhline(0, color="gray", linewidth=0.5)
        ax.axvline(0, color="gray", linewidth=0.5)

        colors = ["#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231", "#911eb4",
                  "#42d4f4", "#f032e6", "#bfef45", "#fabed4"]
        for idx, (name, cw, ch) in enumerate(compare_list):
            color = colors[idx % len(colors)]
            ax.add_patch(Rectangle((-cw / 2, -ch / 2), cw, ch,
                                   fill=True, facecolor=color, alpha=0.3,
                                   edgecolor=color, linewidth=2,
                                   label=f"{name} ({cw:.1f}x{ch:.1f}mm)"))
        ax.legend(loc="upper right", fontsize=8)
        ax.set_title("Sensor Size Comparison", fontsize=10)
        self.sensor_canvas.draw()

    def _build_storage_ui(self, frame, calc, label_key):
        input_frame = ttk.Labelframe(frame, text=tr("storage_title_input", self.lang), padding=15)
        input_frame.pack(fill=X, padx=10, pady=10)

        ttk.Label(input_frame, text=tr("storage_label_size", self.lang)).grid(row=0, column=0, sticky=W, pady=5)
        size_var = ttk.StringVar(value=str(calc.inputs["image_size"]))
        ttk.Entry(input_frame, textvariable=size_var, width=12).grid(row=0, column=1, padx=(10, 0), pady=5, sticky=W)
        ttk.Label(input_frame, text="MB").grid(row=0, column=2, padx=(5, 0), pady=5, sticky=W)

        ttk.Label(input_frame, text=tr("storage_label_frames", self.lang)).grid(row=1, column=0, sticky=W, pady=5)
        frames_var = ttk.StringVar(value=str(calc.inputs["total_frames"]))
        ttk.Entry(input_frame, textvariable=frames_var, width=12).grid(row=1, column=1, padx=(10, 0), pady=5, sticky=W)

        entries = {"image_size": size_var, "total_frames": frames_var}

        output_vars = {
            "total_gb": ttk.StringVar(value="---"),
        }

        calc_btn = ttk.Button(input_frame, text=tr("fov_btn_calc", self.lang),
                              bootstyle=PRIMARY, command=lambda: self._storage_calculate(calc, entries, output_vars))
        calc_btn.grid(row=2, column=0, columnspan=3, pady=10)

        output_frame = ttk.Labelframe(frame, text=tr("storage_title_output", self.lang), padding=15)
        output_frame.pack(fill=X, padx=10, pady=10)

        ttk.Label(output_frame, text=tr("storage_result_gb", self.lang)).pack(anchor=W)
        ttk.Label(output_frame, textvariable=output_vars["total_gb"],
                  font=("", 12, "bold"), foreground="#0072B5").pack(anchor=W, pady=5)

        self.tab_pages.append((label_key, frame, calc, entries, output_vars))

    def _storage_calculate(self, calc, entries, output_vars):
        try:
            calc.set_inputs(
                image_size=float(entries["image_size"].get()),
                total_frames=int(entries["total_frames"].get()),
            )
            calc.calculate()
            res = calc.results
            if "error" in res:
                raise ValueError(res["error"])
            output_vars["total_gb"].set(f"{res['total_gb']:.2f} GB")
        except Exception as e:
            output_vars["total_gb"].set(str(e))

    def change_theme(self, theme_name):
        self.style.theme_use(theme_name)
        self.app_settings["theme"] = theme_name
        self.save_settings(self.app_settings)

    def set_font_size(self, size):
        self.font_size = size
        self.app_settings["font_size"] = size
        for _, frame, _, _, _ in self.tab_pages:
            self._set_widget_font(frame, size)
        self.save_settings(self.app_settings)

    def _set_widget_font(self, widget, size):
        font_tuple = ("TkDefaultFont", size)
        try:
            widget.configure(font=font_tuple)
        except:
            pass
        for child in widget.winfo_children():
            self._set_widget_font(child, size)

    def set_language(self, lang):
        if lang == self.lang:
            return
        self.lang = lang
        self.app_settings["lang"] = lang
        self.save_settings(self.app_settings)
        self.title(tr("app_title", lang))
        self._create_menu()
        old_pages = list(self.tab_pages)
        self.tab_pages.clear()
        for i, (label_key, frame, calc, entries, output_vars) in enumerate(old_pages):
            self.notebook.tab(i, text=tr(label_key, self.lang))
            for child in frame.winfo_children():
                child.destroy()
            top_bar = ttk.Frame(frame)
            top_bar.pack(fill=X, padx=5, pady=(5, 0))
            close_btn = ttk.Button(top_bar, text=tr("close_tab", self.lang), padding=(4, 0),
                                   command=self._close_current_tab)
            close_btn.pack(side=RIGHT)
            if isinstance(calc, FOVCalculator):
                self._build_fov_ui(frame, calc, label_key)
            elif isinstance(calc, ExposureCalculator):
                self._build_exposure_ui(frame, calc, label_key)
            elif isinstance(calc, SamplingCalculator):
                self._build_sampling_ui(frame, calc, label_key)
            elif isinstance(calc, SensorCalculator):
                self._build_sensor_ui(frame, calc, label_key)
            elif isinstance(calc, StorageCalculator):
                self._build_storage_ui(frame, calc, label_key)
            self._set_widget_font(frame, self.font_size)

    def show_sensor_editor(self):
        win = tk.Toplevel(self)
        win.title(tr("sensor_editor_title", self.lang))
        win.transient(self)
        win.grab_set()
        self.update_idletasks()
        saved_size = self.app_settings.get("sensor_editor_size", "500x400")
        x = self.winfo_x() + (self.winfo_width() - 500) // 2
        y = self.winfo_y() + (self.winfo_height() - 400) // 2
        win.geometry(f"{saved_size}+{x}+{y}")

        def on_close():
            self.app_settings["sensor_editor_size"] = win.geometry().split("+")[0]
            self.save_settings(self.app_settings)
            win.destroy()
        win.protocol("WM_DELETE_WINDOW", on_close)

        list_frame = ttk.Frame(win)
        list_frame.pack(fill=BOTH, expand=YES, padx=10, pady=10)

        columns = ("name", "width", "height", "pixel")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode=BROWSE)
        tree.heading("name", text=tr("sensor_editor_name", self.lang))
        tree.heading("width", text=tr("sensor_editor_width", self.lang))
        tree.heading("height", text=tr("sensor_editor_height", self.lang))
        tree.heading("pixel", text=tr("sensor_editor_pixel", self.lang))
        tree.column("name", width=160)
        tree.column("width", width=80)
        tree.column("height", width=80)
        tree.column("pixel", width=80)

        scrollbar = ttk.Scrollbar(list_frame, orient=VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)

        sensors = load_sensors()
        for k, (w, h, p) in sensors.items():
            tree.insert("", END, values=(k, w, h, p))

        entry_frame = ttk.Frame(win)
        entry_frame.pack(fill=X, padx=10, pady=(0, 10))

        ttk.Label(entry_frame, text=tr("sensor_editor_name", self.lang)).grid(row=0, column=0, padx=2)
        name_var = ttk.StringVar()
        ttk.Entry(entry_frame, textvariable=name_var, width=16).grid(row=0, column=1, padx=2)

        ttk.Label(entry_frame, text=tr("sensor_editor_width", self.lang)).grid(row=0, column=2, padx=2)
        w_var = ttk.StringVar()
        ttk.Entry(entry_frame, textvariable=w_var, width=7).grid(row=0, column=3, padx=2)

        ttk.Label(entry_frame, text=tr("sensor_editor_height", self.lang)).grid(row=0, column=4, padx=2)
        h_var = ttk.StringVar()
        ttk.Entry(entry_frame, textvariable=h_var, width=7).grid(row=0, column=5, padx=2)

        ttk.Label(entry_frame, text=tr("sensor_editor_pixel", self.lang)).grid(row=0, column=6, padx=2)
        p_var = ttk.StringVar()
        ttk.Entry(entry_frame, textvariable=p_var, width=7).grid(row=0, column=7, padx=2)

        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill=X, padx=10, pady=(0, 10))

        def add_sensor():
            name = name_var.get().strip()
            try:
                w = float(w_var.get())
                h = float(h_var.get())
                p = float(p_var.get()) if p_var.get().strip() else 0
            except ValueError:
                return
            if not name or w <= 0 or h <= 0:
                return
            sensors = load_sensors()
            sensors[name] = [w, h, p]
            save_sensors(sensors)
            tree.insert("", END, values=(name, w, h, p))
            name_var.set("")
            w_var.set("")
            h_var.set("")
            p_var.set("")

        def delete_sensor():
            sel = tree.selection()
            if not sel:
                return
            item = tree.item(sel[0])
            name = str(item["values"][0])
            sensors = load_sensors()
            if name in sensors:
                del sensors[name]
                save_sensors(sensors)
            tree.delete(sel[0])

        def modify_sensor():
            sel = tree.selection()
            if not sel:
                return
            item = tree.item(sel[0])
            old_name = item["values"][0]
            name = name_var.get().strip()
            try:
                w = float(w_var.get())
                h = float(h_var.get())
                p = float(p_var.get()) if p_var.get().strip() else 0
            except ValueError:
                return
            if not name or w <= 0 or h <= 0:
                return
            sensors = load_sensors()
            if old_name in sensors:
                del sensors[old_name]
            sensors[name] = [w, h, p]
            save_sensors(sensors)
            tree.item(sel[0], values=(name, w, h, p))

        def on_select(event):
            sel = tree.selection()
            if sel:
                item = tree.item(sel[0])
                name_var.set(item["values"][0])
                w_var.set(str(item["values"][1]))
                h_var.set(str(item["values"][2]))
                p_var.set(str(item["values"][3]))

        tree.bind("<<TreeviewSelect>>", on_select)

        ttk.Button(btn_frame, text=tr("sensor_editor_add", self.lang),
                   command=add_sensor).pack(side=LEFT, padx=2)
        ttk.Button(btn_frame, text=tr("sensor_editor_modify", self.lang),
                   command=modify_sensor).pack(side=LEFT, padx=2)
        ttk.Button(btn_frame, text=tr("sensor_editor_delete", self.lang),
                   command=delete_sensor).pack(side=LEFT, padx=2)

    def show_lens_editor(self):
        win = tk.Toplevel(self)
        win.title(tr("lens_editor_title", self.lang))
        win.transient(self)
        win.grab_set()
        self.update_idletasks()
        saved_size = self.app_settings.get("lens_editor_size", "500x400")
        x = self.winfo_x() + (self.winfo_width() - 500) // 2
        y = self.winfo_y() + (self.winfo_height() - 400) // 2
        win.geometry(f"{saved_size}+{x}+{y}")

        def on_close():
            self.app_settings["lens_editor_size"] = win.geometry().split("+")[0]
            self.save_settings(self.app_settings)
            win.destroy()
        win.protocol("WM_DELETE_WINDOW", on_close)

        list_frame = ttk.Frame(win)
        list_frame.pack(fill=BOTH, expand=YES, padx=10, pady=10)

        columns = ("name", "focal_length", "aperture")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode=BROWSE)
        tree.heading("name", text=tr("lens_editor_name", self.lang))
        tree.heading("focal_length", text=tr("lens_editor_fl", self.lang))
        tree.heading("aperture", text=tr("lens_editor_ap", self.lang))
        tree.column("name", width=240)
        tree.column("focal_length", width=100)
        tree.column("aperture", width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient=VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)

        lenses = load_lenses()
        for k, (fl, ap) in lenses.items():
            tree.insert("", END, values=(k, fl, ap))

        entry_frame = ttk.Frame(win)
        entry_frame.pack(fill=X, padx=10, pady=(0, 10))

        ttk.Label(entry_frame, text=tr("lens_editor_name", self.lang)).grid(row=0, column=0, padx=2)
        name_var = ttk.StringVar()
        ttk.Entry(entry_frame, textvariable=name_var, width=24).grid(row=0, column=1, padx=2)

        ttk.Label(entry_frame, text=tr("lens_editor_fl", self.lang)).grid(row=0, column=2, padx=2)
        fl_var = ttk.StringVar()
        ttk.Entry(entry_frame, textvariable=fl_var, width=8).grid(row=0, column=3, padx=2)

        ttk.Label(entry_frame, text=tr("lens_editor_ap", self.lang)).grid(row=0, column=4, padx=2)
        ap_var = ttk.StringVar()
        ttk.Entry(entry_frame, textvariable=ap_var, width=8).grid(row=0, column=5, padx=2)

        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill=X, padx=10, pady=(0, 10))

        def add_lens():
            name = name_var.get().strip()
            try:
                fl = float(fl_var.get())
                ap = float(ap_var.get())
            except ValueError:
                return
            if not name or fl <= 0 or ap <= 0:
                return
            lenses = load_lenses()
            lenses[name] = [fl, ap]
            save_lenses(lenses)
            tree.insert("", END, values=(name, fl, ap))
            name_var.set("")
            fl_var.set("")
            ap_var.set("")

        def delete_lens():
            sel = tree.selection()
            if not sel:
                return
            item = tree.item(sel[0])
            name = str(item["values"][0])
            lenses = load_lenses()
            if name in lenses:
                del lenses[name]
                save_lenses(lenses)
            tree.delete(sel[0])

        def modify_lens():
            sel = tree.selection()
            if not sel:
                return
            item = tree.item(sel[0])
            old_name = item["values"][0]
            name = name_var.get().strip()
            try:
                fl = float(fl_var.get())
                ap = float(ap_var.get())
            except ValueError:
                return
            if not name or fl <= 0 or ap <= 0:
                return
            lenses = load_lenses()
            if old_name in lenses:
                del lenses[old_name]
            lenses[name] = [fl, ap]
            save_lenses(lenses)
            tree.item(sel[0], values=(name, fl, ap))

        def on_select(event):
            sel = tree.selection()
            if sel:
                item = tree.item(sel[0])
                name_var.set(item["values"][0])
                fl_var.set(str(item["values"][1]))
                ap_var.set(str(item["values"][2]))

        tree.bind("<<TreeviewSelect>>", on_select)

        ttk.Button(btn_frame, text=tr("sensor_editor_add", self.lang),
                   command=add_lens).pack(side=LEFT, padx=2)
        ttk.Button(btn_frame, text=tr("sensor_editor_modify", self.lang),
                   command=modify_lens).pack(side=LEFT, padx=2)
        ttk.Button(btn_frame, text=tr("sensor_editor_delete", self.lang),
                   command=delete_lens).pack(side=LEFT, padx=2)

    def _on_destroy(self, event):
        if event.widget == self:
            size = self.geometry()
            self.app_settings["window_size"] = size
            self.save_settings(self.app_settings)

    def show_about(self):
        win = tk.Toplevel(self)
        win.title(tr("about_title", self.lang))
        win.transient(self)
        win.grab_set()
        try:
            win.iconbitmap("icon.ico")
        except:
            pass
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 300) // 2
        y = self.winfo_y() + (self.winfo_height() - 150) // 2
        win.geometry(f"300x150+{x}+{y}")
        win.resizable(False, False)
        ttk.Label(win, text=tr("about_content", self.lang), justify=CENTER).pack(expand=YES)
        ttk.Button(win, text="OK", command=win.destroy).pack(pady=(0, 10))

    def export_current_calculation(self):
        idx = self.notebook.index(self.notebook.select())
        if idx is None:
            return
        title, _, calc, entries, output_vars = self.tab_pages[idx]

        if isinstance(calc, SensorCalculator):
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG 图片", "*.png"), ("所有文件", "*.*")],
                title="导出传感器对比图"
            )
            if file_path:
                self.sensor_canvas.figure.savefig(file_path, dpi=150, bbox_inches="tight")
                messagebox.showinfo("导出成功", f"图片已保存至：{file_path}")
            return

        lines = ["AstroPrep 计算记录", "="*30, title]
        for k, var in entries.items():
            lines.append(f"{k}: {var.get()}")
        for k, var in output_vars.items():
            lines.append(f"{k}: {var.get()}")
        lines.append("="*30)
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            title="导出计算记录"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            messagebox.showinfo("导出成功", f"记录已保存至：{file_path}")

    @staticmethod
    def load_settings():
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {"theme": "darkly", "lang": "zh", "font_size": 10}

    @staticmethod
    def save_settings(settings_dict):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings_dict, f, indent=4)
        except Exception as e:
            print(f"保存设置失败: {e}")


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
