#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DynSys Pro v8.5

Полноценное научное приложение для 2D нелинейных систем:
- GUI (PySide6 + matplotlib) для интерактивного анализа,
- CLI режим для запуска из терминала,
- подготовка к упаковке в EXE через PyInstaller.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

# Lazy imports for scientific stack
np = None
sp = None
solve_ivp = None
fsolve = None


class Colors:
    BG_PRIMARY = "#111827"
    BG_SECONDARY = "#1f2937"
    BG_TERTIARY = "#273244"
    ACCENT_BLUE = "#60a5fa"
    ACCENT_GREEN = "#34d399"
    ACCENT_RED = "#f87171"
    ACCENT_ORANGE = "#f59e0b"
    ACCENT_PURPLE = "#c084fc"
    TEXT_PRIMARY = "#e5e7eb"
    TEXT_SECONDARY = "#9ca3af"
    BORDER = "#374151"

    # calmer arrows
    VECTOR_COLOR = "#9aa4b2"
    VECTOR_ALPHA = 0.72
    VECTOR_WIDTH = 0.0030
    VECTOR_SCALE = 48


@dataclass
class ModelPreset:
    params: Dict[str, float]
    desc: str
    eq_x: str = "a*x + b*y - c*x**2 - h*x*y"
    eq_y: str = "d*y + e*x - f*y**2 - k*x*y"


class Config:
    VERSION = "8.5"
    EQ_X_DEFAULT = "a*x + b*y - c*x**2 - h*x*y"
    EQ_Y_DEFAULT = "d*y + e*x - f*y**2 - k*x*y"
    PARAM_KEYS = ["a", "b", "c", "d", "e", "f", "h", "k"]
    SETTINGS_FILE = Path.home() / ".dynsys_settings_v8.json"

    LOVE_PRESETS: Dict[str, ModelPreset] = {
        "Стабильная любовь": ModelPreset({"a": -0.3, "b": 0.8, "c": 0.1, "d": -0.3, "e": 0.8, "f": 0.1, "h": 0.0, "k": 0.0}, "Гармоничное устойчивое равновесие."),
        "Неравная любовь": ModelPreset({"a": 0.2, "b": 0.9, "c": 0.1, "d": -0.5, "e": 0.3, "f": 0.1, "h": 0.0, "k": 0.0}, "Один любит сильнее другого."),
        "Токсичность": ModelPreset({"a": 0.3, "b": -0.8, "c": 0.2, "d": 0.3, "e": -0.8, "f": 0.2, "h": 0.5, "k": 0.5}, "Взаимное разрушение и конфликт."),
        "Романтика": ModelPreset({"a": 0.1, "b": 0.7, "c": 0.05, "d": 0.1, "e": 0.7, "f": 0.05, "h": 0.0, "k": 0.0}, "Лёгкий и приятный подъём чувств."),
        "Эмоциональные качели": ModelPreset({"a": -0.1, "b": 1.0, "c": 0.0, "d": -1.0, "e": -0.1, "f": 0.0, "h": 0.0, "k": 0.0}, "Периоды сближения и отдаления."),
        "Дружба в любовь": ModelPreset({"a": -0.05, "b": 0.45, "c": 0.05, "d": -0.05, "e": 0.45, "f": 0.05, "h": 0.0, "k": 0.0}, "Медленный переход в тёплую привязанность."),
        "Любовь на расстоянии": ModelPreset({"a": -0.18, "b": 0.55, "c": 0.12, "d": -0.18, "e": 0.55, "f": 0.12, "h": 0.08, "k": 0.08}, "Связь поддерживается усилием и периодическими спадами."),
        "Ревность": ModelPreset({"a": 0.25, "b": -0.45, "c": 0.1, "d": 0.2, "e": 0.15, "f": 0.1, "h": 0.35, "k": 0.25}, "Рост напряжения и нестабильности."),
        "Созависимость": ModelPreset({"a": -0.35, "b": 1.1, "c": 0.15, "d": -0.35, "e": 1.1, "f": 0.15, "h": 0.2, "k": 0.2}, "Сильная взаимозависимость со слабой автономией."),
        "Восстановление после ссоры": ModelPreset({"a": -0.25, "b": 0.75, "c": 0.08, "d": -0.25, "e": 0.75, "f": 0.08, "h": -0.1, "k": -0.1}, "Постепенный выход к гармонии."),
        "Влюблённость и выгорание": ModelPreset({"a": 0.55, "b": 0.95, "c": 0.35, "d": 0.45, "e": 0.85, "f": 0.3, "h": 0.0, "k": 0.0}, "Быстрый рост эмоций с последующим спадом."),
        "Зрелый союз": ModelPreset({"a": -0.22, "b": 0.52, "c": 0.12, "d": -0.2, "e": 0.5, "f": 0.12, "h": 0.0, "k": 0.0}, "Устойчивый спокойный режим партнёрства."),
        "Треугольник": ModelPreset({"a": 0.32, "b": -0.62, "c": 0.16, "d": 0.24, "e": -0.48, "f": 0.13, "h": 0.42, "k": 0.34}, "Внешний фактор усиливает конфликт и турбулентность."),
        "Любовь-игра": ModelPreset({"a": 0.15, "b": 0.9, "c": 0.06, "d": -0.3, "e": 0.7, "f": 0.06, "h": 0.12, "k": 0.0}, "Флирт, проверка границ и неустойчивая динамика."),
        "Новая жизнь после разрыва": ModelPreset({"a": -0.4, "b": 0.2, "c": 0.18, "d": 0.05, "e": 0.55, "f": 0.08, "h": 0.0, "k": -0.08}, "Один отпускает, другой медленно стабилизируется."),
    }


