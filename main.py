import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import json
import os
from tkinter import filedialog, messagebox

from calculators.fov_calc import FOVCalculator
from calculators.exposure_calc import ExposureCalculator
from calculators.sampling_calc import SamplingCalculator

SETTINGS_FILE = "astro_settings.json"
LOCALE_DIR = "locales"

_locales_cache = {}

def load_locale(lang):
    path = os.path.join(LOCALE_DIR, f"{lang}.json")
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
    ("tab_exposure", ExposureCalculator),
    ("tab_sampling", SamplingCalculator),
]

CATEGORIES = ["starscape", "planetary", "deepsky"]


class MainApplication(ttk.Window):
    def __init__(self):
        self.app_settings = self.load_settings()
        init_theme = self.app_settings.get("theme", "darkly")
        self.lang = self.app_settings.get("lang", "zh")
        self.font_size = self.app_settings.get("font_size", 10)
        self.current_category = "deepsky"

        super().__init__(themename=init_theme)
        self.title(tr("app_title", self.lang))
        self.geometry("650x550")
        self.resizable(True, True)

        self.tab_pages = []

        self._create_menu()
        self._build_notebook()

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
        for cat in CATEGORIES:
            cat_menu = ttk.Menu(calc_menu, tearoff=False)
            for label_key, calc_class in ALL_CALCULATORS:
                if calc_class.category == cat:
                    cat_menu.add_command(
                        label=tr(label_key, self.lang),
                        command=lambda c=cat: self.switch_category(c)
                    )
            calc_menu.add_cascade(label=tr(f"menu_calc_{cat}", self.lang), menu=cat_menu)
        menubar.add_cascade(label=tr("menu_calc", self.lang), menu=calc_menu)

        about_menu = ttk.Menu(menubar, tearoff=False)
        about_menu.add_command(label=tr("menu_about", self.lang), command=self.show_about)
        menubar.add_cascade(label=tr("menu_about", self.lang), menu=about_menu)

        self.config(menu=menubar)

    def switch_category(self, category):
        self.current_category = category
        saved_inputs = {}
        for _, _, calc, entries, _ in self.tab_pages:
            saved_inputs[type(calc).__name__] = {k: v.get() for k, v in entries.items()}
        self._build_notebook()
        for _, _, calc, entries, _ in self.tab_pages:
            name = type(calc).__name__
            if name in saved_inputs:
                for k, v in saved_inputs[name].items():
                    if k in entries:
                        entries[k].set(v)

    def _build_notebook(self):
        if hasattr(self, 'notebook'):
            self.notebook.destroy()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=BOTH, expand=YES, padx=10, pady=10)
        self.tab_pages.clear()

        for label_key, calc_class in ALL_CALCULATORS:
            if calc_class.category == self.current_category:
                self._add_tab(label_key, calc_class)

        if self.notebook.tabs():
            self.notebook.select(0)

    def _add_tab(self, label_key, calc_class):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=tr(label_key, self.lang))
        calc = calc_class()

        if isinstance(calc, FOVCalculator):
            self._build_fov_ui(frame, calc)
        elif isinstance(calc, ExposureCalculator):
            self._build_exposure_ui(frame, calc)
        elif isinstance(calc, SamplingCalculator):
            self._build_sampling_ui(frame, calc)

        self._set_widget_font(frame, self.font_size)

    def _build_fov_ui(self, frame, calc):
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

        self.tab_pages.append((tr(label_key, self.lang), frame, calc, entries, output_vars))

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

    def _build_exposure_ui(self, frame, calc):
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

        self.tab_pages.append((tr("tab_exposure", lang), frame, calc, entries, output_vars))

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

    def _build_sampling_ui(self, frame, calc):
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

        self.tab_pages.append((tr("tab_sampling", self.lang), frame, calc, entries, output_vars))

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
        saved_inputs = {}
        for _, _, calc, entries, _ in self.tab_pages:
            saved_inputs[type(calc).__name__] = {k: v.get() for k, v in entries.items()}
        self.lang = lang
        self.app_settings["lang"] = lang
        self.save_settings(self.app_settings)
        self.title(tr("app_title", lang))
        self._create_menu()
        self._build_notebook()
        for _, _, calc, entries, _ in self.tab_pages:
            name = type(calc).__name__
            if name in saved_inputs:
                for k, v in saved_inputs[name].items():
                    if k in entries:
                        entries[k].set(v)

    def show_about(self):
        messagebox.showinfo(
            tr("about_title", self.lang),
            tr("about_content", self.lang)
        )

    def export_current_calculation(self):
        idx = self.notebook.index(self.notebook.select())
        if idx is None:
            return
        title, _, calc, entries, output_vars = self.tab_pages[idx]
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
