"""应用入口。"""
import sys
import traceback

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def _excepthook(exc_type, exc_value, exc_tb):
    """把未捕获异常完整打到 stderr，避免 PySide6 直接终止进程时丢失信息。"""
    print('\n=== UNHANDLED EXCEPTION ===', file=sys.stderr)
    traceback.print_exception(exc_type, exc_value, exc_tb)
    print('===========================\n', file=sys.stderr)
    sys.stderr.flush()


def _build_app_font() -> QFont:
    """显式构造一个 pointSize 明确的字体。"""
    if sys.platform.startswith('win'):
        family = 'Microsoft YaHei UI'
    elif sys.platform == 'darwin':
        family = 'PingFang SC'
    else:
        family = 'Noto Sans CJK SC'
    f = QFont(family)
    f.setPointSize(10)
    return f


def main() -> int:
    sys.excepthook = _excepthook

    app = QApplication(sys.argv)
    app.setApplicationName('几何画板')
    app.setFont(_build_app_font())

    win = MainWindow()
    # 保险：窗口创建后，再对所有已存在 widget 刷新一遍字体
    for w in app.allWidgets():
        f = w.font()
        if f.pointSize() <= 0:
            f.setPointSize(10)
            w.setFont(f)

    win.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())