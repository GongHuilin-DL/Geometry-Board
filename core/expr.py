# 表达式：asteval 封装，表达式校验、采样、定义域裁剪
"""函数表达式求值，基于 asteval 沙箱。

对外暴露：
- ExpressionError：非法表达式异常
- ExprEvaluator：可缓存的求值器（编译一次，多次求值）
- evaluate / is_valid_expr / sample_curve：全局便捷函数

设计要点：
- asteval 预编译（parse），批量采样时 run 不重复解析。
- 数学写法 ^ 自动转换为 Python 的 **。
- 求值失败统一返回 nan，上层只判断 isfinite。
"""
from __future__ import annotations

import ast
import math
from typing import Any, Dict, List, Tuple

from asteval import Interpreter

from .geometry import Vec2


class ExpressionError(ValueError):
    """表达式非法（语法错误、非法符号等）。"""


def _normalize(expr: str) -> str:
    """把数学写法 ^ 转换为 Python 的 **，去首尾空白。"""
    return (expr or '').strip().replace('^', '**')


def _format_errors(errors) -> str:
    parts = []
    for e in errors:
        try:
            parts.append(str(e.get_error()[1]))
        except Exception:
            parts.append(str(e))
    return '; '.join(parts) if parts else '未知错误'


class _Compiled:
    """内部编译产物：interp + AST node。"""

    __slots__ = ('interp', 'node')

    def __init__(self, interp: Interpreter, node: Any):
        self.interp = interp
        self.node = node


class ExprEvaluator:
    """表达式求值器，内部缓存编译结果。"""

    def __init__(self):
        self._cache: Dict[str, _Compiled] = {}
        self._consts = {'pi': math.pi, 'e': math.e, 'PI': math.pi, 'E': math.e}

    # ------------------------------------------------------------ 编译
    def _get_compiled(self, expr: str) -> _Compiled:
        key = _normalize(expr)
        if not key:
            raise ExpressionError('表达式为空')

        compiled = self._cache.get(key)
        if compiled is not None:
            return compiled

        interp = Interpreter()
        for k, v in self._consts.items():
            interp.symtable[k] = v

        try:
            node = interp.parse(key)
        except Exception as e:
            interp.error.clear()
            raise ExpressionError(f'表达式非法: {e}') from e

        if interp.error:
            msg = _format_errors(interp.error)
            interp.error.clear()
            raise ExpressionError(f'表达式非法: {msg}')

        # parse() 不负责安全拦截，这里显式检查 import 语句和 __import__ 调用
        for n in ast.walk(node):
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                raise ExpressionError('不允许使用 import 语句')
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                    and n.func.id == '__import__':
                raise ExpressionError('不允许调用 __import__')

        compiled = _Compiled(interp, node)
        self._cache[key] = compiled
        return compiled

    # ------------------------------------------------------------ 求值
    def evaluate(self, expr: str, x: float) -> float:
        """单点求值，失败返回 nan。"""
        try:
            compiled = self._get_compiled(expr)
        except ExpressionError:
            return float('nan')

        compiled.interp.symtable['x'] = float(x)
        try:
            result = compiled.interp.run(compiled.node)
        except Exception:
            result = None

        if compiled.interp.error:
            compiled.interp.error.clear()
            return float('nan')

        if isinstance(result, bool):  # bool 是 int 子类，这里要排除
            return float('nan')
        if not isinstance(result, (int, float)):
            return float('nan')
        try:
            v = float(result)
        except (TypeError, ValueError):
            return float('nan')
        return v if math.isfinite(v) else float('nan')

    def is_valid(self, expr: str) -> bool:
        try:
            self._get_compiled(expr)
            return True
        except ExpressionError:
            return False

    def sample(self, expr: str, xmin: float, xmax: float,
               n: int = 800) -> List[Vec2]:
        """均匀采样，返回有效 (x, y) 点列表。"""
        if n < 2:
            n = 2
        if xmax <= xmin:
            return []

        try:
            compiled = self._get_compiled(expr)
        except ExpressionError:
            return []

        interp = compiled.interp
        node = compiled.node
        pts: List[Vec2] = []
        step = (xmax - xmin) / (n - 1)

        for i in range(n):
            x = xmin + step * i
            interp.symtable['x'] = x
            try:
                y = interp.run(node)
            except Exception:
                interp.error.clear()
                continue
            if interp.error:
                interp.error.clear()
                continue
            if isinstance(y, bool) or not isinstance(y, (int, float)):
                continue
            y = float(y)
            if math.isfinite(y) and abs(y) < 1e6:
                pts.append(Vec2(x, y))

        return pts


# ---------------------------------------------------------------- 全局实例
_default = ExprEvaluator()


def evaluate(expr: str, x: float) -> float:
    return _default.evaluate(expr, x)


def is_valid_expr(expr: str) -> bool:
    return _default.is_valid(expr)


def sample_curve(expr: str, xmin: float, xmax: float, n: int = 800) -> List[Vec2]:
    return _default.sample(expr, xmin, xmax, n)