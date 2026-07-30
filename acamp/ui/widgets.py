"""Reusable widgets shared by the desktop interface."""

from __future__ import annotations

from PySide6.QtCharts import (
    QAbstractBarSeries,
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QPieSeries,
    QValueAxis,
)
from PySide6.QtCore import QMargins, QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .theme import (
    BORDER,
    CARD,
    CHART_COLORS,
    DARK_GREEN,
    MUTED,
    OLIVE,
    ORANGE,
    TEXT,
)


ICON_NAMES = {
    "dashboard",
    "registrations",
    "finance",
    "inventory",
    "activities",
    "reports",
    "sync",
    "search",
    "heart",
    "expenses",
    "warning",
    "transportation",
}


def make_line_icon(
    name: str,
    color: str = "#ffffff",
    size: int = 32,
) -> QIcon:
    """Create the restrained outline icons used throughout the mockups."""

    canvas = QPixmap(size, size)
    canvas.fill(Qt.GlobalColor.transparent)
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    scale = size / 32.0
    painter.scale(scale, scale)
    pen = QPen(QColor(color), 1.8)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    if name == "dashboard":
        painter.drawArc(QRectF(5, 5, 22, 18), 0, 180 * 16)
        painter.drawLine(QPointF(16, 14), QPointF(22, 10))
        for x, height in ((7, 7), (13, 11), (19, 15), (25, 9)):
            painter.drawRect(QRectF(x - 2, 27 - height, 4, height))
    elif name == "registrations":
        painter.drawEllipse(QRectF(7, 5, 8, 8))
        painter.drawEllipse(QRectF(18, 7, 7, 7))
        painter.drawArc(QRectF(3, 14, 17, 13), 0, 180 * 16)
        painter.drawArc(QRectF(15, 15, 14, 11), 0, 180 * 16)
    elif name == "finance":
        painter.drawEllipse(QRectF(5, 4, 22, 24))
        font = QFont("Segoe UI", 15)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        painter.drawText(QRectF(5, 3, 22, 26), Qt.AlignmentFlag.AlignCenter, "$")
    elif name == "inventory":
        top = QPointF(16, 4)
        left = QPointF(5, 10)
        right = QPointF(27, 10)
        middle = QPointF(16, 16)
        bottom = QPointF(16, 29)
        painter.drawLine(top, left)
        painter.drawLine(top, right)
        painter.drawLine(left, middle)
        painter.drawLine(right, middle)
        painter.drawLine(middle, bottom)
        painter.drawLine(left, QPointF(5, 22))
        painter.drawLine(QPointF(5, 22), bottom)
        painter.drawLine(right, QPointF(27, 22))
        painter.drawLine(QPointF(27, 22), bottom)
    elif name == "activities":
        painter.drawRoundedRect(QRectF(9, 5, 14, 13), 2, 2)
        painter.drawArc(QRectF(3, 7, 10, 10), 90 * 16, 180 * 16)
        painter.drawArc(QRectF(19, 7, 10, 10), -90 * 16, 180 * 16)
        painter.drawLine(QPointF(16, 18), QPointF(16, 25))
        painter.drawLine(QPointF(11, 26), QPointF(21, 26))
    elif name == "reports":
        painter.drawLine(QPointF(5, 27), QPointF(28, 27))
        painter.drawRoundedRect(QRectF(7, 17, 4, 8), 1, 1)
        painter.drawRoundedRect(QRectF(14, 11, 4, 14), 1, 1)
        painter.drawRoundedRect(QRectF(21, 5, 4, 20), 1, 1)
    elif name == "sync":
        painter.drawRoundedRect(QRectF(6, 4, 20, 24), 2, 2)
        for y in (11, 17, 23):
            painter.drawLine(QPointF(9, y), QPointF(23, y))
        painter.drawLine(QPointF(14, 8), QPointF(14, 25))
    elif name == "search":
        painter.drawEllipse(QRectF(5, 5, 16, 16))
        painter.drawLine(QPointF(18, 18), QPointF(27, 27))
    elif name == "heart":
        path = QPainterPath(QPointF(16, 27))
        path.cubicTo(13, 23, 5, 18, 5, 11)
        path.cubicTo(5, 4, 14, 3, 16, 9)
        path.cubicTo(18, 3, 27, 4, 27, 11)
        path.cubicTo(27, 18, 19, 23, 16, 27)
        painter.drawPath(path)
    elif name == "expenses":
        painter.drawLine(QPointF(16, 4), QPointF(16, 24))
        painter.drawLine(QPointF(8, 17), QPointF(16, 25))
        painter.drawLine(QPointF(24, 17), QPointF(16, 25))
    elif name == "warning":
        path = QPainterPath(QPointF(16, 4))
        path.lineTo(QPointF(28, 27))
        path.lineTo(QPointF(4, 27))
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(QPointF(16, 11), QPointF(16, 19))
        painter.drawPoint(QPointF(16, 23))
    elif name == "transportation":
        painter.drawRoundedRect(QRectF(5, 12, 22, 10), 3, 3)
        painter.drawLine(QPointF(9, 12), QPointF(12, 7))
        painter.drawLine(QPointF(12, 7), QPointF(21, 7))
        painter.drawLine(QPointF(21, 7), QPointF(25, 12))
        painter.drawEllipse(QRectF(8, 20, 5, 5))
        painter.drawEllipse(QRectF(20, 20, 5, 5))
    painter.end()
    return QIcon(canvas)


