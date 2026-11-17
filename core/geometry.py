# 几何基础运算：点/向量/线段/圆/多边形，相交、距离、凸包
"""纯 Python 几何基础运算，不依赖 Qt / numpy。

设计原则：
- 值对象不可变（frozen dataclass），可哈希、可比较。
- 浮点比较统一走 EPS 容忍。
- 所有函数无副作用，方便单元测试。

本模块提供：
- Vec2：二维点/向量，支持加减、数乘、点积、叉积、旋转、距离
- BBox：轴对齐包围盒
- 距离：点到点/线/线段/射线
- 相交：线段与线段
- 多边形：有符号面积、周长、点在多边形内、凸包
- 变换：平移、旋转、缩放的纯函数
- 角度工具
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

EPS: float = 1e-9


# ---------------------------------------------------------------- 浮点工具
def almost_equal(a: float, b: float, eps: float = EPS) -> bool:
    """浮点近似相等。"""
    return abs(a - b) <= eps


# ---------------------------------------------------------------- 向量 / 点
@dataclass(frozen=True, slots=True)
class Vec2:
    """不可变二维点/向量。"""

    x: float
    y: float

    # -- 构造
    @staticmethod
    def of(x: float, y: float) -> "Vec2":
        return Vec2(float(x), float(y))

    @staticmethod
    def origin() -> "Vec2":
        return Vec2(0.0, 0.0)

    # -- 基本运算
    def __add__(self, o: "Vec2") -> "Vec2":
        return Vec2(self.x + o.x, self.y + o.y)

    def __sub__(self, o: "Vec2") -> "Vec2":
        return Vec2(self.x - o.x, self.y - o.y)

    def __mul__(self, k: float) -> "Vec2":
        return Vec2(self.x * k, self.y * k)

    __rmul__ = __mul__

    def __truediv__(self, k: float) -> "Vec2":
        return Vec2(self.x / k, self.y / k)

    def __neg__(self) -> "Vec2":
        return Vec2(-self.x, -self.y)

    # -- 向量运算
    def dot(self, o: "Vec2") -> float:
        return self.x * o.x + self.y * o.y

    def cross(self, o: "Vec2") -> float:
        return self.x * o.y - self.y * o.x

    def length(self) -> float:
        return math.hypot(self.x, self.y)

    def length_sq(self) -> float:
        return self.x * self.x + self.y * self.y

    def normalized(self) -> "Vec2":
        n = self.length()
        if n < EPS:
            return Vec2(0.0, 0.0)
        return Vec2(self.x / n, self.y / n)

    def distance_to(self, o: "Vec2") -> float:
        return math.hypot(self.x - o.x, self.y - o.y)

    def rotate(self, angle_rad: float) -> "Vec2":
        c, s = math.cos(angle_rad), math.sin(angle_rad)
        return Vec2(self.x * c - self.y * s, self.x * s + self.y * c)

    def angle(self) -> float:
        return math.atan2(self.y, self.x)

    def is_close(self, o: "Vec2", eps: float = EPS) -> bool:
        return almost_equal(self.x, o.x, eps) and almost_equal(self.y, o.y, eps)


Point = Vec2  # 语义别名，方便阅读


# ---------------------------------------------------------------- 包围盒
@dataclass(frozen=True, slots=True)
class BBox:
    """轴对齐包围盒（世界坐标）。"""

    xmin: float
    ymin: float
    xmax: float
    ymax: float

    @staticmethod
    def from_points(points: Iterable[Vec2]) -> "BBox":
        pts = list(points)
        if not pts:
            return BBox(0.0, 0.0, 0.0, 0.0)
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        return BBox(min(xs), min(ys), max(xs), max(ys))

    def width(self) -> float:
        return self.xmax - self.xmin

    def height(self) -> float:
        return self.ymax - self.ymin

    def center(self) -> Vec2:
        return Vec2((self.xmin + self.xmax) / 2.0, (self.ymin + self.ymax) / 2.0)

    def contains(self, p: Vec2) -> bool:
        return (self.xmin - EPS <= p.x <= self.xmax + EPS
                and self.ymin - EPS <= p.y <= self.ymax + EPS)

    def union(self, o: "BBox") -> "BBox":
        return BBox(min(self.xmin, o.xmin), min(self.ymin, o.ymin),
                    max(self.xmax, o.xmax), max(self.ymax, o.ymax))

    def expand(self, margin: float) -> "BBox":
        return BBox(self.xmin - margin, self.ymin - margin,
                    self.xmax + margin, self.ymax + margin)


# ---------------------------------------------------------------- 距离
def point_to_line_distance(p: Vec2, a: Vec2, b: Vec2) -> float:
    """点到无限直线 ab 的距离。a==b 时退化为点距。"""
    ab = b - a
    if ab.length() < EPS:
        return p.distance_to(a)
    return abs((p - a).cross(ab)) / ab.length()


def point_to_segment_distance(p: Vec2, a: Vec2, b: Vec2) -> float:
    """点到线段 ab 的距离。"""
    ab = b - a
    denom = ab.length_sq()
    if denom < EPS * EPS:
        return p.distance_to(a)
    t = (p - a).dot(ab) / denom
    t = max(0.0, min(1.0, t))
    return p.distance_to(a + ab * t)


def point_to_ray_distance(p: Vec2, a: Vec2, b: Vec2) -> float:
    """点到射线 ab（起点 a，经过 b）的距离。"""
    ab = b - a
    denom = ab.length_sq()
    if denom < EPS * EPS:
        return p.distance_to(a)
    t = (p - a).dot(ab) / denom
    if t <= 0.0:
        return p.distance_to(a)
    return p.distance_to(a + ab * t)


def closest_point_on_segment(p: Vec2, a: Vec2, b: Vec2) -> Vec2:
    """线段 ab 上离 p 最近的点。"""
    ab = b - a
    denom = ab.length_sq()
    if denom < EPS * EPS:
        return a
    t = (p - a).dot(ab) / denom
    t = max(0.0, min(1.0, t))
    return a + ab * t


# ---------------------------------------------------------------- 线段相交
def segment_intersection(a1: Vec2, a2: Vec2, b1: Vec2, b2: Vec2) -> Vec2 | None:
    """两线段求交。相交返回交点；平行/共线/不相交返回 None。"""
    r = a2 - a1
    s = b2 - b1
    denom = r.cross(s)
    if abs(denom) < EPS:
        return None
    qp = b1 - a1
    t = qp.cross(s) / denom
    u = qp.cross(r) / denom
    if -EPS <= t <= 1.0 + EPS and -EPS <= u <= 1.0 + EPS:
        return a1 + r * t
    return None


def segments_intersect(a1: Vec2, a2: Vec2, b1: Vec2, b2: Vec2) -> bool:
    """两线段是否有公共点（含共线重叠、端点接触）。"""
    if segment_intersection(a1, a2, b1, b2) is not None:
        return True
    # 退化：某条线段长度≈0
    if (a2 - a1).length() < EPS:
        return point_to_segment_distance(a1, b1, b2) < EPS
    if (b2 - b1).length() < EPS:
        return point_to_segment_distance(b1, a1, a2) < EPS
    # 共线判断 + 投影区间重叠
    ab = a2 - a1
    if abs(ab.cross(b1 - a1)) < EPS and abs(ab.cross(b2 - a1)) < EPS:
        denom = ab.length_sq()
        t1 = (b1 - a1).dot(ab) / denom
        t2 = (b2 - a1).dot(ab) / denom
        tmin, tmax = min(t1, t2), max(t1, t2)
        return tmax >= -EPS and tmin <= 1.0 + EPS
    return False


# ---------------------------------------------------------------- 多边形
def polygon_area_signed(points: Sequence[Vec2]) -> float:
    """有符号面积：顶点逆时针（数学习惯）为正。"""
    n = len(points)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n):
        j = (i + 1) % n
        s += points[i].x * points[j].y - points[j].x * points[i].y
    return s / 2.0


def polygon_area(points: Sequence[Vec2]) -> float:
    """无符号面积。"""
    return abs(polygon_area_signed(points))


def polygon_perimeter(points: Sequence[Vec2], closed: bool = True) -> float:
    n = len(points)
    if n < 2:
        return 0.0
    total = 0.0
    for i in range(n - 1):
        total += points[i].distance_to(points[i + 1])
    if closed and n > 2:
        total += points[-1].distance_to(points[0])
    return total


def point_in_polygon(p: Vec2, points: Sequence[Vec2]) -> bool:
    """射线法判断点是否在多边形内部或边上。"""
    n = len(points)
    if n < 3:
        return False
    # 边上优先视为“在内”
    for i in range(n):
        j = (i + 1) % n
        if point_to_segment_distance(p, points[i], points[j]) < EPS:
            return True
    # 射线法
    inside = False
    for i in range(n):
        j = (i + 1) % n
        yi, yj = points[i].y, points[j].y
        if (yi > p.y) != (yj > p.y):
            x_int = (points[j].x - points[i].x) * (p.y - yi) / (yj - yi) + points[i].x
            if p.x < x_int:
                inside = not inside
    return inside


def convex_hull(points: Iterable[Vec2]) -> List[Vec2]:
    """Andrew's monotone chain 凸包，逆时针返回最小凸包顶点。"""
    pts = sorted(set(points), key=lambda v: (v.x, v.y))
    if len(pts) <= 1:
        return list(pts)

    def cross(o: Vec2, a: Vec2, b: Vec2) -> float:
        return (a - o).cross(b - o)

    lower: List[Vec2] = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 1e-12:
            lower.pop()
        lower.append(p)

    upper: List[Vec2] = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 1e-12:
            upper.pop()
        upper.append(p)

    return lower[:-1] + upper[:-1]


