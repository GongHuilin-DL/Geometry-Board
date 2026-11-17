"""图元层：Shape -> QGraphicsItem 工厂。"""
from items.base_item import ShapeItem
from items.primitives import (
    PointItem, SegmentItem, LineItem, RayItem,
    PolygonItem, CircleItem, EllipseItem,
)
from items.curve_items import FuncItem, FreehandItem


ITEM_CLASSES = {
    'point':    PointItem,
    'segment':  SegmentItem,
    'line':     LineItem,
    'ray':      RayItem,
    'polygon':  PolygonItem,
    'circle':   CircleItem,
    'ellipse':  EllipseItem,
    'freehand': FreehandItem,
    'func':     FuncItem,
}


def create_item(shape) -> ShapeItem:
    """根据 Shape 创建对应的图元；未知类型回退为 PolygonItem。"""
    cls = ITEM_CLASSES.get(shape.type, PolygonItem)
    return cls(shape)


__all__ = [
    'ShapeItem', 'create_item', 'ITEM_CLASSES',
    'PointItem', 'SegmentItem', 'LineItem', 'RayItem',
    'PolygonItem', 'CircleItem', 'EllipseItem',
    'FuncItem', 'FreehandItem',
]