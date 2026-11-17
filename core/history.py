# 命令栈：Undo/Redo，Command 基类
"""命令模式与撤销重做栈。

Command 只描述行为，不持有 Scene。
History 只维护栈，执行由上层（Scene）负责。

ModifyShapeCommand 使用 to_dict 快照 + apply_dict 原地还原，
保证 shape 对象引用稳定，item 层不需要重新绑定。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .model import Shape


# ---------------------------------------------------------------- 命令基类
class Command(ABC):
    """命令基类。"""

    @abstractmethod
    def execute(self, shapes: List[Shape]) -> None: ...

    @abstractmethod
    def undo(self, shapes: List[Shape]) -> None: ...

    @property
    def label(self) -> str:
        return self.__class__.__name__

    # 受影响图形 id，Scene 用来做增量刷新
    def affected_ids(self) -> List[str]:
        return []


# ---------------------------------------------------------------- 增删
class AddShapeCommand(Command):
    def __init__(self, shape: Shape, index: Optional[int] = None):
        self.shape = shape
        self.index = index  # None 表示追加到末尾

    def execute(self, shapes: List[Shape]) -> None:
        if self.shape in shapes:
            return
        if self.index is None or self.index >= len(shapes):
            shapes.append(self.shape)
        else:
            shapes.insert(max(0, self.index), self.shape)

    def undo(self, shapes: List[Shape]) -> None:
        for i, s in enumerate(shapes):
            if s is self.shape:
                del shapes[i]
                return

    def affected_ids(self) -> List[str]:
        return [self.shape.id]

    @property
    def label(self) -> str:
        return f'添加 {self.shape.type}'


class RemoveShapeCommand(Command):
    def __init__(self, shape: Shape):
        self.shape = shape
        self.index = -1  # 首次 execute 时记录原位置

    def execute(self, shapes: List[Shape]) -> None:
        for i, s in enumerate(shapes):
            if s is self.shape:
                self.index = i
                del shapes[i]
                return

    def undo(self, shapes: List[Shape]) -> None:
        if self.shape in shapes:
            return
        idx = max(0, min(self.index if self.index >= 0 else len(shapes), len(shapes)))
        shapes.insert(idx, self.shape)

    def affected_ids(self) -> List[str]:
        return [self.shape.id]

    @property
    def label(self) -> str:
        return f'删除 {self.shape.type}'


# ---------------------------------------------------------------- 修改
class ModifyShapeCommand(Command):
    """通用修改：记录修改前后的 dict 快照。

    注意：execute 时是“把 after 写回”，而不是“重新执行修改逻辑”。
    这样与 Add/Remove 的命令语义一致，Scene 在 push 前已经做过原地修改，
    所以只需 push、无需再 execute；undo / redo 时由 History 调度。
    """

    def __init__(self, shape_id: str,
                 before: Dict[str, Any],
                 after: Dict[str, Any],
                 label: str = '修改图形'):
        self.shape_id = shape_id
        self.before = before
        self.after = after
        self._label = label

    def _apply(self, shapes: List[Shape], state: Dict[str, Any]) -> None:
        for s in shapes:
            if s.id == self.shape_id:
                s.apply_dict(state)
                return

    def execute(self, shapes: List[Shape]) -> None:
        self._apply(shapes, self.after)

    def undo(self, shapes: List[Shape]) -> None:
        self._apply(shapes, self.before)

    def affected_ids(self) -> List[str]:
        return [self.shape_id]

    @property
    def label(self) -> str:
        return self._label


# ---------------------------------------------------------------- 历史栈
class History:
    """Undo / Redo 栈。"""

    def __init__(self, max_size: int = 300):
        self._undo: List[Command] = []
        self._redo: List[Command] = []
        self.max_size = max_size

    # ---------------------------------------------------------- 查询
    def can_undo(self) -> bool:
        return bool(self._undo)

    def can_redo(self) -> bool:
        return bool(self._redo)

    def undo_label(self) -> Optional[str]:
        return self._undo[-1].label if self._undo else None

    def redo_label(self) -> Optional[str]:
        return self._redo[-1].label if self._redo else None

    # ---------------------------------------------------------- 推入
    def push(self, cmd: Command) -> None:
        """记录一个已执行过的命令。"""
        self._undo.append(cmd)
        if len(self._undo) > self.max_size:
            self._undo.pop(0)
        self._redo.clear()

    # ---------------------------------------------------------- 撤销 / 重做
    def undo(self, shapes: List[Shape]) -> Optional[Command]:
        if not self._undo:
            return None
        cmd = self._undo[-1]
        try:
            cmd.undo(shapes)
        except Exception:
            return None
        self._undo.pop()
        self._redo.append(cmd)
        return cmd

    def redo(self, shapes: List[Shape]) -> Optional[Command]:
        if not self._redo:
            return None
        cmd = self._redo[-1]
        try:
            cmd.execute(shapes)
        except Exception:
            return None
        self._redo.pop()
        self._undo.append(cmd)
        return cmd

    # ---------------------------------------------------------- 清空
    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()


class CompositeCommand(Command):
    """多个命令的组合，作为单一撤销单元。"""

    def __init__(self, commands: List[Command]):
        self.commands: List[Command] = list(commands)

    def execute(self, shapes: List[Shape]) -> None:
        for cmd in self.commands:
            cmd.execute(shapes)

    def undo(self, shapes: List[Shape]) -> None:
        for cmd in reversed(self.commands):
            cmd.undo(shapes)

    def affected_ids(self) -> List[str]:
        ids: List[str] = []
        for cmd in self.commands:
            ids.extend(cmd.affected_ids())
        return ids

    @property
    def label(self) -> str:
        return f'组合操作 ({len(self.commands)} 个)'