# ---------------------------------------------------------------- 变换（纯函数）
def translate_points(points: Sequence[Vec2], dx: float, dy: float) -> List[Vec2]:
    return [Vec2(p.x + dx, p.y + dy) for p in points]


def rotate_points(points: Sequence[Vec2], center: Vec2, angle_rad: float) -> List[Vec2]:
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    out: List[Vec2] = []
    for p in points:
        dx, dy = p.x - center.x, p.y - center.y
        out.append(Vec2(center.x + dx * c - dy * s,
                        center.y + dx * s + dy * c))
    return out


def scale_points(points: Sequence[Vec2], center: Vec2,
                 kx: float, ky: float | None = None) -> List[Vec2]:
    if ky is None:
        ky = kx
    return [Vec2(center.x + (p.x - center.x) * kx,
                 center.y + (p.y - center.y) * ky)
            for p in points]


# ---------------------------------------------------------------- 角度工具
def deg_to_rad(deg: float) -> float:
    return deg * math.pi / 180.0


def rad_to_deg(rad: float) -> float:
    return rad * 180.0 / math.pi


def normalize_angle(rad: float) -> float:
    """归一化到 [-pi, pi)。"""
    two_pi = 2.0 * math.pi
    while rad >= math.pi:
        rad -= two_pi
    while rad < -math.pi:
        rad += two_pi
    return rad