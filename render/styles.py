# 样式：画笔、画刷、虚线模式、填充算法定义
"""样式构造：ShapeStyle -> QPen / QBrush。

QPen 负责描边（实线/虚线/点线/点划线），
QBrush 负责填充（纯色/渐变/4 种纹理图案）。
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QColor, QPen, QBrush, QLinearGradient, QRadialGradient, QPainterPath,
)

from core.model import ShapeStyle


DASH_PATTERNS = {
    'solid':   Qt.SolidLine,
    'dashed':  Qt.DashLine,
    'dotted':  Qt.DotLine,
    'dashdot': Qt.DashDotLine,
}

# 纹理类填充：复用 Qt 内置 pattern，性能最好
TEXTURE_PATTERNS = {
    'hatch': Qt.BDiagPattern,
    'cross': Qt.DiagCrossPattern,
    'grid':  Qt.CrossPattern,
    'dots':  Qt.Dense5Pattern,
}


def make_pen(style: ShapeStyle) -> QPen:
    """根据样式构造 QPen。"""
    pen = QPen(QColor(style.stroke))
    pen.setWidthF(max(0.5, float(style.line_width)))
    pen.setStyle(DASH_PATTERNS.get(style.dash, Qt.SolidLine))
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    return pen


def make_fill_brush(style: ShapeStyle, path: QPainterPath) -> QBrush:
    """根据样式与绘制路径构造填充刷。"""
    color = QColor(style.fill_color)
    algo = style.fill_algo

    if algo == 'solid':
        return QBrush(color)

    r = path.boundingRect()
    if r.isEmpty():
        return QBrush(color)

    if algo == 'linear':
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0.0, color)
        light = QColor(color)
        light.setAlpha(50)
        g.setColorAt(1.0, light)
        return QBrush(g)

    if algo == 'radial':
        g = QRadialGradient(r.center(), max(r.width(), r.height()) / 2.0)
        g.setColorAt(0.0, color)
        light = QColor(color)
        light.setAlpha(50)
        g.setColorAt(1.0, light)
        return QBrush(g)

    if algo in TEXTURE_PATTERNS:
        return QBrush(color, TEXTURE_PATTERNS[algo])

    return QBrush(color)