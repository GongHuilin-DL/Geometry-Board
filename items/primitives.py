# 基本图元：点、线、射线、矩形、圆、椭圆、多边形
"""基本图元：点、线段、直线、射线、多边形、圆、椭圆。"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QPainterPath, QColor, QBrush, QTransform

from items.base_item import ShapeItem


class PointItem(ShapeItem):
    """点：实心小圆，颜色跟描边一致。"""

    def _radius(self) -> float:
        return max(4.0, float(self.model.style.line_width) + 2.0)

    def build_path(self) -> QPainterPath:
        p = QPainterPath()
        if self.model.points:
            c = self.model.points[0]
            r = self._radius()
            p.addEllipse(QPointF(c.x, c.y), r, r)
        return p

    def boundingRect(self) -> QRectF:
        if not self.model.points:
            return QRectF()
        c = self.model.points[0]
        r = self._radius() + 2
        return QRectF(c.x - r, c.y - r, 2 * r, 2 * r)

    def shape(self) -> QPainterPath:
        p = QPainterPath()
        if self.model.points:
            c = self.model.points[0]
            r = self._radius() + 4
            p.addEllipse(QPointF(c.x, c.y), r, r)
        return p

    def paint(self, painter, option, widget=None):
        style = self.model.style
        color = QColor(style.fill_color if style.fill_enabled else style.stroke)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawPath(self.build_path())


class SegmentItem(ShapeItem):
    def build_path(self) -> QPainterPath:
        p = QPainterPath()
        if len(self.model.points) >= 2:
            a, b = self.model.points[0], self.model.points[1]
            p.moveTo(a.x, a.y)
            p.lineTo(b.x, b.y)
        return p


class LineItem(ShapeItem):
    EXTEND = 1e4

    def build_path(self) -> QPainterPath:
        p = QPainterPath()
        if len(self.model.points) < 2:
            return p
        a, b = self.model.points[0], self.model.points[1]
        dx, dy = b.x - a.x, b.y - a.y
        d = math.hypot(dx, dy)
        if d < 1e-9:
            return p
        ux, uy = dx / d, dy / d
        p.moveTo(a.x - ux * self.EXTEND, a.y - uy * self.EXTEND)
        p.lineTo(b.x + ux * self.EXTEND, b.y + uy * self.EXTEND)
        return p


class RayItem(ShapeItem):
    EXTEND = 1e4

    def build_path(self) -> QPainterPath:
        p = QPainterPath()
        if len(self.model.points) < 2:
            return p
        a, b = self.model.points[0], self.model.points[1]
        dx, dy = b.x - a.x, b.y - a.y
        d = math.hypot(dx, dy)
        if d < 1e-9:
            return p
        ux, uy = dx / d, dy / d
        p.moveTo(a.x, a.y)
        p.lineTo(a.x + ux * self.EXTEND, a.y + uy * self.EXTEND)
        return p


class PolygonItem(ShapeItem):
    """三角形、矩形、平行四边形、梯形、五角星、六边形、任意多边形都走这里。"""

    def build_path(self) -> QPainterPath:
        pts = self.model.points
        p = QPainterPath()
        if len(pts) < 2:
            return p
        p.moveTo(pts[0].x, pts[0].y)
        for pt in pts[1:]:
            p.lineTo(pt.x, pt.y)
        p.closeSubpath()
        return p


class CircleItem(ShapeItem):
    def build_path(self) -> QPainterPath:
        p = QPainterPath()
        if not self.model.points or self.model.rx <= 0:
            return p
        c = self.model.points[0]
        r = self.model.rx
        p.addEllipse(QPointF(c.x, c.y), r, r)
        return p


class EllipseItem(ShapeItem):
    def build_path(self) -> QPainterPath:
        p = QPainterPath()
        if not self.model.points:
            return p
        rx, ry = self.model.rx, self.model.ry
        if rx <= 0 or ry <= 0:
            return p
        c = self.model.points[0]
        p.addEllipse(QPointF(c.x, c.y), rx, ry)
        if abs(self.model.rotation) > 1e-9:
            t = QTransform()
            t.translate(c.x, c.y)
            t.rotate(math.degrees(self.model.rotation))
            t.translate(-c.x, -c.y)
            p = t.map(p)
        return p