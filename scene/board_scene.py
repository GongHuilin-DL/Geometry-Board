"""BoardScene：图形场景管理。

职责：
- 维护 Shape 数据列表与 ShapeItem 映射
- 所有变更走 Command，统一入 History
- 左键拖拽选中图形平移（多选一次撤销）
- 选中框绘制、selectionChanged 透传 UI

坐标系：View 层 scale(1, -1)，Scene 坐标 = 世界坐标。

命名注意：属性 shape_items 刻意避开 items 这个名字，
避免遮蔽 QGraphicsScene.items() 方法（命中检测依赖它）。
"""
from __future__ import annotations

from dataclasses import replace
from typing import Dict, List, Optional

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QGraphicsScene

from core.geometry import Vec2
from core.history import (
    History, AddShapeCommand, RemoveShapeCommand,
    ModifyShapeCommand, CompositeCommand,
)
from core.model import Shape
from items import ShapeItem, create_item


class BoardScene(QGraphicsScene):
    """几何画板的图形场景。"""

    DRAG_THRESHOLD = 1e-3   # 世界坐标下的最小拖拽距离

    def __init__(self, parent=None):
        super().__init__(parent)
        self.shapes: List[Shape] = []
        self.shape_items: Dict[str, ShapeItem] = {}
        self.history = History()
        self._drag_state: Optional[dict] = None
        self.setBackgroundBrush(QColor('#fbfdff'))

    # ------------------------------------------------------------ 查询
    def find_shape(self, shape_id: str) -> Optional[Shape]:
        for s in self.shapes:
            if s.id == shape_id:
                return s
        return None

    def selected_shapes(self) -> List[Shape]:
        return [it.model for it in self.selectedItems() if isinstance(it, ShapeItem)]

    def selected_shape(self) -> Optional[Shape]:
        sel = self.selected_shapes()
        return sel[0] if sel else None

    # ------------------------------------------------------------ 命令执行
    def _run_command(self, cmd, execute: bool = True) -> None:
        if execute:
            cmd.execute(self.shapes)
        self.history.push(cmd)
        self._sync_items()
        self.selectionChanged.emit()

    def undo(self):
        cmd = self.history.undo(self.shapes)
        if cmd:
            self._sync_items()
            self.selectionChanged.emit()
        return cmd

    def redo(self):
        cmd = self.history.redo(self.shapes)
        if cmd:
            self._sync_items()
            self.selectionChanged.emit()
        return cmd

    # ------------------------------------------------------------ 增删改
    def add_shape(self, shape: Shape) -> None:
        self._run_command(AddShapeCommand(shape))

    def remove_shape(self, shape_id: str) -> None:
        shape = self.find_shape(shape_id)
        if shape:
            self._run_command(RemoveShapeCommand(shape))

    def remove_selected(self) -> None:
        sel = self.selected_shapes()
        if not sel:
            return
        cmds = [RemoveShapeCommand(s) for s in sel]
        if len(cmds) == 1:
            self._run_command(cmds[0])
        else:
            self._run_command(CompositeCommand(cmds))

    def modify_shape(self, shape_id: str, mutate_fn, label: str = '修改图形') -> None:
        """原地修改 shape，自动记录 before/after；若完全一致则不入栈。"""
        shape = self.find_shape(shape_id)
        if not shape:
            return
        before = shape.to_dict()
        mutate_fn(shape)
        after = shape.to_dict()
        if before == after:
            return
        cmd = ModifyShapeCommand(shape_id, before, after, label)
        self.history.push(cmd)
        item = self.shape_items.get(shape_id)
        if item:
            item.sync_from_model()
        self.selectionChanged.emit()

    def modify_shapes(self, shape_ids: List[str], mutate_fn,
                      label: str = '修改图形') -> None:
        """批量原地修改，多图形一次撤销。"""
        cmds = []
        for sid in shape_ids:
            shape = self.find_shape(sid)
            if not shape:
                continue
            before = shape.to_dict()
            mutate_fn(shape)
            after = shape.to_dict()
            if before != after:
                cmds.append(ModifyShapeCommand(sid, before, after, label))
        if not cmds:
            return
        if len(cmds) == 1:
            self.history.push(cmds[0])
        else:
            self.history.push(CompositeCommand(cmds))
        self._sync_items()
        self.selectionChanged.emit()

    def apply_style(self, shape_ids: List[str], style_updates: dict,
                    label: str = '修改样式') -> None:
        """批量修改样式，一次撤销。"""
        cmds = []
        for sid in shape_ids:
            shape = self.find_shape(sid)
            if not shape:
                continue
            before = shape.to_dict()
            shape.style = replace(shape.style, **style_updates)
            after = shape.to_dict()
            if before != after:
                cmds.append(ModifyShapeCommand(sid, before, after, label))
        if not cmds:
            return
        if len(cmds) == 1:
            self.history.push(cmds[0])
        else:
            self.history.push(CompositeCommand(cmds))
        self._sync_items()
        self.selectionChanged.emit()

    # ------------------------------------------------------------ items 同步
    def _sync_items(self) -> None:
        """shapes 列表 → shape_items 字典，按 id 增量同步。"""
        current_ids = {s.id for s in self.shapes}
        for sid in list(self.shape_items.keys()):
            if sid not in current_ids:
                self.removeItem(self.shape_items[sid])
                del self.shape_items[sid]
        for s in self.shapes:
            if s.id in self.shape_items:
                self.shape_items[s.id].sync_from_model()
            else:
                item = create_item(s)
                self.addItem(item)
                self.shape_items[s.id] = item

    # ------------------------------------------------------------ 鼠标交互
    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return
        pos = event.scenePos()
        hit = self._hit_item(pos)
        if hit is not None:
            if not hit.isSelected():
                self.clearSelection()
                hit.setSelected(True)
            self._begin_drag(pos)
            event.accept()
        else:
            self.clearSelection()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_state is None:
            super().mouseMoveEvent(event)
            return
        self._update_drag(event.scenePos())
        event.accept()

    def mouseReleaseEvent(self, event):
        if self._drag_state is None:
            super().mouseReleaseEvent(event)
            return
        self._end_drag()
        event.accept()

    def _hit_item(self, scene_pos: QPointF) -> Optional[ShapeItem]:
        # 这里调用的是 QGraphicsScene.items(QPointF) 方法，
        # 因为 self.shape_items 没有遮蔽 items 这个名字。
        for item in self.items(scene_pos):
            if isinstance(item, ShapeItem):
                return item
        return None

    def _begin_drag(self, scene_pos: QPointF) -> None:
        self._drag_state = {
            'start': QPointF(scene_pos),
            'initial': {s.id: s.to_dict() for s in self.selected_shapes()},
            'moved': False,
        }

    def _update_drag(self, scene_pos: QPointF) -> None:
        state = self._drag_state
        if not state:
            return
        dx = scene_pos.x() - state['start'].x()
        dy = scene_pos.y() - state['start'].y()
        if abs(dx) < self.DRAG_THRESHOLD and abs(dy) < self.DRAG_THRESHOLD:
            return
        state['moved'] = True
        for sid, initial in state['initial'].items():
            shape = self.find_shape(sid)
            if not shape:
                continue
            init_pts = [Vec2(p['x'], p['y']) for p in initial['points']]
            shape.points = [Vec2(p.x + dx, p.y + dy) for p in init_pts]
            item = self.shape_items.get(sid)
            if item:
                item.sync_from_model()

    def _end_drag(self) -> None:
        state = self._drag_state
        self._drag_state = None
        if not state or not state['moved']:
            return
        cmds = []
        for sid, initial in state['initial'].items():
            shape = self.find_shape(sid)
            if not shape:
                continue
            after = shape.to_dict()
            if after != initial:
                cmds.append(ModifyShapeCommand(sid, initial, after, '移动图形'))
        if not cmds:
            return
        if len(cmds) == 1:
            self.history.push(cmds[0])
        else:
            self.history.push(CompositeCommand(cmds))
        self.selectionChanged.emit()

    # ------------------------------------------------------------ 选中框
    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)
        pen = QPen(QColor('#0ea5e9'))
        pen.setStyle(Qt.DashLine)
        pen.setWidth(0)             # cosmetic pen：缩放时不加粗
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        for item in self.selectedItems():
            if not isinstance(item, ShapeItem):
                continue
            if item.model.type in ('line', 'ray'):
                continue             # 避免 1e4 量级的超长包围盒
            painter.drawRect(item.boundingRect())