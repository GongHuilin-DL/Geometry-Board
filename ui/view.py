"""BoardView：自定义 QGraphicsView。

职责：
- y 轴翻转（scale(1, -1)），使场景坐标 = 世界坐标
- 滚轮缩放（以鼠标为锚点）、中键平移
- 工具状态机：select 放行给 Scene，其余工具在此处理
- 拖动预览、多边形累积、自由曲线收集
"""
from __future__ import annotations

import math
from dataclasses import replace
from typing import List, Optional

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsView

from core.geometry import Vec2
from core.model import Shape, ShapeStyle
from items import create_item, ShapeItem
from items.star_hexagon import make_hexagon_points, make_star_points
from scene.board_scene import BoardScene


TOOL_IDS_WITH_DRAG = frozenset({
    'line', 'segment', 'ray', 'triangle', 'rect',
    'parallelogram', 'trapezoid', 'star', 'hexagon',
    'circle', 'ellipse',
})


class BoardView(QGraphicsView):
    request_function = Signal()
    request_polynomial = Signal()
    status_message = Signal(str)

    def __init__(self, scene: BoardScene, parent=None):
        super().__init__(scene, parent)
        self.scene = scene
        self.current_tool = 'select'
        self.current_style = ShapeStyle()
        self._drag_start: Optional[Vec2] = None
        self._polygon_points: List[Vec2] = []
        self._freehand_points: List[Vec2] = []
        self._preview_item: Optional[ShapeItem] = None
        self._pan_start: Optional[QPointF] = None

        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setSceneRect(-50, -50, 100, 100)
        self.scale(1, -1)   # 关键：世界坐标 y 向上

    # ------------------------------------------------------------ 工具
    def set_tool(self, tool_id: str) -> None:
        if tool_id == self.current_tool:
            return
        self._cancel_pending()
        self.current_tool = tool_id
        if tool_id != 'select':
            self.scene.clearSelection()
        self.setCursor(Qt.CrossCursor if tool_id != 'select' else Qt.ArrowCursor)
        self.status_message.emit(self._hint_for(tool_id))

    def _hint_for(self, tool_id: str) -> str:
        hints = {
            'select': '选择模式：单击选中，拖动平移，滚轮缩放',
            'point': '点击画点',
            'line': '按住拖动画直线',
            'segment': '按住拖动画线段',
            'ray': '按住拖动画射线',
            'triangle': '按住拖动画三角形',
            'rect': '按住拖动画矩形',
            'parallelogram': '按住拖动画平行四边形',
            'trapezoid': '按住拖动画梯形',
            'star': '以按下点为中心、拖动距离为半径画五角星',
            'hexagon': '以按下点为中心、拖动距离为半径画六边形',
            'circle': '以按下点为中心、拖动距离为半径画圆',
            'ellipse': '以按下点为中心、拖动距离为横纵半径画椭圆',
            'polygon': '单击累积顶点，双击或回车结束',
            'freehand': '按住自由拖动绘制曲线',
            'func': '单击后在对话框输入函数表达式',
            'polynomial': '单击后在对话框输入多项式系数',
        }
        return hints.get(tool_id, '')

    # ------------------------------------------------------------ 事件
    def wheelEvent(self, event):
        factor = 1.1 if event.angleDelta().y() > 0 else 1 / 1.1
        self.scale(factor, factor)
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._pan_start = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return

        if event.button() == Qt.LeftButton and self.current_tool not in ('select', 'freehand'):
            self._handle_tool_press(event)
            event.accept()
            return

        if event.button() == Qt.LeftButton and self.current_tool == 'freehand':
            wp = self._world_pos(event)
            self._freehand_points = [wp]
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._pan_start is not None:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            # 翻转 y 后，平移向量在 view 坐标中的 y 需取反
            self.translate(delta.x(), -delta.y())
            event.accept()
            return

        if self.current_tool == 'freehand' and self._freehand_points:
            wp = self._world_pos(event)
            self._freehand_points.append(wp)
            self._update_freehand_preview()
            event.accept()
            return

        if self._drag_start is not None:
            self._update_drag_preview(self._drag_start, self._world_pos(event))
            event.accept()
            return

        if self.current_tool == 'polygon' and self._polygon_points:
            self._update_polygon_preview(self._world_pos(event))
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton and self._pan_start is not None:
            self._pan_start = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return

        if event.button() == Qt.LeftButton and self._drag_start is not None:
            self._finish_drag(self._drag_start, self._world_pos(event))
            self._drag_start = None
            event.accept()
            return

        if event.button() == Qt.LeftButton and self.current_tool == 'freehand' \
                and self._freehand_points:
            self._finish_freehand()
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.current_tool == 'polygon' and event.button() == Qt.LeftButton:
            self._finish_polygon()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._cancel_pending()
            event.accept()
            return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and self.current_tool == 'polygon':
            self._finish_polygon()
            event.accept()
            return
        super().keyPressEvent(event)

    # ------------------------------------------------------------ 工具处理
    def _world_pos(self, event) -> Vec2:
        sp = self.mapToScene(event.position().toPoint())
        return Vec2(sp.x(), sp.y())

    def _handle_tool_press(self, event):
        tool = self.current_tool
        wp = self._world_pos(event)

        if tool == 'point':
            shape = Shape(type='point', points=[wp], style=self.current_style)
            self.scene.add_shape(shape)
            return

        if tool in TOOL_IDS_WITH_DRAG:
            self._drag_start = wp
            return

        if tool == 'polygon':
            self._polygon_points.append(wp)
            self._update_polygon_preview(wp)
            return

        if tool == 'func':
            self.request_function.emit()
            return

        if tool == 'polynomial':
            self.request_polynomial.emit()
            return

    # ------------------------------------------------------------ 拖动预览
    def _clear_preview(self):
        if self._preview_item is not None:
            self.scene.removeItem(self._preview_item)
            self._preview_item = None

    def _set_preview(self, shape: Shape):
        self._clear_preview()
        self._preview_item = create_item(shape)
        self.scene.addItem(self._preview_item)

    def _update_drag_preview(self, start: Vec2, cur: Vec2):
        shape = self._build_drag_shape(self.current_tool, start, cur)
        if shape is None:
            self._clear_preview()
            return
        shape.style = self.current_style
        self._set_preview(shape)

    def _finish_drag(self, start: Vec2, end: Vec2):
        self._clear_preview()
        shape = self._build_drag_shape(self.current_tool, start, end)
        if shape is None:
            return
        shape.style = self.current_style
        self.scene.add_shape(shape)

    def _update_polygon_preview(self, cursor: Vec2):
        pts = self._polygon_points + [cursor]
        if len(pts) < 2:
            return
        self._set_preview(Shape(type='freehand', points=pts,
                                style=self.current_style))

    def _finish_polygon(self):
        pts = self._polygon_points
        self._polygon_points = []
        self._clear_preview()
        if len(pts) < 3:
            return
        self.scene.add_shape(Shape(type='polygon', points=pts,
                                   style=self.current_style))

    def _update_freehand_preview(self):
        if len(self._freehand_points) < 2:
            return
        self._set_preview(Shape(type='freehand',
                                points=list(self._freehand_points),
                                style=self.current_style))

    def _finish_freehand(self):
        pts = self._freehand_points
        self._freehand_points = []
        self._clear_preview()
        if len(pts) < 2:
            return
        self.scene.add_shape(Shape(type='freehand', points=pts,
                                   style=self.current_style))

    def _cancel_pending(self):
        self._clear_preview()
        self._drag_start = None
        self._polygon_points = []
        self._freehand_points = []

    # ------------------------------------------------------------ 图形构造
    @staticmethod
    def _build_drag_shape(tool: str, a: Vec2, b: Vec2) -> Optional[Shape]:
        dx = b.x - a.x
        dy = b.y - a.y
        x0, x1 = min(a.x, b.x), max(a.x, b.x)
        y0, y1 = min(a.y, b.y), max(a.y, b.y)
        r = math.hypot(dx, dy)

        if tool == 'segment':
            return Shape(type='segment', points=[a, b])
        if tool == 'line':
            return Shape(type='line', points=[a, b])
        if tool == 'ray':
            return Shape(type='ray', points=[a, b])
        if tool == 'rect':
            return Shape(type='polygon', points=[
                Vec2(x0, y0), Vec2(x1, y0), Vec2(x1, y1), Vec2(x0, y1)])
        if tool == 'triangle':
            mx = (x0 + x1) / 2
            return Shape(type='polygon', points=[
                Vec2(mx, y1), Vec2(x1, y0), Vec2(x0, y0)])
        if tool == 'parallelogram':
            d = (x1 - x0) * 0.25
            return Shape(type='polygon', points=[
                Vec2(x0 + d, y1), Vec2(x1, y1),
                Vec2(x1 - d, y0), Vec2(x0, y0)])
        if tool == 'trapezoid':
            d = (x1 - x0) * 0.22
            return Shape(type='polygon', points=[
                Vec2(x0 + d, y1), Vec2(x1 - d, y1),
                Vec2(x1, y0), Vec2(x0, y0)])
        if tool == 'star':
            if r < 1e-6:
                return None
            return Shape(type='polygon', points=make_star_points(a, r))
        if tool == 'hexagon':
            if r < 1e-6:
                return None
            return Shape(type='polygon', points=make_hexagon_points(a, r))
        if tool == 'circle':
            if r < 1e-6:
                return None
            return Shape(type='circle', points=[a], rx=r, ry=r)
        if tool == 'ellipse':
            rx, ry = abs(dx), abs(dy)
            if rx < 1e-6 or ry < 1e-6:
                return None
            return Shape(type='ellipse', points=[a], rx=rx, ry=ry)
        return None