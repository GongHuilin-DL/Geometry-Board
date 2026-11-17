# 几何运算单元测试
"""core.geometry 单元测试。"""
import math

import pytest

from core.geometry import (
    Vec2, BBox, EPS,
    almost_equal,
    point_to_line_distance, point_to_segment_distance, point_to_ray_distance,
    closest_point_on_segment,
    segment_intersection, segments_intersect,
    polygon_area_signed, polygon_area, polygon_perimeter,
    point_in_polygon, convex_hull,
    translate_points, rotate_points, scale_points,
    deg_to_rad, rad_to_deg, normalize_angle,
)


# ----------------------------------------------------------- Vec2 基础
def test_vec2_arithmetic():
    a, b = Vec2(1, 2), Vec2(3, 4)
    assert a + b == Vec2(4, 6)
    assert b - a == Vec2(2, 2)
    assert a * 3 == Vec2(3, 6)
    assert 3 * a == Vec2(3, 6)
    assert a / 2 == Vec2(0.5, 1.0)
    assert -a == Vec2(-1, -2)


def test_vec2_dot_cross_length():
    assert Vec2(1, 0).dot(Vec2(0, 1)) == 0
    assert Vec2(1, 2).dot(Vec2(3, 4)) == 11
    assert Vec2(1, 0).cross(Vec2(0, 1)) == 1
    assert Vec2(3, 4).length() == pytest.approx(5.0)
    assert Vec2(3, 4).normalized().is_close(Vec2(0.6, 0.8))


def test_vec2_rotate():
    r = Vec2(1, 0).rotate(math.pi / 2)
    assert r.is_close(Vec2(0, 1), 1e-12)
    r2 = Vec2(2, 0).rotate(math.pi)
    assert r2.is_close(Vec2(-2, 0), 1e-12)


def test_vec2_distance_and_hash():
    assert Vec2(0, 0).distance_to(Vec2(3, 4)) == pytest.approx(5.0)
    s = {Vec2(1, 2), Vec2(1, 2), Vec2(3, 4)}
    assert len(s) == 2


# ----------------------------------------------------------- BBox
def test_bbox_from_points():
    bb = BBox.from_points([Vec2(-1, -2), Vec2(3, 4), Vec2(0, 0)])
    assert bb.xmin == -1 and bb.ymin == -2
    assert bb.xmax == 3 and bb.ymax == 4
    assert bb.width() == 4 and bb.height() == 6
    assert bb.center().is_close(Vec2(1, 1))


def test_bbox_contains_and_union():
    bb = BBox(0, 0, 2, 2)
    assert bb.contains(Vec2(1, 1))
    assert bb.contains(Vec2(0, 0))      # 边上算在内
    assert not bb.contains(Vec2(3, 3))
    bb2 = BBox(1, 1, 5, 4)
    u = bb.union(bb2)
    assert u.xmax == 5 and u.ymax == 4
    e = bb.expand(1)
    assert e.xmin == -1 and e.xmax == 3


# ----------------------------------------------------------- 距离
def test_point_to_line_distance():
    assert point_to_line_distance(Vec2(0, 5), Vec2(-10, 0), Vec2(10, 0)) == pytest.approx(5.0)
    # 退化
    assert point_to_line_distance(Vec2(1, 0), Vec2(0, 0), Vec2(0, 0)) == pytest.approx(1.0)


def test_point_to_segment_distance():
    # 投影落在线段内
    assert point_to_segment_distance(Vec2(0, 5), Vec2(-10, 0), Vec2(10, 0)) == pytest.approx(5.0)
    # 投影落在线段外（左侧）
    assert point_to_segment_distance(Vec2(-20, 0), Vec2(-10, 0), Vec2(10, 0)) == pytest.approx(10.0)
    # 退化
    assert point_to_segment_distance(Vec2(1, 0), Vec2(0, 0), Vec2(0, 0)) == pytest.approx(1.0)


def test_point_to_ray_distance():
    a, b = Vec2(0, 0), Vec2(1, 0)
    assert point_to_ray_distance(Vec2(5, 3), a, b) == pytest.approx(3.0)
    assert point_to_ray_distance(Vec2(-5, 3), a, b) == pytest.approx(math.hypot(5, 3))


def test_closest_point_on_segment():
    c = closest_point_on_segment(Vec2(0, 5), Vec2(-10, 0), Vec2(10, 0))
    assert c.is_close(Vec2(0, 0))
    c2 = closest_point_on_segment(Vec2(-20, 0), Vec2(-10, 0), Vec2(10, 0))
    assert c2.is_close(Vec2(-10, 0))


# ----------------------------------------------------------- 线段相交
def test_segment_intersection():
    p = segment_intersection(Vec2(0, 0), Vec2(2, 2), Vec2(0, 2), Vec2(2, 0))
    assert p is not None and p.is_close(Vec2(1, 1))


def test_segment_no_intersection_parallel():
    assert segment_intersection(Vec2(0, 0), Vec2(2, 0), Vec2(0, 1), Vec2(2, 1)) is None


def test_segment_no_intersection_disjoint():
    assert segment_intersection(Vec2(0, 0), Vec2(1, 0), Vec2(2, 0), Vec2(3, 0)) is None


