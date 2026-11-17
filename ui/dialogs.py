# 对话框：函数输入、多项式配置、填充设置
"""对话框：函数输入、多项式输入。"""
from __future__ import annotations

from typing import Optional, Tuple
from typing import List, Union
Number = Union[int, float]

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QLabel, QLineEdit, QSpinBox, QVBoxLayout,
)


class FunctionDialog(QDialog):
    def __init__(self, default_domain: Tuple[float, float], parent=None):
        super().__init__(parent)
        self.setWindowTitle('函数曲线')
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        hint = QLabel('可用：sin cos tan sqrt abs exp log pow PI E，^ 表示幂\n例：sin(x)、x^2-3*x+1、sqrt(abs(x))')
        hint.setStyleSheet('color:#94a3b8;font-size:11px;')
        layout.addWidget(hint)

        form = QFormLayout()
        self.expr_edit = QLineEdit('sin(x)')
        self.xmin_spin = QDoubleSpinBox()
        self.xmax_spin = QDoubleSpinBox()
        for sp in (self.xmin_spin, self.xmax_spin):
            sp.setRange(-1e6, 1e6)
            sp.setDecimals(2)
            sp.setSingleStep(0.5)
        self.xmin_spin.setValue(default_domain[0])
        self.xmax_spin.setValue(default_domain[1])

        form.addRow('表达式 f(x)', self.expr_edit)
        form.addRow('定义域 左', self.xmin_spin)
        form.addRow('定义域 右', self.xmax_spin)
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def result_data(self) -> Optional[dict]:
        expr = self.expr_edit.text().strip()
        xmin, xmax = self.xmin_spin.value(), self.xmax_spin.value()
        if not expr or xmax <= xmin:
            return None
        return {'expr': expr, 'xmin': xmin, 'xmax': xmax}


class PolynomialDialog(QDialog):
    def __init__(self, default_domain: Tuple[float, float], parent=None):
        super().__init__(parent)
        self.setWindowTitle('多项式曲线')
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        hint = QLabel('系数按「最高次 → 常数项」顺序，用逗号分隔\n例：次数 3，系数 1,0,-2,1 → x³ - 2x + 1')
        hint.setStyleSheet('color:#94a3b8;font-size:11px;')
        layout.addWidget(hint)

        form = QFormLayout()
        self.degree_spin = QSpinBox()
        self.degree_spin.setRange(0, 20)
        self.degree_spin.setValue(2)
        self.coef_edit = QLineEdit('1, 0, 0')
        self.xmin_spin = QDoubleSpinBox()
        self.xmax_spin = QDoubleSpinBox()
        for sp in (self.xmin_spin, self.xmax_spin):
            sp.setRange(-1e6, 1e6)
            sp.setDecimals(2)
            sp.setSingleStep(0.5)
        self.xmin_spin.setValue(default_domain[0])
        self.xmax_spin.setValue(default_domain[1])

        form.addRow('次数 n', self.degree_spin)
        form.addRow('系数', self.coef_edit)
        form.addRow('定义域 左', self.xmin_spin)
        form.addRow('定义域 右', self.xmax_spin)
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def result_data(self) -> Optional[dict]:
        n = self.degree_spin.value()
        try:
            cs = [float(x) for x in
                  self.coef_edit.text().replace('，', ',').replace(' ', ',').split(',')
                  if x.strip()]
        except ValueError:
            return None
        while len(cs) < n + 1:
            cs.append(0.0)
        cs = cs[:n + 1]
        xmin, xmax = self.xmin_spin.value(), self.xmax_spin.value()
        if xmax <= xmin:
            return None
        return {'coeffs': cs, 'xmin': xmin, 'xmax': xmax}


def coeffs_to_expr(coeffs: list[float]) -> str:
    """系数（最高次→常数项）转合法表达式，幂用 **，首项为负时用 -(...) 包裹。"""
    n = len(coeffs) - 1
    parts = []
    for i, c in enumerate(coeffs):
        p = n - i
        if c == 0:
            continue
        abs_c = abs(c)
        if p == 0:
            term = _fmt(abs_c)
        elif p == 1:
            term = ('x' if abs_c == 1 else f'{_fmt(abs_c)}*x')
        else:
            term = (f'x**{p}' if abs_c == 1 else f'{_fmt(abs_c)}*x**{p}')
        if not parts:
            parts.append(('-' + term) if c < 0 else term)
        else:
            parts.append((' - ' if c < 0 else ' + ') + term)
    return ''.join(parts) or '0'


def _fmt(v) -> str:
    """把数值转成字符串：整数值不带小数点，否则保留原样。"""
    try:
        iv = int(v)
        if v == iv:
            return str(iv)
    except (TypeError, ValueError, OverflowError):
        pass
    return str(v)