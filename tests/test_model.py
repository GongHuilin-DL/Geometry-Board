"""core.model 单元测试。"""
import math

import pytest

from core.geometry import Vec2
from core.model import (
    Shape, ShapeStyle, SHAPE_TYPES, DASH_STYLES, FILL_ALGORITHMS,
)


def test_style_default():
    st = ShapeStyle()
    assert st.stroke == '#1d4ed8'
    assert st.line_width == 2.0
    assert st.dash == 'solid'
    assert st.fill_enabled is False


def test_style_roundtrip():
    st = ShapeStyle(stroke='#ff0000', line_width=3.5, dash='dashed',
                    fill_enabled=True, fill_color='#00ff00', fill_algo='hatch')
    d = st.to_dict()
    st2 = ShapeStyle.from_dict(d)
    assert st2 == st


def test_style_from_dict_invalid_dash():
    st = ShapeStyle.from_dict({'dash': 'unknown', 'fill_algo': 'xx'})
    assert st.dash == 'solid'
    assert st.fill_algo == 'solid'


def test_shape_default():
    s = Shape()
    assert s.type == 'point'
    assert s.id.startswith('s')
    assert s.points == []


def test_shape_roundtrip():
    s = Shape(
        type='polygon',
        points=[Vec2(0, 0), Vec2(1, 0), Vec2(1, 1)],
        style=ShapeStyle(stroke='#000'),
        name='三角形',
    )
    d = s.to_dict()
    s2 = Shape.from_dict(d)
    assert s2.id == s.id
    assert s2.type == s.type
    assert len(s2.points) == 3
    assert s2.points[1].is_close(Vec2(1, 0))
    assert s2.style == s.style
    assert s2.name == '三角形'


def test_shape_clone_independent():
    s = Shape(type='segment', points=[Vec2(0, 0), Vec2(1, 1)])
    c = s.clone()
    assert c is not s
    c.points[0] = Vec2(99, 99)
    assert s.points[0].is_close(Vec2(0, 0))


def test_apply_dict_inplace():
    s = Shape(type='point', points=[Vec2(0, 0)])
    before = s.to_dict()
    s.points = [Vec2(5, 5)]
    after = s.to_dict()

    s.apply_dict(before)
    assert s.points[0].is_close(Vec2(0, 0))
    s.apply_dict(after)
    assert s.points[0].is_close(Vec2(5, 5))
    # id 不变
    assert s.id == before['id']


def test_is_fillable():
    assert Shape(type='polygon').is_fillable()
    assert Shape(type='circle').is_fillable()
    assert Shape(type='ellipse').is_fillable()
    assert Shape(type='freehand', closed=True).is_fillable()
    assert not Shape(type='freehand', closed=False).is_fillable()
    assert not Shape(type='segment').is_fillable()
    assert not Shape(type='func').is_fillable()


def test_bounding_box_polygon():
    s = Shape(type='polygon', points=[Vec2(0, 0), Vec2(4, 0), Vec2(4, 3)])
    bb = s.bounding_box()
    assert bb.xmin == 0 and bb.xmax == 4
    assert bb.ymin == 0 and bb.ymax == 3
    c = s.center()
    assert c.x == pytest.approx(2.0)
    assert c.y == pytest.approx(1.5)


def test_bounding_box_circle():
    s = Shape(type='circle', points=[Vec2(1, 2)], rx=3, ry=3)
    bb = s.bounding_box()
    assert bb.xmin == pytest.approx(-2)
    assert bb.xmax == pytest.approx(4)
    assert bb.ymin == pytest.approx(-1)
    assert bb.ymax == pytest.approx(5)


def test_bounding_box_rotated_ellipse():
    s = Shape(type='ellipse', points=[Vec2(0, 0)], rx=2, ry=1,
              rotation=math.pi / 2)
    bb = s.bounding_box()
    # 旋转 90° 后宽高互换
    assert bb.xmax - bb.xmin == pytest.approx(2.0)
    assert bb.ymax - bb.ymin == pytest.approx(4.0)


def test_bounding_box_func():
    s = Shape(type='func', expr='x', xmin=0, xmax=4)
    bb = s.bounding_box()
    assert bb.xmin == pytest.approx(0, abs=1e-6)
    assert bb.xmax == pytest.approx(4, abs=1e-6)
    assert bb.ymin == pytest.approx(0, abs=1e-6)
    assert bb.ymax == pytest.approx(4, abs=1e-6)


def test_bounding_box_empty():
    assert Shape(type='polygon').bounding_box() == Shape(type='polygon').bounding_box()
    empty_bb = Shape(type='polygon').bounding_box()
    assert empty_bb.xmin == empty_bb.xmax == 0


def test_valid_type_fallback():
    s = Shape.from_dict({'type': 'unknown', 'points': []})
    assert s.type == 'point'