class SidebarButton(QPushButton):
    def __init__(self, icon_name: str, label: str, parent: QWidget | None = None):
        super().__init__(label, parent)
        self.setObjectName("sidebarButton")
        self.setIcon(make_line_icon(icon_name, "#f3f2eb", 30))
        self.setIconSize(QSize(28, 28))
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(54)


class PrimaryButton(QPushButton):
    def __init__(self, text: str, parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setObjectName("primaryButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(40)


class PageHeader(QWidget):
    def __init__(
        self,
        title: str,
        subtitle: str,
        icon_name: str,
        action: QWidget | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        icon = QLabel()
        icon.setObjectName("headerIcon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFixedSize(68, 68)
        icon.setPixmap(make_line_icon(icon_name, "#ffffff", 38).pixmap(38, 38))
        layout.addWidget(icon)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("pageSubtitle")
        subtitle_label.setWordWrap(True)
        text_layout.addWidget(title_label)
        text_layout.addWidget(subtitle_label)
        layout.addLayout(text_layout, 1)

        if action is not None:
            layout.addWidget(action, 0, Qt.AlignmentFlag.AlignVCenter)


class Card(QFrame):
    def __init__(
        self,
        title: str = "",
        subtitle: str = "",
        parent: QWidget | None = None,
        *,
        icon_name: str = "",
    ):
        super().__init__(parent)
        self.setObjectName("card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(20, 18, 20, 18)
        self.body.setSpacing(10)
        self.title_label: QLabel | None = None
        self.subtitle_label: QLabel | None = None

        if title and icon_name:
            heading = QHBoxLayout()
            heading.setSpacing(12)
            icon = QLabel()
            icon.setObjectName("sectionIcon")
            icon.setFixedSize(46, 46)
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon.setPixmap(
                make_line_icon(icon_name, DARK_GREEN, 27).pixmap(27, 27)
            )
            heading.addWidget(icon)
            heading_text = QVBoxLayout()
            heading_text.setSpacing(2)
            self.title_label = QLabel(title)
            self.title_label.setObjectName("cardTitle")
            self.title_label.setWordWrap(True)
            heading_text.addWidget(self.title_label)
            if subtitle:
                self.subtitle_label = QLabel(subtitle)
                self.subtitle_label.setObjectName("cardSubtitle")
                self.subtitle_label.setWordWrap(True)
                heading_text.addWidget(self.subtitle_label)
            heading.addLayout(heading_text, 1)
            self.body.addLayout(heading)
        else:
            if title:
                self.title_label = QLabel(title)
                self.title_label.setObjectName("cardTitle")
                self.title_label.setWordWrap(True)
                self.body.addWidget(self.title_label)
            if subtitle:
                self.subtitle_label = QLabel(subtitle)
                self.subtitle_label.setObjectName("cardSubtitle")
                self.subtitle_label.setWordWrap(True)
                self.body.addWidget(self.subtitle_label)

class MetricCard(Card):
    clicked = Signal()

    def __init__(
        self,
        title: str,
        accent: str = OLIVE,
        icon_text: str = "",
        parent: QWidget | None = None,
    ):
        super().__init__(title, parent=parent)
        self._clickable = False
        self.setMinimumSize(125, 182)
        if self.title_label is not None:
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.icon_label = QLabel()
        self.icon_label.setObjectName("metricIcon")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedSize(52, 52)
        self.icon_label.setStyleSheet(
            f"background: {accent}; color: white; border-radius: 26px;"
        )
        if icon_text in ICON_NAMES:
            self.icon_label.setPixmap(
                make_line_icon(icon_text, "#ffffff", 30).pixmap(30, 30)
            )
        else:
            self.icon_label.setText(icon_text)
        self.body.insertWidget(
            0,
            self.icon_label,
            0,
            Qt.AlignmentFlag.AlignHCenter,
        )

        self.value_label = QLabel("—")
        self.value_label.setObjectName("metricValue")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setWordWrap(True)
        self.value_label.setStyleSheet(f"color: {accent};")
        self.body.addWidget(self.value_label, 1)

        self.details_label = QLabel()
        self.details_label.setObjectName("metricDetails")
        self.details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.details_label.setWordWrap(True)
        self.details_label.hide()
        self.body.addWidget(self.details_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)

    def set_details(self, details: str) -> None:
        self.details_label.setText(details)
        self.details_label.setVisible(bool(details))

    def set_clickable(self, tooltip: str = "") -> None:
        self._clickable = True
        self.setProperty("clickable", True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(tooltip)
        self.setToolTip(tooltip)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if (
            self._clickable
            and event.button() == Qt.MouseButton.LeftButton
        ):
            self.clicked.emit()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if (
            self._clickable
            and event.key() in {
                Qt.Key.Key_Enter,
                Qt.Key.Key_Return,
                Qt.Key.Key_Space,
            }
        ):
            self.clicked.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class PageScaffold(QScrollArea):
    def __init__(
        self,
        title: str,
        subtitle: str,
        icon_name: str,
        action: QWidget | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("pageScroll")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.canvas = QWidget()
        self.canvas.setObjectName("pageCanvas")
        self.content = QVBoxLayout(self.canvas)
        self.content.setContentsMargins(32, 28, 32, 0)
        self.content.setSpacing(18)
        self.header = PageHeader(title, subtitle, icon_name, action)
        self.content.addWidget(self.header)

        separator = QFrame()
        separator.setObjectName("separator")
        self.content.addWidget(separator)
        self.setWidget(self.canvas)


class ReportChartCard(Card):
    """Theme-aware QtCharts card with a safe empty state."""

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        parent: QWidget | None = None,
    ):
        super().__init__(title, subtitle, parent)
        self.setMinimumHeight(250)
        self.chart_view = QChartView()
        self.chart_view.setObjectName("reportChart")
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart_view.setMinimumHeight(180)
        self.chart_view.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.empty_label = QLabel(
            "Não há dados suficientes para gerar este relatório."
        )
        self.empty_label.setObjectName("reportEmptyState")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setWordWrap(True)
        self.empty_label.setMinimumHeight(180)
        self.empty_label.hide()
        self.body.addWidget(self.chart_view, 1)
        self.body.addWidget(self.empty_label, 1)

    def show_empty(self, message: str) -> None:
        self.empty_label.setText(message)
        self.chart_view.hide()
        self.empty_label.show()

    def set_pie_data(
        self,
        values: tuple[tuple[str, int], ...],
    ) -> None:
        positive_values = tuple(
            (label, value)
            for label, value in values
            if value > 0
        )
        if not positive_values:
            self.show_empty(
                "Não há dados suficientes para gerar este relatório."
            )
            return

        series = QPieSeries()
        series.setHoleSize(0.46)
        series.setPieSize(0.7)
        for index, (label, value) in enumerate(positive_values):
            pie_slice = series.append(label, value)
            pie_slice.setColor(
                QColor(CHART_COLORS[index % len(CHART_COLORS)])
            )
            pie_slice.setBorderColor(QColor(CARD))
            pie_slice.setBorderWidth(2)
            pie_slice.setLabel(f"{label}: {value}")
            pie_slice.setLabelVisible(False)

        chart = self._new_chart()
        chart.addSeries(series)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
        chart.legend().setLabelColor(QColor(TEXT))
        self._show_chart(chart)

    def set_bar_data(
        self,
        values: tuple[tuple[str, int], ...],
        *,
        label_angle: int = 0,
    ) -> None:
        if not values:
            self.show_empty(
                "Não há dados suficientes para gerar este relatório."
            )
            return

        bar_set = QBarSet("")
        bar_set.append([float(value) for _label, value in values])
        bar_set.setColor(QColor(OLIVE))
        bar_set.setBorderColor(QColor(DARK_GREEN))

        series = QBarSeries()
        series.append(bar_set)
        series.setBarWidth(0.72)
        series.setLabelsVisible(True)
        series.setLabelsFormat("@value")
        series.setLabelsPosition(
            QAbstractBarSeries.LabelsPosition.LabelsOutsideEnd
        )

        chart = self._new_chart()
        chart.addSeries(series)
        chart.legend().setVisible(False)

        category_axis = QBarCategoryAxis()
        category_axis.append([label for label, _value in values])
        category_axis.setLabelsAngle(label_angle)
        category_axis.setLabelsColor(QColor(TEXT))
        category_axis.setLinePenColor(QColor(BORDER))
        chart.addAxis(category_axis, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(category_axis)

        numeric_values = [value for _label, value in values]
        lower, upper = self._bar_range(numeric_values)
        value_axis = QValueAxis()
        value_axis.setRange(lower, upper)
        value_axis.setTickCount(5)
        value_axis.setLabelFormat("%d")
        value_axis.setLabelsColor(QColor(MUTED))
        value_axis.setGridLinePen(QPen(QColor("#e8e4d9"), 1))
        value_axis.setLinePenColor(QColor(BORDER))
        chart.addAxis(value_axis, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(value_axis)
        self._show_chart(chart)

    @staticmethod
    def _bar_range(values: list[int]) -> tuple[float, float]:
        minimum = min(values)
        maximum = max(values)
        if minimum == maximum == 0:
            return -1.0, 1.0
        if minimum >= 0:
            return 0.0, float(maximum) * 1.2 or 1.0
        if maximum <= 0:
            return float(minimum) * 1.2, 0.0
        padding = max(1.0, float(maximum - minimum) * 0.12)
        return float(minimum) - padding, float(maximum) + padding

    @staticmethod
    def _new_chart() -> QChart:
        chart = QChart()
        chart.setBackgroundVisible(False)
        chart.setPlotAreaBackgroundVisible(False)
        chart.setMargins(QMargins(0, 0, 0, 0))
        chart.setTitleBrush(QBrush(QColor(TEXT)))
        return chart

    def _show_chart(self, chart: QChart) -> None:
        previous_chart = self.chart_view.chart()
        self.chart_view.setChart(chart)
        if previous_chart is not chart:
            previous_chart.deleteLater()
        self.empty_label.hide()
        self.chart_view.show()


class CampLandscape(QWidget):
    """Layered code-drawn landscape motif matching the reference footer."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMinimumHeight(112)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt naming convention
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width = self.width()
        height = self.height()

        sky = QLinearGradient(0, 0, 0, height)
        sky.setColorAt(0, QColor("#f5f2e9"))
        sky.setColorAt(1, QColor("#e6e5d7"))
        painter.fillRect(self.rect(), sky)

        far = QPainterPath()
        far.moveTo(0, height)
        far.lineTo(0, height * 0.56)
        far.cubicTo(
            width * 0.12,
            height * 0.3,
            width * 0.22,
            height * 0.62,
            width * 0.34,
            height * 0.44,
        )
        far.cubicTo(
            width * 0.46,
            height * 0.27,
            width * 0.56,
            height * 0.66,
            width * 0.7,
            height * 0.43,
        )
        far.cubicTo(
            width * 0.82,
            height * 0.25,
            width * 0.9,
            height * 0.58,
            width,
            height * 0.37,
        )
        far.lineTo(width, height)
        far.closeSubpath()
        painter.fillPath(far, QColor("#d8d8ca"))

        back = QPainterPath()
        back.moveTo(0, height)
        back.lineTo(0, height * 0.67)
        back.cubicTo(width * 0.18, height * 0.36, width * 0.32, height * 0.78, width * 0.48, height * 0.52)
        back.cubicTo(width * 0.64, height * 0.3, width * 0.78, height * 0.75, width, height * 0.48)
        back.lineTo(width, height)
        back.closeSubpath()
        painter.fillPath(back, QColor("#b9bea6"))

        front = QPainterPath()
        front.moveTo(0, height)
        front.lineTo(0, height * 0.78)
        front.cubicTo(width * 0.2, height * 0.5, width * 0.35, height, width * 0.55, height * 0.68)
        front.cubicTo(width * 0.75, height * 0.42, width * 0.86, height * 0.88, width, height * 0.64)
        front.lineTo(width, height)
        front.closeSubpath()
        painter.fillPath(front, QColor("#6f8060"))

        foreground = QPainterPath()
        foreground.moveTo(0, height)
        foreground.lineTo(0, height * 0.88)
        foreground.cubicTo(
            width * 0.2,
            height * 0.69,
            width * 0.34,
            height * 1.02,
            width * 0.52,
            height * 0.83,
        )
        foreground.cubicTo(
            width * 0.7,
            height * 0.65,
            width * 0.84,
            height * 0.98,
            width,
            height * 0.77,
        )
        foreground.lineTo(width, height)
        foreground.closeSubpath()
        painter.fillPath(foreground, QColor("#405a3f"))

        center_x = width * 0.52
        ground_y = height * 0.91
        painter.setPen(QPen(QColor(DARK_GREEN), 2.2))
        painter.setBrush(QColor(DARK_GREEN))
        tent = QPainterPath()
        tent.moveTo(center_x - 35, ground_y)
        tent.lineTo(center_x, height * 0.42)
        tent.lineTo(center_x + 38, ground_y)
        tent.closeSubpath()
        painter.drawPath(tent)
        painter.setBrush(QColor("#e8e5d8"))
        opening = QPainterPath()
        opening.moveTo(center_x - 4, ground_y)
        opening.lineTo(center_x, height * 0.52)
        opening.lineTo(center_x + 16, ground_y)
        opening.closeSubpath()
        painter.drawPath(opening)

        painter.setPen(QPen(QColor("#667653"), 2))
        painter.drawLine(int(center_x), int(height * 0.42), int(center_x), int(height * 0.25))
        painter.drawLine(int(center_x), int(height * 0.25), int(center_x + 14), int(height * 0.3))

        painter.setPen(QPen(QColor("#8d8f75"), 2))
        cross_x = width * 0.67
        painter.drawLine(
            QPointF(cross_x, height * 0.66),
            QPointF(cross_x, height * 0.42),
        )
        painter.drawLine(
            QPointF(cross_x - 7, height * 0.5),
            QPointF(cross_x + 7, height * 0.5),
        )

        for x, tree_height in (
            (0.03, 35),
            (0.055, 48),
            (0.085, 30),
            (0.12, 40),
            (0.88, 34),
            (0.92, 49),
            (0.955, 40),
            (0.98, 54),
        ):
            self._draw_tree(
                painter,
                QPointF(width * x, height * 0.98),
                tree_height,
            )
        painter.end()

    @staticmethod
    def _draw_tree(
        painter: QPainter,
        base: QPointF,
        tree_height: float,
        color: str = "#263d2b",
    ) -> None:
        painter.setPen(QPen(QColor(color), 1.4))
        painter.setBrush(QColor(color))
        painter.drawLine(
            QPointF(base.x(), base.y()),
            QPointF(base.x(), base.y() - tree_height),
        )
        crown = QPainterPath()
        crown.moveTo(base.x(), base.y() - tree_height)
        crown.lineTo(base.x() - tree_height * 0.2, base.y() - tree_height * 0.48)
        crown.lineTo(base.x() - tree_height * 0.09, base.y() - tree_height * 0.52)
        crown.lineTo(base.x() - tree_height * 0.25, base.y() - tree_height * 0.2)
        crown.lineTo(base.x() + tree_height * 0.25, base.y() - tree_height * 0.2)
        crown.lineTo(base.x() + tree_height * 0.09, base.y() - tree_height * 0.52)
        crown.lineTo(base.x() + tree_height * 0.2, base.y() - tree_height * 0.48)
        crown.closeSubpath()
        painter.drawPath(crown)


class BrandMark(QWidget):
    """Code-drawn pine and tent used above the ACAMP wordmark."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedHeight(58)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center = self.width() / 2
        CampLandscape._draw_tree(
            painter,
            QPointF(center - 14, 52),
            43,
            "#c6cbb1",
        )
        painter.setPen(QPen(QColor("#f1f0e8"), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(QPointF(center + 7, 50), QPointF(center + 22, 27))
        painter.drawLine(QPointF(center + 22, 27), QPointF(center + 35, 50))
        painter.drawLine(QPointF(center + 7, 50), QPointF(center + 35, 50))
        painter.drawLine(QPointF(center + 22, 27), QPointF(center + 22, 50))
        painter.end()


class SidebarFooterCard(QFrame):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("sidebarFooterCard")
        self.setMinimumHeight(145)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(6)

        help_label = QLabel("?")
        help_label.setObjectName("sidebarHelp")
        help_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        help_label.setFixedSize(28, 28)
        message = QLabel("Servindo, amando\ne fazendo a diferença!")
        message.setObjectName("sidebarFooterText")
        message.setWordWrap(True)
        heart = QLabel("♥")
        heart.setObjectName("sidebarHeart")
        layout.addWidget(help_label, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(message)
        layout.addWidget(heart)
