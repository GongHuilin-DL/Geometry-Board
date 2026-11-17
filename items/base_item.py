# 图元基类：统一 style、boundingRect、shape 命中检测
"""ShapeItem：所有图元的基类。

本地坐标系 = 世界坐标系（View 层通过 scale(1, -1) 翻转 y 轴）。
子类实现 build_path()；命中检测、boundingRect、paint 由基类统一处理。
"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainterPath, QPainterPathStroker
from PySide6.QtWidgets import QGraphicsItem

from core.model import Shape
from render.styles import make_pen, make_fill_brush


class ShapeItem(QGraphicsItem):
    """图元基类。"""

    def __init__(self, model: Shape, parent: QGraphicsItem | None = None):
        super().__init__(parent)
        self.model = model
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)

    # ---------------------------------------------------------- 几何
    def boundingRect(self) -> QRectF:
        bb = self.model.bounding_box()
        m = max(2.0, float(self.model.style.line_width)) + 2.0
        return QRectF(bb.xmin - m, bb.ymin - m,
                      bb.width() + 2 * m, bb.height() + 2 * m)

    def shape(self) -> QPainterPath:
        """命中形状：描边加宽 + 可填充图形把内部也纳入命中区。"""
        base = self.build_path()
        stroker = QPainterPathStroker()
        stroker.setWidth(max(6.0, float(self.model.style.line_width) + 4))
        hit = stroker.createStroke(base)
        if self.model.is_fillable():
            hit.addPath(base)
        return hit

    def build_path(self) -> QPainterPath:
        """子类实现：把 model 转成 QPainterPath（世界坐标）。"""
        return QPainterPath()

    # ---------------------------------------------------------- 绘制
    def paint(self, painter, option, widget=None):
        style = self.model.style
        path = self.build_path()
        painter.setPen(make_pen(style))
        if style.fill_enabled and self.model.is_fillable():
            painter.setBrush(make_fill_brush(style, path))
        else:
            painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

    # ---------------------------------------------------------- 模型同步
    def sync_from_model(self, geometry_changed: bool = True) -> None:
        """模型变化后调用；拖动时每个点都会调用，默认刷新几何索引。"""
        if geometry_changed:
            self.prepareGeometryChange()
        self.update()