def ensure_math_deps() -> None:
    global np, sp, solve_ivp, fsolve
    if np is not None and sp is not None and solve_ivp is not None and fsolve is not None:
        return
    try:
        import numpy as _np
        import sympy as _sp
        from scipy.integrate import solve_ivp as _solve_ivp
        from scipy.optimize import fsolve as _fsolve
    except ImportError as exc:
        raise RuntimeError("Не хватает зависимостей. Установите: pip install -r requirements.txt") from exc

    np = _np
    sp = _sp
    solve_ivp = _solve_ivp
    fsolve = _fsolve


class MathEngine:
    def __init__(self, eq_x: str = Config.EQ_X_DEFAULT, eq_y: str = Config.EQ_Y_DEFAULT):
        ensure_math_deps()
        self.x, self.y = sp.symbols("x y")
        self.params_sym = sp.symbols("a b c d e f h k")
        self.compile_equations(eq_x, eq_y)

    def compile_equations(self, eq_x: str, eq_y: str) -> None:
        local_dict = {"sin": sp.sin, "cos": sp.cos, "exp": sp.exp, "log": sp.log, "sqrt": sp.sqrt}
        self.expr_x = sp.sympify(eq_x, locals=local_dict)
        self.expr_y = sp.sympify(eq_y, locals=local_dict)
        args = (self.x, self.y) + self.params_sym
        self.func_x = sp.lambdify(args, self.expr_x, "numpy")
        self.func_y = sp.lambdify(args, self.expr_y, "numpy")
        self.j11 = sp.lambdify(args, sp.diff(self.expr_x, self.x), "numpy")
        self.j12 = sp.lambdify(args, sp.diff(self.expr_x, self.y), "numpy")
        self.j21 = sp.lambdify(args, sp.diff(self.expr_y, self.x), "numpy")
        self.j22 = sp.lambdify(args, sp.diff(self.expr_y, self.y), "numpy")

    def field(self, x: np.ndarray, y: np.ndarray, params: Dict[str, float]) -> Tuple[np.ndarray, np.ndarray]:
        p = [params.get(k, 0.0) for k in Config.PARAM_KEYS]
        u = np.nan_to_num(self.func_x(x, y, *p), nan=0.0, posinf=1e6, neginf=-1e6)
        v = np.nan_to_num(self.func_y(x, y, *p), nan=0.0, posinf=1e6, neginf=-1e6)
        return u, v

    def jacobian(self, x: float, y: float, params: Dict[str, float]):
        p = [params.get(k, 0.0) for k in Config.PARAM_KEYS]
        return np.array([[self.j11(x, y, *p), self.j12(x, y, *p)], [self.j21(x, y, *p), self.j22(x, y, *p)]], dtype=float)

    def trajectory(self, params: Dict[str, float], x0: float, y0: float, t_end: float = 50, n: int = 300):
        p = [params.get(k, 0.0) for k in Config.PARAM_KEYS]
        t = np.linspace(0, t_end, n)

        def rhs(_t: float, z: np.ndarray) -> List[float]:
            return [self.func_x(z[0], z[1], *p), self.func_y(z[0], z[1], *p)]

        sol = solve_ivp(rhs, [0, t_end], [x0, y0], t_eval=t, max_step=0.3, rtol=1e-8, atol=1e-10)
        return sol.t, sol.y[0], sol.y[1]

    def find_equilibria(self, params: Dict[str, float], lim: float = 4.0, n_grid: int = 9):
        p = [params.get(k, 0.0) for k in Config.PARAM_KEYS]

        def system(v):
            return [self.func_x(v[0], v[1], *p), self.func_y(v[0], v[1], *p)]

        roots = []
        grid = np.linspace(-lim, lim, n_grid)
        for x0 in grid:
            for y0 in grid:
                try:
                    sol, info, ier, msg = fsolve(system, [x0, y0], full_output=True)
                    if ier == 1 and np.linalg.norm(system(sol)) < 1e-6:
                        if not any(np.linalg.norm(sol - r) < 0.12 for r in roots):
                            roots.append(sol)
                except Exception:
                    continue
        return roots

    def stability_label(self, jac):
        eig = np.linalg.eigvals(jac)
        re = eig.real
        im = eig.imag
        if np.all(re < -1e-6):
            return ("устойчивый фокус" if np.any(np.abs(im) > 1e-6) else "устойчивый узел", Colors.ACCENT_GREEN)
        if np.all(re > 1e-6):
            return ("неустойчивый фокус" if np.any(np.abs(im) > 1e-6) else "неустойчивый узел", Colors.ACCENT_RED)
        if np.any(re > 1e-6) and np.any(re < -1e-6):
            return ("седло", Colors.ACCENT_PURPLE)
        return ("нейтральная/граничная", Colors.ACCENT_ORANGE)

    def lyapunov(self, params: Dict[str, float], x0: float, y0: float, t_end: float = 30.0, n: int = 200) -> float:
        t, x1, y1 = self.trajectory(params, x0, y0, t_end=t_end, n=n)
        _, x2, y2 = self.trajectory(params, x0 + 1e-7, y0 + 1e-7, t_end=t_end, n=n)
        d = np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
        d = d[d > 0]
        if len(d) < 2:
            return 0.0
        dt = t[1] - t[0]
        return float(np.mean(np.log(d[1:] / d[:-1])) / dt)


