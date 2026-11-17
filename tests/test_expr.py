"""core.expr 单元测试。"""
import math

import pytest

from core.expr import (
    ExprEvaluator, ExpressionError,
    evaluate, is_valid_expr, sample_curve,
)
from core.geometry import Vec2


def test_basic_evaluate():
    assert evaluate('x + 1', 2) == pytest.approx(3.0)
    assert evaluate('x * x', 3) == pytest.approx(9.0)
    assert evaluate('sin(x)', 0) == pytest.approx(0.0)
    assert evaluate('cos(x)', 0) == pytest.approx(1.0)


def test_caret_power_conversion():
    assert evaluate('x^2', 3) == pytest.approx(9.0)
    assert evaluate('x^3', 2) == pytest.approx(8.0)
    assert evaluate('2^x', 3) == pytest.approx(8.0)
    # 与 ** 等价
    assert evaluate('x^2', 3) == evaluate('x**2', 3)


def test_constants():
    assert evaluate('pi', 0) == pytest.approx(math.pi)
    assert evaluate('e', 0) == pytest.approx(math.e)
    assert evaluate('PI', 0) == pytest.approx(math.pi)


def test_nan_on_domain_error():
    assert math.isnan(evaluate('sqrt(x)', -1))
    assert math.isnan(evaluate('log(x)', -1))


def test_invalid_expr():
    assert not is_valid_expr('import os')
    assert not is_valid_expr('__import__("os")')
    assert not is_valid_expr('x +')
    assert is_valid_expr('x + 1')
    assert math.isnan(evaluate('x +', 1))


def test_evaluator_cache():
    ev = ExprEvaluator()
    assert ev.evaluate('x^2', 3) == pytest.approx(9.0)
    # 第二次走缓存，结果一致
    assert ev.evaluate('x^2', 4) == pytest.approx(16.0)


def test_sample_curve():
    pts = sample_curve('x', 0, 10, 11)
    assert len(pts) == 11
    assert pts[0].is_close(Vec2(0, 0), 1e-12)
    assert pts[-1].is_close(Vec2(10, 10), 1e-12)


def test_sample_skips_invalid():
    # 在 [-1, 1] 上有非定义域段
    pts = sample_curve('sqrt(x)', -1, 1, 21)
    assert all(p.x >= 0 for p in pts)
    assert all(math.isfinite(p.y) for p in pts)


def test_sample_invalid_domain():
    assert sample_curve('x', 1, 0) == []
    assert sample_curve('import os', 0, 1) == []


def test_expression_error_raised():
    ev = ExprEvaluator()
    with pytest.raises(ExpressionError):
        ev._get_compiled('import os')