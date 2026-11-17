"""items 层单元测试。需要 pytest-qt 提供 qapp fixture。"""
import math

from PySide6.QtCore import QPointF
from PySide6.QtGui import QImage, QPainter

from core.geometry import Vec2
from core.model import Shape, ShapeStyle
from items import create_item
from items.primitives import (
    PointItem, SegmentItem, LineItem, RayItem, PolygonItem,
    CircleItem, EllipseItem,
)
from items.curve_items import FuncItem, FreehandItem


def test_point_item(qapp):
    item = PointItem(Shape(type='point', points=[Vec2(1, 2)]))
    r = item.boundingRect()
    assert r.contains(QPointF(1, 2))
    assert item.shape().contains(QPointF(1, 2))


def test_segment_item(qapp):
    item = SegmentItem(Shape(type='segment', points=[Vec2(0, 0), Vec2(4, 0)]))
    r = item.boundingRect()
    assert r.contains(QPointF(0, 0))
    assert r.contains(QPointF(4, 0))
    hit = item.shape()
    assert hit.contains(QPointF(2, 0.1))
    assert not hit.contains(QPointF(2, 5))


def test_line_extends_beyond_endpoints(qapp):
    item = LineItem(Shape(type='line', points=[Vec2(0, 0), Vec2(1, 1)]))
    hit = item.shape()
    # 端点外远处仍在线上
    assert hit.contains(QPointF(100, 100))


def test_ray_starts_at_a(qapp):
    item = RayItem(Shape(type='ray', points=[Vec2(0, 0), Vec2(1, 0)]))
    hit = item.shape()
    assert hit.contains(QPointF(50, 0))
    assert not hit.contains(QPointF(-50, 0))


def test_polygon_item(qapp):
    s = Shape(type='polygon',
              points=[Vec2(0, 0), Vec2(2, 0), Vec2(2, 2), Vec2(0, 2)])
    item = PolygonItem(s)
    assert item.boundingRect().contains(QPointF(1, 1))
    hit = item.shape()
    assert hit.contains(QPointF(1, 1))         # 内部
    assert hit.contains(QPointF(0, 1))         # 边上


def test_circle_item(qapp):
    item = CircleItem(Shape(type='circle', points=[Vec2(0, 0)], rx=3, ry=3))
    r = item.boundingRect()
    assert r.contains(QPointF(3, 0))
    assert r.contains(QPointF(-3, 0))
    assert item.shape().contains(QPointF(0, 0))


# def test_ellipse_item_rotation(qapp):
#     item = EllipseItem(Shape(type='ellipse', points=[Vec2(0, 0)],
#                              rx=2, ry=1, rotation=math.pi / 2))
#     r = item.boundingRect()
#     # 旋转 90° 后宽高互换
#     assert r.width() > r.height()


# def test_ellipse_item_rotation(qapp):
#     """旋转 90° 后，boundingRect 的宽高互换。"""
#     base = Shape(type='ellipse', points=[Vec2(0, 0)], rx=2, ry=1)
#     rotated = Shape(type='ellipse', points=[Vec2(0, 0)], rx=2, ry=1,
#                     rotation=math.pi / 2)

#     r1 = EllipseItem(base).boundingRect()
#     r2 = EllipseItem(rotated).boundingRect()

#     # 未旋转：横长竖短；旋转 90°：横短竖长
#     assert r1.width() > r1.height()
#     assert r2.width() < r2.height()

#     # margin 对两个 boundingRect 相同，所以宽高应精确互换
#     assert r2.width() == pytest.approx(r1.height())
#     assert r2.height() == pytest.approx(r1.width())


def test_ellipse_item_rotation(qapp):
    """旋转 90° 后，boundingRect 的宽高互换。"""
    base = Shape(type='ellipse', points=[Vec2(0, 0)], rx=2, ry=1)
    rotated = Shape(type='ellipse', points=[Vec2(0, 0)], rx=2, ry=1,
                    rotation=math.pi / 2)

    r1 = EllipseItem(base).boundingRect()
    r2 = EllipseItem(rotated).boundingRect()

    # 未旋转：横长竖短；旋转 90°：横短竖长
    assert r1.width() > r1.height()
    assert r2.width() < r2.height()

    # margin 对两个 boundingRect 相同，宽高应精确互换
    assert abs(r2.width() - r1.height()) < 1e-6
    assert abs(r2.height() - r1.width()) < 1e-6


def test_func_item(qapp):
    item = FuncItem(Shape(type='func', expr='x', xmin=0, xmax=4))
    r = item.boundingRect()
    assert r.contains(QPointF(2, 2))
    hit = item.shape()
    assert hit.contains(QPointF(2, 2))


def test_freehand_item(qapp):
    item = FreehandItem(Shape(
        type='freehand',
        points=[Vec2(0, 0), Vec2(1, 1), Vec2(2, 0)],
        closed=True,
    ))
    hit = item.shape()
    assert hit.contains(QPointF(0, 0))
    assert hit.contains(QPointF(1, 0.5))       # 封闭区域内


def test_create_item_factory(qapp):
    for t in ('point', 'segment', 'line', 'ray', 'polygon',
              'circle', 'ellipse', 'freehand', 'func'):
        s = Shape(type=t, points=[Vec2(0, 0)])
        item = create_item(s)
        assert item is not None


def test_paint_does_not_crash(qapp):
    """用离屏 QImage 验证 paint 不报错。"""
    cases = [
        Shape(type='point', points=[Vec2(1, 1)]),
        Shape(type='segment', points=[Vec2(0, 0), Vec2(3, 3)]),
        Shape(type='polygon',
              points=[Vec2(0, 0), Vec2(2, 0), Vec2(2, 2)],
              style=ShapeStyle(fill_enabled=True)),
        Shape(type='circle', points=[Vec2(0, 0)], rx=2, ry=2,
              style=ShapeStyle(fill_enabled=True, fill_algo='radial')),
        Shape(type='func', expr='sin(x)', xmin=-3, xmax=3),
    ]
    img = QImage(300, 300, QImage.Format_ARGB32)
    img.fill(0)
    painter = QPainter(img)
    try:
        for s in cases:
            create_item(s).paint(painter, None)
    finally:
        painter.end()
    assert not img.isNull()