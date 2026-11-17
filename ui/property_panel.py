# 属性面板：选中图元的样式、变换参数编辑
"""右侧属性面板：选中信息、变换、删除。"""
from __future__ import annotations

import math

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDoubleSpinBox, QFormLayout, QGroupBox, QLabel,
    QPushButton, QVBoxLayout, QWidget,
)

from core.geometry import Vec2, rotate_points, scale_points
from scene.board_scene import BoardScene


class PropertyPanel(QWidget):
    def __init__(self, scene: BoardScene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.setFixedWidth(240)
        self.setStyleSheet('background:#fff;border-left:1px solid #e2e8f0;')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.info = QLabel('未选中图形')
        self.info.setStyleSheet('color:#64748b;font-size:12px;')
        self.info.setWordWrap(True)
        layout.addWidget(self.info)

        # 平移
        g_move = QGroupBox('平移')
        f1 = QFormLayout(g_move)
        self.tx = QDoubleSpinBox(); self.tx.setRange(-1e6, 1e6); self.tx.setDecimals(2); self.tx.setValue(1)
        self.ty = QDoubleSpinBox(); self.ty.setRange(-1e6, 1e6); self.ty.setDecimals(2); self.ty.setValue(1)
        f1.addRow('Δx', self.tx)
        f1.addRow('Δy', self.ty)
        btn_move = QPushButton('应用平移')
        btn_move.clicked.connect(self._apply_translate)
        f1.addRow(btn_move)
        layout.addWidget(g_move)

        # 旋转
        g_rot = QGroupBox('旋转')
        f2 = QFormLayout(g_rot)
        self.rot = QDoubleSpinBox(); self.rot.setRange(-360, 360); self.rot.setValue(15)
        f2.addRow('角度°', self.rot)
        btn_rot = QPushButton('绕中心旋转')
        btn_rot.clicked.connect(self._apply_rotate)
        f2.addRow(btn_rot)
        layout.addWidget(g_rot)

        # 缩放
        g_scale = QGroupBox('缩放')
        f3 = QFormLayout(g_scale)
        self.scale = QDoubleSpinBox(); self.scale.setRange(0.01, 100); self.scale.setValue(1.2)
        f3.addRow('比例', self.scale)
        btn_scale = QPushButton('绕中心缩放')
        btn_scale.clicked.connect(self._apply_scale)
        f3.addRow(btn_scale)
        layout.addWidget(g_scale)

        # 删除
        btn_del = QPushButton('删除该图形')
        btn_del.setStyleSheet('background:#fee2e2;color:#b91c1c;border:1px solid #fecaca;')
        btn_del.clicked.connect(self._delete_selected)
        layout.addWidget(btn_del)

        layout.addStretch(1)

        self.scene.selectionChanged.connect(self._on_selection_changed)

    # ---------------------------------------------------------- 刷新
    def _on_selection_changed(self):
        sel = self.scene.selected_shapes()
        if not sel:
            self.info.setText('未选中图形')
        elif len(sel) == 1:
            s = sel[0]
            names = {'point': '点', 'line': '直线', 'segment': '线段', 'ray': '射线',
                     'polygon': '多边形', 'circle': '圆', 'ellipse': '椭圆',
                     'freehand': '自由曲线', 'func': '函数曲线'}
            extra = ''
            if s.type == 'polygon':
                extra = f' · {len(s.points)} 顶点'
            if s.type == 'func':
                extra = f' · f(x)={s.expr}'
            self.info.setText(f'选中：{names.get(s.type, s.type)}{extra}')
        else:
            self.info.setText(f'选中 {len(sel)} 个图形')

    # ---------------------------------------------------------- 变换
    def _apply_translate(self):
        dx, dy = self.tx.value(), self.ty.value()
        if dx == 0 and dy == 0:
            return
        def mutate(s):
            s.points = [Vec2(p.x + dx, p.y + dy) for p in s.points]
        self._apply_to_selected(mutate, '平移')

    def _apply_rotate(self):
        deg = self.rot.value()
        if deg == 0:
            return
        rad = math.radians(deg)
        def mutate(s):
            if not s.points:
                return
            c = s.bounding_box().center()
            s.points = rotate_points(s.points, c, rad)
            if s.type in ('circle', 'ellipse'):
                s.rotation += rad
        self._apply_to_selected(mutate, '旋转')

    def _apply_scale(self):
        k = self.scale.value()
        if k == 1:
            return
        def mutate(s):
            if not s.points:
                return
            c = s.bounding_box().center()
            s.points = scale_points(s.points, c, k)
            if s.rx:
                s.rx *= abs(k)
            if s.ry:
                s.ry *= abs(k)
        self._apply_to_selected(mutate, '缩放')

    def _apply_to_selected(self, mutate, label):
        ids = [s.id for s in self.scene.selected_shapes()]
        if not ids:
            return
        self.scene.modify_shapes(ids, mutate, label)

    def _delete_selected(self):
        self.scene.remove_selected()