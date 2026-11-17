# 工具栏：工具切换（选择/点/线/多边形/函数...）
"""左侧工具栏：垂直按钮组，发送 tool_changed 信号。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QToolBar, QToolButton, QWidget, QVBoxLayout


TOOLS = [
    ('select', '选择', '✥'),
    ('point', '点', '•'),
    ('line', '直线', '╱'),
    ('segment', '线段', '─'),
    ('ray', '射线', '→'),
    ('triangle', '三角形', '△'),
    ('rect', '矩形', '▭'),
    ('parallelogram', '平行四边形', '▱'),
    ('trapezoid', '梯形', '⏢'),
    ('star', '五角星', '★'),
    ('hexagon', '六边形', '⬡'),
    ('polygon', '多边形', '⬠'),
    ('circle', '圆', '○'),
    ('ellipse', '椭圆', '⬭'),
    ('polynomial', '多项式', 'xⁿ'),
    ('func', '函数', 'ƒ'),
    ('freehand', '自由曲线', '∿'),
]


class ToolBarWidget(QWidget):
    tool_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(64)
        self.setStyleSheet('background:#fff;border-right:1px solid #e2e8f0;')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        self._buttons: dict[str, QToolButton] = {}
        self._current = 'select'

        for tid, label, icon in TOOLS:
            btn = QToolButton()
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            btn.setText(f'{icon}\n{label}')
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setFixedHeight(48)
            btn.setStyleSheet(
                'QToolButton{border:none;border-radius:6px;color:#475569;font-size:10px;}'
                'QToolButton:hover{background:#f1f5f9;}'
                'QToolButton:checked{background:#dbeafe;color:#1d4ed8;font-weight:700;}'
            )
            btn.clicked.connect(lambda _=False, t=tid: self._on_click(t))
            layout.addWidget(btn)
            self._buttons[tid] = btn

        layout.addStretch(1)
        self._buttons['select'].setChecked(True)

    def _on_click(self, tool_id: str):
        self._current = tool_id
        self.tool_changed.emit(tool_id)

    def current_tool(self) -> str:
        return self._current