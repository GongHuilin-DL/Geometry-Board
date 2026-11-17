"""临时验证脚本：把 items/ 层全部图元画到屏幕上，确认无误后可删。"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView

from core.geometry import Vec2
from core.model import Shape, ShapeStyle
from items import create_item
from items.star_hexagon import make_star_points, make_hexagon_points


def main():
    app = QApplication(sys.argv)
    view = QGraphicsView()
    view.setRenderHint(QPainter.Antialiasing, True)
    view.scale(1, -1)                     # 关键：y 轴翻转，世界坐标 → 场景坐标
    scene = QGraphicsScene()
    view.setScene(scene)
    view.setSceneRect(-10, -10, 20, 20)

    shapes = [
        Shape(type='point', points=[Vec2(-8, 8)]),
        Shape(type='segment', points=[Vec2(-6, 6), Vec2(-3, 6)]),
        Shape(type='line', points=[Vec2(-6, 4), Vec2(-3, 4)],
              style=ShapeStyle(stroke='#ef4444', dash='dashed')),
        Shape(type='ray', points=[Vec2(-6, 2), Vec2(-3, 2)],
              style=ShapeStyle(stroke='#22c55e')),
        Shape(type='polygon',
              points=[Vec2(-6, -2), Vec2(-3, -2), Vec2(-4.5, -5)],
              style=ShapeStyle(fill_enabled=True, fill_color='#bfdbfe')),
        Shape(type='polygon', points=make_star_points(Vec2(3, 4), 2),
              style=ShapeStyle(stroke='#f59e0b', fill_enabled=True,
                               fill_color='#fde68a')),
        Shape(type='polygon', points=make_hexagon_points(Vec2(3, -1), 2),
              style=ShapeStyle(stroke='#8b5cf6', fill_enabled=True,
                               fill_algo='hatch', fill_color='#ddd6fe')),
        Shape(type='circle', points=[Vec2(-8, -4)], rx=2, ry=2,
              style=ShapeStyle(fill_enabled=True, fill_algo='radial',
                               fill_color='#fca5a5')),
        Shape(type='ellipse', points=[Vec2(3, -6)], rx=3, ry=1.5,
              style=ShapeStyle(fill_enabled=True, fill_algo='linear',
                               fill_color='#86efac')),
        Shape(type='func', expr='sin(x)', xmin=-9, xmax=9,
              style=ShapeStyle(stroke='#dc2626', line_width=3)),
        Shape(type='freehand',
              points=[Vec2(-2, 6), Vec2(-1, 7), Vec2(0, 6.5), Vec2(1, 7.5)],
              style=ShapeStyle(stroke='#0ea5e9')),
    ]

    for s in shapes:
        scene.addItem(create_item(s))

    view.resize(800, 800)
    view.setWindowTitle('items 层验证')
    view.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()