# 工程文件：读写 .gboard 工程
# persistence/project.py
"""工程文件读写（最小实现）。"""
from __future__ import annotations

import json

from core.model import Shape


def save_project(path: str, shapes, transform) -> None:
    data = {
        'version': 1,
        'shapes': [s.to_dict() for s in shapes],
        'view': {
            'm11': transform.m11(), 'm12': transform.m12(),
            'm21': transform.m21(), 'm22': transform.m22(),
            'dx': transform.dx(), 'dy': transform.dy(),
        } if transform is not None else None,
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_project(path: str):
    from PySide6.QtGui import QTransform
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    shapes = [Shape.from_dict(d) for d in data.get('shapes', [])]
    v = data.get('view')
    transform = QTransform(v['m11'], v['m12'], v['m21'], v['m22'], v['dx'], v['dy']) if v else None
    return shapes, transform