def test_segments_intersect_collinear_overlap():
    assert segments_intersect(Vec2(0, 0), Vec2(2, 0), Vec2(1, 0), Vec2(3, 0))
    assert not segments_intersect(Vec2(0, 0), Vec2(1, 0), Vec2(2, 0), Vec2(3, 0))


def test_segments_intersect_endpoint_touch():
    assert segments_intersect(Vec2(0, 0), Vec2(1, 0), Vec2(1, 0), Vec2(2, 0))


# ----------------------------------------------------------- 多边形
def test_polygon_area_square():
    sq = [Vec2(0, 0), Vec2(2, 0), Vec2(2, 2), Vec2(0, 2)]
    assert polygon_area_signed(sq) == pytest.approx(4.0)
    assert polygon_area(sq) == pytest.approx(4.0)
    # 反序为负
    assert polygon_area_signed(list(reversed(sq))) == pytest.approx(-4.0)


def test_polygon_area_triangle():
    tri = [Vec2(0, 0), Vec2(4, 0), Vec2(0, 3)]
    assert polygon_area(tri) == pytest.approx(6.0)


def test_polygon_perimeter():
    sq = [Vec2(0, 0), Vec2(2, 0), Vec2(2, 2), Vec2(0, 2)]
    assert polygon_perimeter(sq) == pytest.approx(8.0)


def test_point_in_polygon():
    sq = [Vec2(0, 0), Vec2(2, 0), Vec2(2, 2), Vec2(0, 2)]
    assert point_in_polygon(Vec2(1, 1), sq)
    assert point_in_polygon(Vec2(0, 1), sq)        # 边上
    assert not point_in_polygon(Vec2(3, 1), sq)
    assert not point_in_polygon(Vec2(-0.5, 1), sq)


# def test_convex_hull():
#     pts = [Vec2(0, 0), Vec2(1, 0), Vec2(0.5, 0.5), Vec2(1, 1), Vec2(0, 1), Vec2(0.5, -1)]
#     hull = convex_hull(pts)
#     # 凸包应包含 4 个外顶点（去掉内部点 (0.5,0.5)）
#     assert len(hull) == 4
#     # 顶点按逆时针顺序，面积 = 多边形面积
#     assert polygon_area(hull) == pytest.approx(1.5)

def test_convex_hull_excludes_interior():
    """四边形 + 内部点：内部点应被剔除，凸包为 4 顶点。"""
    pts = [Vec2(0, 0), Vec2(2, 0), Vec2(2, 2), Vec2(0, 2), Vec2(1, 1)]
    hull = convex_hull(pts)
    assert len(hull) == 4
    # 逆时针顺序，面积为 4
    assert polygon_area(hull) == pytest.approx(4.0)
    # 内部点不在凸包顶点中
    assert Vec2(1, 1) not in hull


def test_convex_hull_with_bottom_protrusion():
    """五边形：底部外凸点 (0.5,-1) 也是凸包顶点，共 5 个。"""
    pts = [Vec2(0, 0), Vec2(1, 0), Vec2(0.5, 0.5),
           Vec2(1, 1), Vec2(0, 1), Vec2(0.5, -1)]
    hull = convex_hull(pts)
    assert len(hull) == 5
    assert polygon_area(hull) == pytest.approx(1.5)
    # 内部点 (0.5, 0.5) 被剔除
    assert Vec2(0.5, 0.5) not in hull

def test_convex_hull_degenerate():
    assert convex_hull([]) == []
    assert convex_hull([Vec2(1, 1)]) == [Vec2(1, 1)]
    two = convex_hull([Vec2(0, 0), Vec2(1, 1)])
    assert len(two) == 2


# ----------------------------------------------------------- 变换
def test_translate_points():
    pts = translate_points([Vec2(0, 0), Vec2(1, 1)], 2, -3)
    assert pts[0] == Vec2(2, -3)
    assert pts[1] == Vec2(3, -2)


def test_rotate_points_around_center():
    pts = rotate_points([Vec2(1, 0)], Vec2(0, 0), math.pi / 2)
    assert pts[0].is_close(Vec2(0, 1), 1e-12)


def test_scale_points():
    pts = scale_points([Vec2(1, 1)], Vec2(0, 0), 2)
    assert pts[0] == Vec2(2, 2)
    # 非等比
    pts2 = scale_points([Vec2(1, 1)], Vec2(0, 0), 2, 3)
    assert pts2[0] == Vec2(2, 3)


# ----------------------------------------------------------- 角度
def test_angle_tools():
    assert deg_to_rad(180) == pytest.approx(math.pi)
    assert rad_to_deg(math.pi) == pytest.approx(180.0)
    assert normalize_angle(3 * math.pi) == pytest.approx(math.pi - 2 * math.pi) or \
           normalize_angle(3 * math.pi) == pytest.approx(math.pi)
    assert normalize_angle(2 * math.pi) == pytest.approx(0.0, abs=1e-12)


def test_almost_equal():
    assert almost_equal(1.0, 1.0 + 1e-10)
    assert not almost_equal(1.0, 1.1)