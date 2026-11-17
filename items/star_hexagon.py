# 参数化图元：五角星、六边形
"""星形与六边形的顶点生成工具。

几何画板里的五角星、六边形本质是 type='polygon'，由 PolygonItem 绘制。
本模块仅提供生成顶点的辅助函数，供 UI 层创建图形时调用。
"""
from __future__ import annotations

import math

from core.geometry import Vec2


def make_star_points(center: Vec2, radius: float,
                     num_points: int = 5, inner_ratio: float = 0.382) -> list[Vec2]:
    pts: list[Vec2] = []
    for i in range(num_points * 2):
        ang = math.pi / 2 + i * math.pi / num_points
        r = radius if i % 2 == 0 else radius * inner_ratio
        pts.append(Vec2(center.x + math.cos(ang) * r,
                        center.y + math.sin(ang) * r))
    return pts


def make_hexagon_points(center: Vec2, radius: float) -> list[Vec2]:
    return [Vec2(center.x + math.cos(math.pi / 2 + i * math.pi / 3) * radius,
                 center.y + math.sin(math.pi / 2 + i * math.pi / 3) * radius)
            for i in range(6)]