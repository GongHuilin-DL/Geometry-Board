"""scene 层单元测试。"""
from PySide6.QtCore import QPointF

from core.geometry import Vec2
from core.model import Shape, ShapeStyle
from scene.board_scene import BoardScene


def _pt(x=0, y=0):
    return Shape(type='point', points=[Vec2(x, y)])


def _seg(a=(0, 0), b=(1, 1)):
    return Shape(type='segment', points=[Vec2(*a), Vec2(*b)])


# ---------------------------------------------------------- 增删
def test_add_shape(qapp):
    scene = BoardScene()
    s = _pt(1, 1)
    scene.add_shape(s)
    assert len(scene.shapes) == 1
    assert s.id in scene.shape_items


def test_add_undo_redo(qapp):
    scene = BoardScene()
    s = _pt()
    scene.add_shape(s)
    scene.undo()
    assert len(scene.shapes) == 0
    assert s.id not in scene.shape_items
    scene.redo()
    assert len(scene.shapes) == 1
    assert s.id in scene.shape_items


def test_remove_shape(qapp):
    scene = BoardScene()
    s = _pt()
    scene.add_shape(s)
    scene.remove_shape(s.id)
    assert len(scene.shapes) == 0
    assert s.id not in scene.shape_items
    scene.undo()
    assert len(scene.shapes) == 1
    assert s.id in scene.shape_items


def test_remove_selected_multi(qapp):
    scene = BoardScene()
    s1, s2 = _pt(0, 0), _pt(5, 5)
    scene.add_shape(s1)
    scene.add_shape(s2)
    scene.shape_items[s1.id].setSelected(True)
    scene.remove_selected()
    assert len(scene.shapes) == 1
    assert scene.shapes[0].id == s2.id
    scene.undo()
    assert len(scene.shapes) == 2


# ---------------------------------------------------------- 修改
def test_modify_shape_undo_redo(qapp):
    scene = BoardScene()
    s = _seg((0, 0), (1, 1))
    scene.add_shape(s)

    def move(sh):
        sh.points = [Vec2(p.x + 5, p.y + 5) for p in sh.points]

    scene.modify_shape(s.id, move, '移动')
    assert scene.shapes[0].points[0].is_close(Vec2(5, 5))
    scene.undo()
    assert scene.shapes[0].points[0].is_close(Vec2(0, 0))
    scene.redo()
    assert scene.shapes[0].points[0].is_close(Vec2(5, 5))


def test_modify_shape_no_change(qapp):
    scene = BoardScene()
    s = _pt()
    scene.add_shape(s)
    n = len(scene.history._undo)
    scene.modify_shape(s.id, lambda sh: None)
    assert len(scene.history._undo) == n


# ---------------------------------------------------------- 样式
def test_apply_style_undo(qapp):
    scene = BoardScene()
    s = _seg()
    scene.add_shape(s)
    scene.apply_style([s.id], {'stroke': '#ff0000', 'line_width': 5})
    assert scene.shapes[0].style.stroke == '#ff0000'
    assert scene.shapes[0].style.line_width == 5
    scene.undo()
    assert scene.shapes[0].style.stroke == '#1d4ed8'
    assert scene.shapes[0].style.line_width == 2


def test_apply_style_no_change(qapp):
    scene = BoardScene()
    s = _seg()
    scene.add_shape(s)
    n = len(scene.history._undo)
    scene.apply_style([s.id], {'stroke': s.style.stroke})
    assert len(scene.history._undo) == n


def test_apply_style_multi_single_undo(qapp):
    scene = BoardScene()
    s1, s2 = _pt(0, 0), _pt(1, 1)
    scene.add_shape(s1)
    scene.add_shape(s2)
    scene.apply_style([s1.id, s2.id], {'stroke': '#00ff00'})
    assert scene.shapes[0].style.stroke == '#00ff00'
    assert scene.shapes[1].style.stroke == '#00ff00'
    scene.undo()
    assert scene.shapes[0].style.stroke == '#1d4ed8'
    assert scene.shapes[1].style.stroke == '#1d4ed8'


# ---------------------------------------------------------- 拖拽
def test_drag_single(qapp):
    scene = BoardScene()
    s = _seg((0, 0), (1, 1))
    scene.add_shape(s)
    scene.shape_items[s.id].setSelected(True)

    scene._begin_drag(QPointF(0, 0))
    scene._update_drag(QPointF(3, 4))
    scene._end_drag()

    assert scene.shapes[0].points[0].is_close(Vec2(3, 4))
    assert scene.shapes[0].points[1].is_close(Vec2(4, 5))

    scene.undo()
    assert scene.shapes[0].points[0].is_close(Vec2(0, 0))
    assert scene.shapes[0].points[1].is_close(Vec2(1, 1))


def test_drag_no_move_no_command(qapp):
    scene = BoardScene()
    s = _pt(5, 5)
    scene.add_shape(s)
    scene.shape_items[s.id].setSelected(True)
    n = len(scene.history._undo)
    scene._begin_drag(QPointF(0, 0))
    scene._end_drag()
    assert len(scene.history._undo) == n


def test_drag_multi_single_undo(qapp):
    scene = BoardScene()
    s1, s2 = _pt(0, 0), _pt(10, 10)
    scene.add_shape(s1)
    scene.add_shape(s2)
    scene.shape_items[s1.id].setSelected(True)
    scene.shape_items[s2.id].setSelected(True)

    scene._begin_drag(QPointF(0, 0))
    scene._update_drag(QPointF(2, 3))
    scene._end_drag()

    assert scene.shapes[0].points[0].is_close(Vec2(2, 3))
    assert scene.shapes[1].points[0].is_close(Vec2(12, 13))

    scene.undo()
    assert scene.shapes[0].points[0].is_close(Vec2(0, 0))
    assert scene.shapes[1].points[0].is_close(Vec2(10, 10))


def test_drag_uses_initial_snapshot(qapp):
    """多次 update 后仍以初始快照为准，不累积误差。"""
    scene = BoardScene()
    s = _pt(0, 0)
    scene.add_shape(s)
    scene.shape_items[s.id].setSelected(True)
    scene._begin_drag(QPointF(0, 0))
    scene._update_drag(QPointF(1, 1))
    scene._update_drag(QPointF(2, 2))
    scene._update_drag(QPointF(5, 5))
    scene._end_drag()
    assert scene.shapes[0].points[0].is_close(Vec2(5, 5))


# ---------------------------------------------------------- 选择
def test_selected_shapes(qapp):
    scene = BoardScene()
    s1, s2 = _pt(0, 0), _pt(5, 5)
    scene.add_shape(s1)
    scene.add_shape(s2)
    scene.shape_items[s1.id].setSelected(True)
    scene.shape_items[s2.id].setSelected(True)
    assert len(scene.selected_shapes()) == 2


def test_find_shape(qapp):
    scene = BoardScene()
    s = _pt(1, 1)
    scene.add_shape(s)
    assert scene.find_shape(s.id) is s
    assert scene.find_shape('nonexistent') is None