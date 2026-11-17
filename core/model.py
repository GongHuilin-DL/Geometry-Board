"""数据模型：Shape 与 ShapeStyle。

ShapeStyle：不可变样式（frozen），修改即换对象。
Shape：可变图元数据，to_dict / from_dict / apply_dict 支持快照与原地还原。
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .geometry import BBox, Vec2
from .expr import sample_curve


SHAPE_TYPES = frozenset({
    'point', 'line', 'segment', 'ray', 'polygon',
    'circle', 'ellipse', 'freehand', 'func',
})

DASH_STYLES = frozenset({'solid', 'dashed', 'dotted', 'dashdot'})

FILL_ALGORITHMS = frozenset({
    'solid', 'linear', 'radial', 'hatch', 'cross', 'grid', 'dots',
})


def new_id() -> str:
    return 's' + uuid.uuid4().hex[:8]


# ---------------------------------------------------------------- 样式
@dataclass(frozen=True, slots=True)
class ShapeStyle:
    stroke: str = '#1d4ed8'
    line_width: float = 2.0
    dash: str = 'solid'
    fill_enabled: bool = False
    fill_color: str = '#93c5fd'
    fill_algo: str = 'solid'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'stroke': self.stroke,
            'line_width': self.line_width,
            'dash': self.dash,
            'fill_enabled': self.fill_enabled,
            'fill_color': self.fill_color,
            'fill_algo': self.fill_algo,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> 'ShapeStyle':
        d = d or {}
        dash = d.get('dash', 'solid')
        algo = d.get('fill_algo', 'solid')
        try:
            lw = float(d.get('line_width', 2.0))
        except (TypeError, ValueError):
            lw = 2.0
        return ShapeStyle(
            stroke=str(d.get('stroke', '#1d4ed8')),
            line_width=lw,
            dash=dash if dash in DASH_STYLES else 'solid',
            fill_enabled=bool(d.get('fill_enabled', False)),
            fill_color=str(d.get('fill_color', '#93c5fd')),
            fill_algo=algo if algo in FILL_ALGORITHMS else 'solid',
        )


# ---------------------------------------------------------------- 图元
@dataclass
class Shape:
    id: str = field(default_factory=new_id)
    type: str = 'point'
    points: List[Vec2] = field(default_factory=list)
    style: ShapeStyle = field(default_factory=ShapeStyle)

    # 圆 / 椭圆
    rx: float = 0.0
    ry: float = 0.0
    rotation: float = 0.0        # 弧度

    # 自由曲线
    closed: bool = False

    # 函数曲线
    expr: str = ''
    xmin: float = 0.0
    xmax: float = 0.0

    # 显示名（可选）
    name: str = ''

    # ------------------------------------------------------------ 工具
    def clone(self) -> 'Shape':
        """深拷贝。"""
        return Shape(
            id=self.id,
            type=self.type,
            points=[Vec2(p.x, p.y) for p in self.points],
            style=self.style,
            rx=self.rx, ry=self.ry, rotation=self.rotation,
            closed=self.closed,
            expr=self.expr, xmin=self.xmin, xmax=self.xmax,
            name=self.name,
        )

    def is_fillable(self) -> bool:
        if self.type in ('polygon', 'circle', 'ellipse'):
            return True
        if self.type == 'freehand' and self.closed:
            return True
        return False

    def center(self) -> Vec2:
        return self.bounding_box().center()

    # ------------------------------------------------------------ 包围盒
    def bounding_box(self) -> BBox:
        t = self.type

        if t in ('circle', 'ellipse'):
            if not self.points:
                return BBox(0.0, 0.0, 0.0, 0.0)
            c = self.points[0]
            rx, ry = abs(self.rx), abs(self.ry)
            if rx < 1e-9 and ry < 1e-9:
                return BBox(c.x, c.y, c.x, c.y)
            # 旋转后椭圆在 x / y 轴的半投影
            cos_r = math.cos(self.rotation)
            sin_r = math.sin(self.rotation)
            hw = math.hypot(rx * cos_r, ry * sin_r)
            hh = math.hypot(rx * sin_r, ry * cos_r)
            return BBox(c.x - hw, c.y - hh, c.x + hw, c.y + hh)

        if t == 'func':
            if not self.expr or self.xmax <= self.xmin:
                return BBox(0.0, 0.0, 0.0, 0.0)
            pts = sample_curve(self.expr, self.xmin, self.xmax, 400)
            if not pts:
                return BBox(0.0, 0.0, 0.0, 0.0)
            return BBox.from_points(pts)

        if not self.points:
            return BBox(0.0, 0.0, 0.0, 0.0)
        return BBox.from_points(self.points)

    # ------------------------------------------------------------ 序列化
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type,
            'points': [{'x': p.x, 'y': p.y} for p in self.points],
            'style': self.style.to_dict(),
            'rx': self.rx,
            'ry': self.ry,
            'rotation': self.rotation,
            'closed': self.closed,
            'expr': self.expr,
            'xmin': self.xmin,
            'xmax': self.xmax,
            'name': self.name,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> 'Shape':
        d = d or {}
        try:
            raw_pts = d.get('points', []) or []
            pts = [Vec2(float(p['x']), float(p['y'])) for p in raw_pts]
        except (KeyError, TypeError, ValueError):
            pts = []

        t = d.get('type', 'point')
        if t not in SHAPE_TYPES:
            t = 'point'

        return Shape(
            id=str(d.get('id') or new_id()),
            type=t,
            points=pts,
            style=ShapeStyle.from_dict(d.get('style') or {}),
            rx=float(d.get('rx', 0.0) or 0.0),
            ry=float(d.get('ry', 0.0) or 0.0),
            rotation=float(d.get('rotation', 0.0) or 0.0),
            closed=bool(d.get('closed', False)),
            expr=str(d.get('expr', '') or ''),
            xmin=float(d.get('xmin', 0.0) or 0.0),
            xmax=float(d.get('xmax', 0.0) or 0.0),
            name=str(d.get('name', '') or ''),
        )

    def apply_dict(self, d: Dict[str, Any]) -> None:
        """原地还原字段（id 不变）。命令撤销时使用，保持对象引用稳定。"""
        d = d or {}
        if 'type' in d and d['type'] in SHAPE_TYPES:
            self.type = d['type']
        if 'points' in d:
            try:
                self.points = [Vec2(float(p['x']), float(p['y']))
                               for p in (d['points'] or [])]
            except (KeyError, TypeError, ValueError):
                pass
        if 'style' in d:
            self.style = ShapeStyle.from_dict(d['style'] or {})
        for key, cast in (('rx', float), ('ry', float),
                          ('rotation', float), ('xmin', float), ('xmax', float)):
            if key in d:
                try:
                    setattr(self, key, cast(d[key] or 0.0))
                except (TypeError, ValueError):
                    pass
        if 'closed' in d:
            self.closed = bool(d['closed'])
        if 'expr' in d:
            self.expr = str(d['expr'] or '')
        if 'name' in d:
            self.name = str(d['name'] or '')