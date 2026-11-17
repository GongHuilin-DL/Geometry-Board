# 曲线图元：函数曲线、自由曲线、多项式曲线
"""曲线图元：函数曲线、自由曲线。"""
from __future__ import annotations

from PySide6.QtGui import QPainterPath

from core.expr import sample_curve
from items.base_item import ShapeItem


class FuncItem(ShapeItem):
    """函数曲线：采样后连成 polyline。"""

    SAMPLE_COUNT = 800

    def build_path(self) -> QPainterPath:
        p = QPainterPath()
        m = self.model
        if not m.expr or m.xmax <= m.xmin:
            return p
        pts = sample_curve(m.expr, m.xmin, m.xmax, self.SAMPLE_COUNT)
        if len(pts) < 2:
            return p
        p.moveTo(pts[0].x, pts[0].y)
        for pt in pts[1:]:
            p.lineTo(pt.x, pt.y)
        return p


class FreehandItem(ShapeItem):
    """自由曲线：直接连接采样点；closed=True 时闭合。"""

    def build_path(self) -> QPainterPath:
        p = QPainterPath()
        pts = self.model.points
        if len(pts) < 2:
            return p
        p.moveTo(pts[0].x, pts[0].y)
        for pt in pts[1:]:
            p.lineTo(pt.x, pt.y)
        if self.model.closed:
            p.closeSubpath()
        return p