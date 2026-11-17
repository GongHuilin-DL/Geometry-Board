# 几何画板 · Geometry Board

一款跨平台的桌面几何画板，支持点、线、圆、多边形、函数曲线、自由曲线等图形的绘制、编辑、变换与保存。基于 **Python + PySide6 + QGraphicsView** 构建，面向 Windows 和 Linux 桌面。

---

## 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [安装与运行](#安装与运行)
- [使用指南](#使用指南)
- [项目结构](#项目结构)
- [架构说明](#架构说明)
- [开发与测试](#开发与测试)
- [已知限制](#已知限制)
- [路线图](#路线图)
- [许可证](#许可证)

---

## 功能特性

### 绘图

- **基础图形**：点、线段、直线、射线
- **多边形**：三角形、矩形、平行四边形、梯形、五角星、六边形、任意多边形（连续点击累积顶点，双击或回车结束）
- **圆与椭圆**：支持旋转
- **函数曲线**：输入任意合法表达式，支持 `^` 幂运算、`sin/cos/sqrt/log` 等数学函数，自定义定义域
- **多项式曲线**：指定次数与系数，自动生成合法表达式
- **自由曲线**：按住鼠标自由描绘轨迹

### 样式

- **描边**：颜色、粗细（0.5–30px）、线型（实线 / 虚线 / 点线 / 点划线）
- **填充**：对封闭图形生效，支持纯色、线性渐变、径向渐变、斜线、交叉、网格、点状 7 种填充算法
- 样式控件**双语义**：有选中图形时修改选中图形的样式，无选中时设定"新建图形默认样式"

### 编辑与变换

- **选中**：单击选中，青色虚线框加四个控制点标记
- **拖动平移**：选中后按住拖动，多选拖动合并为一次撤销
- **变换**：右侧面板提供平移（Δx / Δy）、旋转（绕中心，角度制）、缩放（绕中心，等比）
- **删除**：Delete 键或面板按钮
- **撤销 / 重做**：Ctrl+Z / Ctrl+Shift+Z / Ctrl+Y，命令栈深度上限 300

### 视图

- 网格背景与坐标轴
- 滚轮缩放（以鼠标位置为锚点）
- 中键拖动平移画布

### 持久化

- 保存 / 加载 `.gboard` 工程文件（JSON 格式，含图形数据与视图变换）
- 加载时对损坏文件给出友好提示，不崩溃

---

## 技术栈

| 组件 | 用途 |
|---|---|
| **PySide6** | Qt 官方 Python 绑定，提供 `QGraphicsView` / `QGraphicsScene` / `QGraphicsItem` 三层图形框架 |
| **asteval** | 基于 AST 的沙箱表达式求值，支持预编译，比裸 `eval` 安全 |
| **Python 3.11+** | 开发与运行环境 |

不依赖 numpy，表达式求值走 asteval 内置的 `math` 函数。

---

## 安装与运行

### 环境要求

- Python 3.11 或更高版本
- Windows 10/11 或主流 Linux 发行版（Ubuntu 20.04+、Fedora 36+ 等）

### 使用 conda（推荐）

```bash
conda create -n geoboard python=3.11 -y
conda activate geoboard
pip install -r requirements.txt
python app.py
```

### 使用 venv

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

国内网络可加速：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 使用指南

### 工具栏（左侧）

| 图标 | 工具 | 操作 |
|---|---|---|
| ✥ | 选择 | 单击选中，拖动平移 |
| • | 点 | 单击落点 |
| ╱ / ─ / → | 直线 / 线段 / 射线 | 按住拖动 |
| △ / ▭ / ▱ / ⏢ | 三角形 / 矩形 / 平行四边形 / 梯形 | 按住拖动 |
| ★ / ⬡ | 五角星 / 六边形 | 以按下点为中心、拖动距离为半径 |
| ⬠ | 任意多边形 | 单击累积顶点，双击或回车结束，Esc 取消 |
| ○ / ⬭ | 圆 / 椭圆 | 以按下点为中心、拖动距离为半径 |
| xⁿ | 多项式 | 单击后弹出对话框，输入次数与系数 |
| ƒ | 函数 | 单击后弹出对话框，输入表达式与定义域 |
| ∿ | 自由曲线 | 按住鼠标描绘 |

### 顶部样式栏

从左到右依次为：描边颜色、描边粗细、线型、启用填充、填充颜色、填充算法、撤销、重做、保存、加载、清空。

### 右侧属性面板

选中图形后显示其类型信息，并提供平移、旋转、缩放、删除操作。

### 快捷键

| 快捷键 | 功能 |
|---|---|
| `Ctrl+Z` | 撤销 |
| `Ctrl+Shift+Z` / `Ctrl+Y` | 重做 |
| `Delete` / `Backspace` | 删除选中图形 |
| `Esc` | 取消当前工具操作（未完成的多边形、自由曲线等） |
| `Enter` | 结束当前多边形绘制 |

### 表达式语法（函数与多项式）

- 变量为 `x`
- 支持的函数：`sin` `cos` `tan` `asin` `acos` `atan` `sqrt` `abs` `exp` `log` `ln` `pow` `floor` `ceil` `round` `sinh` `cosh` `tanh`
- 常量：`pi` / `PI`、`e` / `E`
- 幂运算：支持 `^` 或 `**`，`-x^2` 会被正确解析为 `-(x²)`
- 示例：`sin(x)`、`x^2-3*x+1`、`sqrt(abs(x))`、`2*sin(x)/x`

**多项式输入约定**：系数按「最高次 → 常数项」顺序，用逗号分隔。例：次数 `3`，系数 `1,0,-2,1` → `x³ - 2x + 1`。

---

## 项目结构

```
geometry_board/
├── app.py                      # 应用入口
├── requirements.txt            # 运行依赖
├── requirements-dev.txt        # 开发依赖（pytest / pytest-qt 等）
│
├── core/                       # 纯 Python 逻辑层，不依赖 Qt
│   ├── geometry.py             # 向量、包围盒、距离、相交、多边形、凸包、变换
│   ├── expr.py                 # asteval 沙箱封装，表达式校验与采样
│   ├── model.py                # Shape / ShapeStyle 数据模型与序列化
│   └── history.py              # Command 体系与 Undo/Redo 栈
│
├── items/                      # 图元层（QGraphicsItem 子类）
│   ├── base_item.py            # ShapeItem 基类：绘制、命中、模型同步
│   ├── primitives.py           # 点、线、射线、多边形、圆、椭圆
│   ├── curve_items.py          # 函数曲线、自由曲线
│   └── star_hexagon.py         # 五角星 / 六边形顶点生成
│
├── scene/                      # 场景层
│   └── board_scene.py          # BoardScene：形状管理、命令调度、拖拽交互
│
├── render/                     # 渲染辅助
│   └── styles.py               # ShapeStyle → QPen / QBrush
│
├── ui/                         # 界面层
│   ├── main_window.py          # 主窗口组装、顶部样式栏、快捷键
│   ├── view.py                 # BoardView：工具状态机、缩放平移、预览
│   ├── toolbar.py              # 左侧工具栏
│   ├── property_panel.py       # 右侧属性面板
│   └── dialogs.py              # 函数 / 多项式输入对话框
│
├── persistence/                # 持久化
│   └── project.py              # 工程文件读写
│
└── tests/                      # 单元测试
    ├── test_geometry.py
    ├── test_expr.py
    ├── test_model.py
    ├── test_history.py
    ├── test_items.py
    ├── test_scene.py
    └── test_ui.py
```

---

## 架构说明

### 分层依赖

```
       ui/  ──►  scene/  ──►  items/  ──►  core/
        │           │            │           ▲
        └──► render/┘            └───────────┘
                            persistence/ ──► core/
```

- **`core/`**：完全独立的纯 Python 层，不 import 任何 Qt。所有几何算法、表达式求值、数据模型、命令栈在此实现，可被纯 pytest 单测覆盖。
- **`items/`**：把 `Shape` 包装为 `QGraphicsItem`，负责"怎么画"和"命中检测"，不持有业务状态。
- **`render/`**：`ShapeStyle` 到 `QPen` / `QBrush` 的转换。
- **`scene/`**：管理形状集合与 item 映射，所有变更走 `Command` 入 `History`，负责拖拽交互与选中框绘制。
- **`ui/`**：用户界面、工具状态机、对话框，通过高层 API 调用 `scene/`。
- **`persistence/`**：工程文件序列化与反序列化。

### 坐标系

- Item 的本地坐标 = 世界坐标，y 轴向上
- 由 `QGraphicsView.scale(1, -1)` 完成 y 轴翻转
- 鼠标 `scenePos()` 直接等于世界坐标，无需转换

### 命令模式

所有对图元的修改都通过 `Command` 完成：

| 命令 | 作用 | 撤销方式 |
|---|---|---|
| `AddShapeCommand` | 添加图形 | 从列表移除同一对象引用 |
| `RemoveShapeCommand` | 删除图形 | 按记录的索引插回原位置 |
| `ModifyShapeCommand` | 修改图形（含样式、变换） | `apply_dict` 原地还原 before 快照 |
| `CompositeCommand` | 组合多个命令作为单一单元 | 逆序 undo |

`ModifyShapeCommand` 使用 `to_dict()` 快照 + `apply_dict()` 原地还原，**保持 `Shape` 对象引用稳定**，item 层不需要重新绑定。

### 测试策略

- `core/` 纯逻辑层：无 Qt 依赖，可直接单测，覆盖几何算法、表达式沙箱、序列化、命令栈
- `items/` 与 `ui/` 层：依赖 `pytest-qt` 提供的 `qapp` fixture
- 测试直接调用内部方法（如 `scene._begin_drag` / `_update_drag` / `_end_drag`），不构造 `QGraphicsSceneMouseEvent`，保证测试稳定且快

---

## 开发与测试

### 安装开发依赖

```bash
pip install -r requirements-dev.txt
```

### 运行测试

```bash
# 全量
pytest tests/ -v

# 单模块
pytest tests/test_geometry.py -v
pytest tests/test_scene.py -v
```

### 添加新图形类型

1. 在 `core/model.py` 的 `SHAPE_TYPES` 中登记类型名
2. 在 `items/primitives.py` 或 `items/curve_items.py` 中新增 `ShapeItem` 子类，实现 `build_path()`
3. 在 `items/__init__.py` 的 `ITEM_CLASSES` 中注册
4. 如需交互绘制，在 `ui/view.py` 的 `TOOL_IDS_WITH_DRAG` 与 `_build_drag_shape` 中增加逻辑
5. 补充对应测试

### 添加新填充算法

1. 在 `core/model.py` 的 `FILL_ALGORITHMS` 中登记
2. 在 `render/styles.py` 的 `make_fill_brush` 中实现对应分支
3. 在 `ui/main_window.py` 的 `FILL_LABELS` 中增加显示项

---

## 已知限制

- **性能**：撤销 / 重做使用全量 `_sync_items`，图元超过数百时会出现可见卡顿。改进方向是按 `Command.affected_ids()` 做增量刷新。
- **持久化**：`.gboard` 目前仅有 `version: 1`，尚未建立向后兼容的迁移机制；PNG / SVG 导出尚未实现。
- **直线 / 射线选中框**：`drawForeground` 中对 `line` / `ray` 跳过选中框绘制（其包围盒为 1e4 量级，直接绘制会拖慢渲染），交互上表现为"选中无视觉反馈"。
- **框选**：目前只能单击逐个选中，尚未支持橡皮筋框选。
- **Z 序调整**：图元按添加顺序叠加，尚不支持手动置顶 / 置底。
- **图标**：工具栏使用 Unicode 字符，未使用 SVG 图标。

---

## 路线图

### v0.2（下一步）

- [ ] `_sync_items` 改为增量刷新
- [ ] `persistence/serializer.py` 与版本迁移机制
- [ ] PNG / SVG 导出
- [ ] 直线 / 射线选中框裁剪后绘制

### v0.3

- [ ] 橡皮筋框选与多选拖动入口
- [ ] Z 序调整
- [ ] 图元吸附（端点、中点、交点）
- [ ] 自定义填充图案（间距、角度、线宽）

### v1.0

- [ ] PyInstaller 双平台构建（GitHub Actions）
- [ ] 完善的用户手册与示例工程
- [ ] 跨平台字体与 DPI 兼容性测试

---

## 许可证

MIT License。

---

## 致谢

- [Qt for Python (PySide6)](https://doc.qt.io/qtforpython/)
- [asteval](https://github.com/newville/asteval)

---

## 使用说明

这份 README 的几个设计取向，供你参考：

1. **功能特性按用户视角组织**，而不是按代码模块罗列——用户关心"能画什么、能改什么"，不关心 `items/` 和 `scene/` 怎么分。
2. **架构说明放在开发章节**，用一张依赖图 + 命令模式表格，让后续接手代码的人 30 秒内理解分层。
3. **已知限制如实写**，包括 `_sync_items` 全量重建、persistence 是 v1、直线选中框跳过、框选缺失。不粉饰，方便你自己或协作者规划路线。
4. **路线图分三档**（v0.2 / v0.3 / v1.0），和我之前给你的项目评价里"优先级"一致——先性能与持久化，再交互手感，最后打包。
5. **`core/` 不依赖 Qt** 这条纪律在 README 里出现了两次（技术栈和架构说明），因为它是整个项目最值钱的资产，必须让后来者知道不能破坏它。

如果后续添加 `render/fill_algorithms.py`（自定义图案）、`persistence/serializer.py`（带版本迁移）或 CI 配置，记得同步更新"项目结构"和"路线图"两处即可。