"""主窗口：组装工具栏、View、属性面板、顶部样式栏。"""
from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QKeySequence
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDoubleSpinBox, QFileDialog, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QToolBar, QWidget,
)

from core.expr import is_valid_expr
from core.model import FILL_ALGORITHMS, Shape, ShapeStyle
from scene.board_scene import BoardScene
from ui.dialogs import FunctionDialog, PolynomialDialog, coeffs_to_expr
from ui.property_panel import PropertyPanel
from ui.toolbar import ToolBarWidget
from ui.view import BoardView


DASH_LABELS = [
    ('solid', '实线'), ('dashed', '虚线'),
    ('dotted', '点线'), ('dashdot', '点划线'),
]
FILL_LABELS = [
    ('solid', '纯色'), ('linear', '线性渐变'), ('radial', '径向渐变'),
    ('hatch', '斜线'), ('cross', '交叉'), ('grid', '网格'), ('dots', '点状'),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('几何画板 Geometry Board')
        self.resize(1200, 800)

        self.scene = BoardScene()
        self.view = BoardView(self.scene)
        self.toolbar = ToolBarWidget()
        self.panel = PropertyPanel(self.scene)

        central = QWidget()
        h = QHBoxLayout(central)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        h.addWidget(self.toolbar)
        h.addWidget(self.view, 1)
        h.addWidget(self.panel)
        self.setCentralWidget(central)

        self._build_style_bar()
        self._build_shortcuts()
        self._connect_signals()

        self.statusBar().showMessage('就绪')

    # ---------------------------------------------------------- 顶部样式栏
    def _build_style_bar(self):
        bar = QToolBar('样式')
        bar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, bar)

        bar.addWidget(QLabel(' 描边 '))
        self.stroke_color = self._color_button('#1d4ed8')
        self.stroke_color.clicked.connect(lambda: self._pick_color('stroke'))
        bar.addWidget(self.stroke_color)

        bar.addWidget(QLabel(' 粗细 '))
        self.line_width = QDoubleSpinBox()
        self.line_width.setRange(0.5, 30)
        self.line_width.setValue(2)
        self.line_width.setSingleStep(0.5)
        self.line_width.valueChanged.connect(self._on_line_width_changed)
        bar.addWidget(self.line_width)

        bar.addWidget(QLabel(' 线型 '))
        self.dash_combo = QComboBox()
        for k, v in DASH_LABELS:
            self.dash_combo.addItem(v, k)
        self.dash_combo.currentIndexChanged.connect(self._on_dash_changed)
        bar.addWidget(self.dash_combo)

        bar.addSeparator()
        bar.addWidget(QLabel(' 填充 '))
        self.fill_enabled = QAction('启用填充', self, checkable=True)
        self.fill_enabled.toggled.connect(
            lambda v: self._apply_style('fill_enabled', v))
        bar.addAction(self.fill_enabled)

        self.fill_color = self._color_button('#93c5fd')
        self.fill_color.clicked.connect(lambda: self._pick_color('fill_color'))
        bar.addWidget(self.fill_color)

        self.fill_algo = QComboBox()
        for k, v in FILL_LABELS:
            self.fill_algo.addItem(v, k)
        self.fill_algo.currentIndexChanged.connect(self._on_fill_algo_changed)
        bar.addWidget(self.fill_algo)

        bar.addSeparator()
        self.undo_action = QAction('撤销', self)
        self.undo_action.triggered.connect(self._undo)
        bar.addAction(self.undo_action)

        self.redo_action = QAction('重做', self)
        self.redo_action.triggered.connect(self._redo)
        bar.addAction(self.redo_action)

        self.save_action = QAction('保存', self)
        self.save_action.triggered.connect(self._save)
        bar.addAction(self.save_action)

        self.load_action = QAction('加载', self)
        self.load_action.triggered.connect(self._load)
        bar.addAction(self.load_action)

        bar.addSeparator()
        self.clear_action = QAction('清空', self)
        self.clear_action.triggered.connect(self._clear)
        bar.addAction(self.clear_action)

    def _color_button(self, color_hex: str):
        from PySide6.QtWidgets import QPushButton
        btn = QPushButton()
        btn.setFixedSize(28, 24)
        btn._color = color_hex
        btn.setStyleSheet(f'background:{color_hex};border:1px solid #cbd5e1;border-radius:4px;')
        return btn

    def _pick_color(self, key: str):
        from PySide6.QtWidgets import QColorDialog
        btn = self.stroke_color if key == 'stroke' else self.fill_color
        c = QColorDialog.getColor(QColor(btn._color), self)
        if c.isValid():
            btn._color = c.name()
            btn.setStyleSheet(f'background:{c.name()};border:1px solid #cbd5e1;border-radius:4px;')
            self._apply_style(key, c.name())

    # ---------------------------------------------------------- 样式应用
    def _apply_style(self, key, value):
        sel = self.scene.selected_shapes()
        if sel:
            self.scene.apply_style([s.id for s in sel], {key: value})
        else:
            self.view.current_style = replace(self.view.current_style, **{key: value})

    def _on_line_width_changed(self, v):
        self._apply_style('line_width', float(v))

    def _on_dash_changed(self):
        self._apply_style('dash', self.dash_combo.currentData())

    def _on_fill_algo_changed(self):
        self._apply_style('fill_algo', self.fill_algo.currentData())

    def _sync_style_controls(self):
        sel = self.scene.selected_shapes()
        style = sel[0].style if sel else self.view.current_style
        self.stroke_color._color = style.stroke
        self.stroke_color.setStyleSheet(
            f'background:{style.stroke};border:1px solid #cbd5e1;border-radius:4px;')
        self.line_width.blockSignals(True)
        self.line_width.setValue(style.line_width)
        self.line_width.blockSignals(False)
        self.dash_combo.blockSignals(True)
        idx = self.dash_combo.findData(style.dash)
        if idx >= 0:
            self.dash_combo.setCurrentIndex(idx)
        self.dash_combo.blockSignals(False)
        self.fill_enabled.blockSignals(True)
        self.fill_enabled.setChecked(style.fill_enabled)
        self.fill_enabled.blockSignals(False)
        self.fill_color._color = style.fill_color
        self.fill_color.setStyleSheet(
            f'background:{style.fill_color};border:1px solid #cbd5e1;border-radius:4px;')
        self.fill_algo.blockSignals(True)
        idx = self.fill_algo.findData(style.fill_algo)
        if idx >= 0:
            self.fill_algo.setCurrentIndex(idx)
        self.fill_algo.blockSignals(False)

    # ---------------------------------------------------------- 快捷键
    def _build_shortcuts(self):
        undo = QAction(self); undo.setShortcut(QKeySequence.Undo)
        undo.triggered.connect(self._undo); self.addAction(undo)

        redo1 = QAction(self); redo1.setShortcut(QKeySequence.Redo)
        redo1.triggered.connect(self._redo); self.addAction(redo1)

        redo2 = QAction(self); redo2.setShortcut(QKeySequence('Ctrl+Y'))
        redo2.triggered.connect(self._redo); self.addAction(redo2)

        delete = QAction(self); delete.setShortcut(QKeySequence.Delete)
        delete.triggered.connect(self._delete_selected); self.addAction(delete)

    # ---------------------------------------------------------- 信号连接
    def _connect_signals(self):
        self.toolbar.tool_changed.connect(self.view.set_tool)
        self.scene.selectionChanged.connect(self._sync_style_controls)
        self.scene.selectionChanged.connect(self._update_undo_actions)
        self.view.request_function.connect(self._on_request_function)
        self.view.request_polynomial.connect(self._on_request_polynomial)
        self.view.status_message.connect(lambda msg: self.statusBar().showMessage(msg))

    def _update_undo_actions(self):
        self.undo_action.setEnabled(self.scene.history.can_undo())
        self.redo_action.setEnabled(self.scene.history.can_redo())

    # ---------------------------------------------------------- 命令
    def _undo(self):
        self.scene.undo()
        self._update_undo_actions()

    def _redo(self):
        self.scene.redo()
        self._update_undo_actions()

    def _delete_selected(self):
        self.scene.remove_selected()

    def _clear(self):
        if not self.scene.shapes:
            return
        r = QMessageBox.question(self, '确认', '确定清空画布吗？')
        if r != QMessageBox.Yes:
            return
        # 逐个 remove 走命令，可一次撤销
        ids = [s.id for s in self.scene.shapes]
        from core.history import CompositeCommand, RemoveShapeCommand
        cmds = [RemoveShapeCommand(self.scene.find_shape(sid)) for sid in ids]
        self.scene._run_command(CompositeCommand(cmds))

    def _save(self):
        from persistence.project import save_project
        path, _ = QFileDialog.getSaveFileName(
            self, '保存工程', 'drawing.gboard', '几何画板工程 (*.gboard *.json)')
        if not path:
            return
        try:
            save_project(path, self.scene.shapes, self.view.transform())
            self.statusBar().showMessage(f'已保存：{path}')
        except Exception as e:
            QMessageBox.critical(self, '保存失败', str(e))

    def _load(self):
        from persistence.project import load_project
        path, _ = QFileDialog.getOpenFileName(
            self, '加载工程', '', '几何画板工程 (*.gboard *.json)')
        if not path:
            return
        try:
            shapes, transform = load_project(path)
            # 清空当前场景：移除所有 item 并清空数据与命令栈
            for s in list(self.scene.shapes):
                item = self.scene.shape_items.get(s.id)
                if item is not None:
                    self.scene.removeItem(item)
            self.scene.shapes.clear()
            self.scene.shape_items.clear()
            self.scene.history.clear()
            # 重新载入
            for s in shapes:
                self.scene.add_shape(s)
            if transform is not None:
                self.view.setTransform(transform)
            self.statusBar().showMessage(f'已加载：{path}')
        except Exception as e:
            QMessageBox.critical(self, '加载失败', str(e))

    # ---------------------------------------------------------- 函数
    def _on_request_function(self):
        r = self.view.sceneRect()
        dlg = FunctionDialog((r.left(), r.right()), self)
        if dlg.exec() != QDialog.Accepted:
            return
        data = dlg.result_data()
        if not data or not is_valid_expr(data['expr']):
            QMessageBox.warning(self, '表达式无效', '请输入合法表达式')
            return
        shape = Shape(type='func', expr=data['expr'],
                      xmin=data['xmin'], xmax=data['xmax'],
                      style=replace(self.view.current_style, fill_enabled=False))
        self.scene.add_shape(shape)

    def _on_request_polynomial(self):
        r = self.view.sceneRect()
        dlg = PolynomialDialog((r.left(), r.right()), self)
        if dlg.exec() != QDialog.Accepted:
            return
        data = dlg.result_data()
        if not data:
            QMessageBox.warning(self, '输入无效', '请检查系数和定义域')
            return
        expr = coeffs_to_expr(data['coeffs'])
        if not is_valid_expr(expr):
            QMessageBox.warning(self, '表达式无效', expr)
            return
        shape = Shape(type='func', expr=expr,
                      xmin=data['xmin'], xmax=data['xmax'],
                      style=replace(self.view.current_style, fill_enabled=False))
        self.scene.add_shape(shape)