# ---------- persistence ----------
def save_settings(payload: dict) -> None:
    try:
        Config.SETTINGS_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def load_settings() -> dict:
    if not Config.SETTINGS_FILE.exists():
        return {}
    try:
        return json.loads(Config.SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


# ---------- CLI ----------
def run_cli(preset_name: str, x0: float, y0: float, t_end: float, points: int, export_csv: str | None) -> int:
    if preset_name not in Config.LOVE_PRESETS:
        print(f"Неизвестная модель: {preset_name}")
        print("Доступные модели:")
        for name in sorted(Config.LOVE_PRESETS):
            print(f" - {name}")
        return 2

    preset = Config.LOVE_PRESETS[preset_name]
    eng = MathEngine(preset.eq_x, preset.eq_y)
    t, x, y = eng.trajectory(preset.params, x0, y0, t_end=t_end, n=points)

    lyap = eng.lyapunov(preset.params, x0, y0, t_end=min(30.0, t_end), n=min(points, 250))
    roots = eng.find_equilibria(preset.params, lim=4.0, n_grid=9)

    print(f"DynSys Pro v{Config.VERSION}")
    print(f"Модель: {preset_name}")
    print(f"Описание: {preset.desc}")
    print(f"Старт: ({x0:.3f}, {y0:.3f})")
    print(f"Финал: ({x[-1]:.6f}, {y[-1]:.6f})")
    print(f"Оценка Ляпунова: {lyap:+.5f}")
    print(f"Равновесия (найдено {len(roots)}):")
    for i, r in enumerate(roots, 1):
        jac = eng.jacobian(float(r[0]), float(r[1]), preset.params)
        kind, _ = eng.stability_label(jac)
        print(f"  {i}. ({r[0]:+.4f}, {r[1]:+.4f}) -> {kind}")

    if export_csv:
        with open(export_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["t", "x", "y"])
            for i in range(len(t)):
                w.writerow([float(t[i]), float(x[i]), float(y[i])])
        print(f"CSV сохранён: {export_csv}")
    return 0


# ---------- GUI ----------
def run_gui() -> int:
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QAction, QKeySequence
        from PySide6.QtWidgets import (
            QApplication,
            QFileDialog,
            QComboBox,
            QDockWidget,
            QDoubleSpinBox,
            QFormLayout,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QMainWindow,
            QMessageBox,
            QPushButton,
            QTextEdit,
            QToolBar,
            QVBoxLayout,
            QWidget,
        )

        import matplotlib
        matplotlib.use("QtAgg")
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
        from matplotlib.figure import Figure
    except ImportError as exc:
        print(f"Ошибка импорта GUI-библиотек: {exc}")
        print("Для GUI нужно: pip install PySide6 matplotlib")
        return 1

    class MainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle(f"DynSys Pro v{Config.VERSION}")
            self.resize(1480, 930)
            self.engine = MathEngine()
            self.params = {k: 0.0 for k in Config.PARAM_KEYS}
            self.last_series = None

            self._setup_style()
            self._build_plot()
            self._build_dock()
            self._build_toolbar()
            self._restore()

        def _setup_style(self) -> None:
            self.setStyleSheet(
                f"""
                QMainWindow {{ background: {Colors.BG_PRIMARY}; }}
                QToolBar {{ background: {Colors.BG_SECONDARY}; border: 0; spacing: 6px; }}
                QDockWidget {{ color: {Colors.TEXT_PRIMARY}; }}
                QGroupBox {{
                    font-weight: 600; border: 1px solid {Colors.BORDER}; border-radius: 8px;
                    margin-top: 10px; color: {Colors.TEXT_PRIMARY};
                }}
                QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; color: {Colors.ACCENT_BLUE}; }}
                QLabel {{ color: {Colors.TEXT_PRIMARY}; }}
                QComboBox, QDoubleSpinBox, QTextEdit {{
                    background: {Colors.BG_TERTIARY}; color: {Colors.TEXT_PRIMARY};
                    border: 1px solid {Colors.BORDER}; border-radius: 6px; padding: 4px;
                }}
                QPushButton {{
                    background: {Colors.BG_TERTIARY}; color: {Colors.TEXT_PRIMARY}; border: 1px solid {Colors.BORDER};
                    border-radius: 7px; padding: 7px 10px;
                }}
                QPushButton:hover {{ background: #334155; }}
                """
            )

        def _build_plot(self) -> None:
            fig = Figure(figsize=(10, 8), dpi=100, facecolor=Colors.BG_SECONDARY)
            self.ax_phase = fig.add_subplot(211)
            self.ax_time = fig.add_subplot(212)
            for ax in (self.ax_phase, self.ax_time):
                ax.set_facecolor(Colors.BG_PRIMARY)
                ax.tick_params(colors=Colors.TEXT_SECONDARY)
                ax.grid(True, alpha=0.18, color=Colors.BORDER)
                for s in ax.spines.values():
                    s.set_color(Colors.BORDER)

            self.canvas = FigureCanvasQTAgg(fig)
            self.setCentralWidget(self.canvas)

        def _build_dock(self) -> None:
            dock = QDockWidget("Параметры", self)
            dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
            dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
            self.addDockWidget(Qt.LeftDockWidgetArea, dock)

            panel = QWidget()
            lay = QVBoxLayout(panel)

            model_box = QGroupBox("Модели любви")
            model_lay = QVBoxLayout(model_box)
            self.model_combo = QComboBox()
            self.model_combo.addItems(sorted(Config.LOVE_PRESETS.keys()))
            self.model_combo.currentTextChanged.connect(self.apply_preset)
            self.desc = QTextEdit(); self.desc.setReadOnly(True); self.desc.setMaximumHeight(72)
            model_lay.addWidget(self.model_combo)
            model_lay.addWidget(self.desc)

            params_box = QGroupBox("Параметры и диапазоны")
            params_form = QFormLayout(params_box)
            self.param_spin = {}
            for key in Config.PARAM_KEYS:
                s = QDoubleSpinBox(); s.setRange(-5, 5); s.setDecimals(3); s.setSingleStep(0.05)
                s.valueChanged.connect(lambda v, k=key: self._set_param(k, v))
                params_form.addRow(key, s)
                self.param_spin[key] = s

            self.x0 = QDoubleSpinBox(); self.x0.setRange(-10, 10); self.x0.setValue(0.2)
            self.y0 = QDoubleSpinBox(); self.y0.setRange(-10, 10); self.y0.setValue(0.4)
            self.t_end = QDoubleSpinBox(); self.t_end.setRange(1, 500); self.t_end.setValue(50)
            self.points = QDoubleSpinBox(); self.points.setRange(50, 3000); self.points.setDecimals(0); self.points.setValue(400)
            self.lim = QDoubleSpinBox(); self.lim.setRange(1, 20); self.lim.setValue(4.0)
            params_form.addRow("x0", self.x0)
            params_form.addRow("y0", self.y0)
            params_form.addRow("T", self.t_end)
            params_form.addRow("точек", self.points)
            params_form.addRow("граница", self.lim)

            actions_box = QGroupBox("Действия")
            actions_l = QHBoxLayout(actions_box)
            b_render = QPushButton("Пересчитать"); b_render.clicked.connect(self.render)
            b_export = QPushButton("Экспорт CSV"); b_export.clicked.connect(self.export_csv)
            actions_l.addWidget(b_render); actions_l.addWidget(b_export)

            analysis_box = QGroupBox("Научный анализ")
            analysis_l = QVBoxLayout(analysis_box)
            self.analysis = QTextEdit(); self.analysis.setReadOnly(True); self.analysis.setMinimumHeight(220)
            analysis_l.addWidget(self.analysis)

            lay.addWidget(model_box)
            lay.addWidget(params_box)
            lay.addWidget(actions_box)
            lay.addWidget(analysis_box)
            lay.addStretch(1)

            dock.setWidget(panel)
            self.params_dock = dock

        def _build_toolbar(self) -> None:
            tb = QToolBar("Main", self)
            self.addToolBar(tb)

            a_toggle = QAction("Свернуть/показать меню", self)
            a_toggle.setShortcut(QKeySequence("Ctrl+M"))
            a_toggle.triggered.connect(lambda: self.params_dock.setVisible(not self.params_dock.isVisible()))
            tb.addAction(a_toggle)

            a_replot = QAction("Обновить", self)
            a_replot.setShortcut(QKeySequence("Ctrl+R"))
            a_replot.triggered.connect(self.render)
            tb.addAction(a_replot)

            a_save_session = QAction("Сохранить сессию", self)
            a_save_session.triggered.connect(self.save_session)
            tb.addAction(a_save_session)

        def _set_param(self, key: str, value: float) -> None:
            self.params[key] = value

        def _restore(self) -> None:
            payload = load_settings()
            model = payload.get("model", "Стабильная любовь")
            if model not in Config.LOVE_PRESETS:
                model = "Стабильная любовь"
            self.model_combo.setCurrentText(model)
            self.x0.setValue(float(payload.get("x0", 0.2)))
            self.y0.setValue(float(payload.get("y0", 0.4)))
            self.t_end.setValue(float(payload.get("t_end", 50.0)))
            self.points.setValue(float(payload.get("points", 400)))
            self.lim.setValue(float(payload.get("lim", 4.0)))
            self.apply_preset(model)

        def apply_preset(self, name: str) -> None:
            p = Config.LOVE_PRESETS[name]
            self.desc.setText(p.desc)
            try:
                self.engine.compile_equations(p.eq_x, p.eq_y)
            except Exception as exc:
                QMessageBox.critical(self, "Ошибка уравнений", str(exc))
                return

            for k, v in p.params.items():
                self.params[k] = v
                self.param_spin[k].blockSignals(True)
                self.param_spin[k].setValue(v)
                self.param_spin[k].blockSignals(False)

            self.render()

        def render(self) -> None:
            lim = self.lim.value()
            x = np.linspace(-lim, lim, 24)
            y = np.linspace(-lim, lim, 24)
            xx, yy = np.meshgrid(x, y)
            u, v = self.engine.field(xx, yy, self.params)
            mag = np.sqrt(u * u + v * v)
            mag[mag == 0] = 1
            u, v = u / mag, v / mag

            n = int(self.points.value())
            t, tx, ty = self.engine.trajectory(self.params, self.x0.value(), self.y0.value(), t_end=self.t_end.value(), n=n)
            self.last_series = (t, tx, ty)

            eq_points = self.engine.find_equilibria(self.params, lim=lim, n_grid=9)
            lyap = self.engine.lyapunov(self.params, self.x0.value(), self.y0.value(), t_end=min(self.t_end.value(), 40.0), n=min(n, 300))

            self.ax_phase.clear()
            self.ax_phase.set_title("Фазовый портрет", color=Colors.TEXT_PRIMARY)
            self.ax_phase.quiver(xx, yy, u, v, color=Colors.VECTOR_COLOR, alpha=Colors.VECTOR_ALPHA, width=Colors.VECTOR_WIDTH, scale=Colors.VECTOR_SCALE, headwidth=2.6, headlength=3.6, headaxislength=3.4)
            self.ax_phase.plot(tx, ty, color=Colors.ACCENT_BLUE, linewidth=1.7)
            self.ax_phase.scatter([tx[0]], [ty[0]], color=Colors.ACCENT_ORANGE, s=35)

            report = [
                f"Ляпунов λ≈ {lyap:+.5f}",
                f"Равновесий: {len(eq_points)}",
            ]
            for i, r in enumerate(eq_points, 1):
                jac = self.engine.jacobian(float(r[0]), float(r[1]), self.params)
                kind, color = self.engine.stability_label(jac)
                self.ax_phase.scatter([r[0]], [r[1]], color=color, s=48, edgecolors="black", linewidths=0.4)
                report.append(f"{i}) ({r[0]:+.3f}, {r[1]:+.3f}) -> {kind}")

            self.ax_phase.set_xlim(-lim, lim)
            self.ax_phase.set_ylim(-lim, lim)

            self.ax_time.clear()
            self.ax_time.set_title("Временные ряды", color=Colors.TEXT_PRIMARY)
            self.ax_time.plot(t, tx, color=Colors.ACCENT_GREEN, label="X")
            self.ax_time.plot(t, ty, color=Colors.ACCENT_RED, label="Y")
            self.ax_time.legend(facecolor=Colors.BG_SECONDARY, edgecolor=Colors.BORDER, labelcolor=Colors.TEXT_PRIMARY)
            self.canvas.draw_idle()

            self.analysis.setPlainText("\n".join(report))

        def export_csv(self) -> None:
            if self.last_series is None:
                self.render()
            path, _ = QFileDialog.getSaveFileName(self, "Сохранить CSV", "trajectory.csv", "CSV files (*.csv)")
            if not path:
                return
            t, x, y = self.last_series
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["t", "x", "y"])
                for i in range(len(t)):
                    w.writerow([float(t[i]), float(x[i]), float(y[i])])
            self.statusBar().showMessage(f"CSV сохранён: {path}", 4000)

        def save_session(self) -> None:
            payload = {
                "model": self.model_combo.currentText(),
                "x0": self.x0.value(),
                "y0": self.y0.value(),
                "t_end": self.t_end.value(),
                "points": int(self.points.value()),
                "lim": self.lim.value(),
            }
            save_settings(payload)
            self.statusBar().showMessage("Сессия сохранена", 3000)

        def closeEvent(self, event):  # noqa: N802
            self.save_session()
            super().closeEvent(event)

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="DynSys Pro: научный анализатор динамических систем (GUI/CLI)")
    p.add_argument("--cli", action="store_true", help="Запуск в консоли без GUI")
    p.add_argument("--model", default="Стабильная любовь", help="Название модели любви")
    p.add_argument("--x0", type=float, default=0.2, help="Начальное x")
    p.add_argument("--y0", type=float, default=0.4, help="Начальное y")
    p.add_argument("--t-end", type=float, default=50.0, help="Конечное время")
    p.add_argument("--points", type=int, default=300, help="Число точек интегрирования")
    p.add_argument("--list-models", action="store_true", help="Вывести все модели")
    p.add_argument("--export-csv", help="Путь для сохранения CSV в CLI")
    return p


def main() -> int:
    args = build_arg_parser().parse_args()
    if args.list_models:
        for name, preset in sorted(Config.LOVE_PRESETS.items()):
            print(f"{name}: {preset.desc}")
        return 0

    try:
        if args.cli:
            return run_cli(args.model, args.x0, args.y0, args.t_end, args.points, args.export_csv)
        return run_gui()
    except RuntimeError as exc:
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
