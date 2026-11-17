"""UI 层测试。"""
import math

import pytest

from core.geometry import Vec2
from core.model import Shape, ShapeStyle
from items import create_item
from scene.board_scene import BoardScene
from ui.dialogs import coeffs_to_expr
from ui.view import BoardView


@pytest.fixture
def view(qapp):
    scene = BoardScene()
    v = BoardView(scene)
    v.resize(800, 600)
    return v


# ---------------------------------------------------------- 图形构造
def test_build_segment(qapp):
    s = BoardView._build_drag_shape('segment', Vec2(0, 0), Vec2(2, 3))
    assert s.type == 'segment'
    assert s.points[1].is_close(Vec2(2, 3))


def test_build_rect(qapp):
    s = BoardView._build_drag_shape('rect', Vec2(0, 0), Vec2(2, 3))
    assert s.type == 'polygon'
    assert len(s.points) == 4
    xs = [p.x for p in s.points]
    ys = [p.y for p in s.points]
    assert min(xs) == 0 and max(xs) == 2
    assert min(ys) == 0 and max(ys) == 3


def test_build_triangle(qapp):
    s = BoardView._build_drag_shape('triangle', Vec2(0, 0), Vec2(4, 3))
    assert s.type == 'polygon'
    assert len(s.points) == 3


def test_build_star(qapp):
    s = BoardView._build_drag_shape('star', Vec2(0, 0), Vec2(0, 2))
    assert s.type == 'polygon'
    assert len(s.points) == 10  # 5 角星 = 10 顶点


def test_build_hexagon(qapp):
    s = BoardView._build_drag_shape('hexagon', Vec2(0, 0), Vec2(0, 2))
    assert s.type == 'polygon'
    assert len(s.points) == 6


def test_build_circle(qapp):
    s = BoardView._build_drag_shape('circle', Vec2(1, 1), Vec2(1, 4))
    assert s.type == 'circle'
    assert s.rx == pytest.approx(3)


def test_build_ellipse(qapp):
    s = BoardView._build_drag_shape('ellipse', Vec2(0, 0), Vec2(3, 2))
    assert s.type == 'ellipse'
    assert s.rx == pytest.approx(3)
    assert s.ry == pytest.approx(2)


def test_build_degenerate_returns_none(qapp):
    assert BoardView._build_drag_shape('circle', Vec2(0, 0), Vec2(0, 0)) is None
    assert BoardView._build_drag_shape('star', Vec2(0, 0), Vec2(0, 0)) is None


# ---------------------------------------------------------- 工具切换
def test_set_tool(view):
    view.set_tool('point')
    assert view.current_tool == 'point'
    view.set_tool('select')
    assert view.current_tool == 'select'


# ---------------------------------------------------------- 多项式表达式
def test_coeffs_to_expr_quadratic():
    assert coeffs_to_expr([1, 0, 0]) == 'x**2'
    assert coeffs_to_expr([2, 3, 1]) == '2*x**2 + 3*x + 1'


def test_coeffs_to_expr_negative_leading():
    assert coeffs_to_expr([-1, 0, 0]) == '-x**2'
    assert coeffs_to_expr([-2, 3]) == '-2*x + 3'


def test_coeffs_to_expr_zero():
    assert coeffs_to_expr([0, 0, 0]) == '0'
    assert coeffs_to_expr([1, 0]) == 'x'