"""Reusable widgets shared by the Phase 1 page shells."""

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
from PySide6.QtCore import QMargins, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
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


class SidebarButton(QPushButton):
    def __init__(self, icon_text: str, label: str, parent: QWidget | None = None):
        super().__init__(f"{icon_text}    {label}", parent)
        self.setObjectName("sidebarButton")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(50)


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
        icon_text: str,
        action: QWidget | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        icon = QLabel(icon_text)
        icon.setObjectName("headerIcon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFixedSize(64, 64)
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
    ):
        super().__init__(parent)
        self.setObjectName("card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(20, 18, 20, 18)
        self.body.setSpacing(10)
        self.title_label: QLabel | None = None
        self.subtitle_label: QLabel | None = None

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

    def add_placeholder(self, text: str = "Conteúdo disponível em uma próxima fase.") -> QLabel:
        label = QLabel(text)
        label.setObjectName("placeholderText")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        self.body.addWidget(label, 1)
        return label


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
        self.setMinimumSize(120, 190)
        if self.title_label is not None:
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.icon_label = QLabel(icon_text)
        self.icon_label.setObjectName("metricIcon")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedSize(52, 52)
        self.icon_label.setStyleSheet(
            f"background: {accent}; color: white; border-radius: 26px;"
        )
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


class PageScaffold(QScrollArea):
    def __init__(
        self,
        title: str,
        subtitle: str,
        icon_text: str,
        action: QWidget | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("pageScroll")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.canvas = QWidget()
        self.canvas.setObjectName("pageCanvas")
        self.content = QVBoxLayout(self.canvas)
        self.content.setContentsMargins(30, 26, 30, 20)
        self.content.setSpacing(20)
        self.content.addWidget(PageHeader(title, subtitle, icon_text, action))

        separator = QFrame()
        separator.setObjectName("separator")
        self.content.addWidget(separator)
        self.setWidget(self.canvas)


class PlaceholderTable(Card):
    def __init__(self, columns: list[str], rows: int = 4, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self.body.setSpacing(0)
        header = QHBoxLayout()
        header.setSpacing(1)
        for column in columns:
            label = QLabel(column.upper())
            label.setObjectName("tableHeader")
            header.addWidget(label, 1)
        self.body.addLayout(header)

        for _ in range(rows):
            row = QFrame()
            row.setFixedHeight(48)
            row.setStyleSheet("border-bottom: 1px solid #ebe8df;")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(10, 0, 10, 0)
            for _column in columns:
                marker = QLabel("—")
                marker.setObjectName("placeholderText")
                row_layout.addWidget(marker, 1)
            self.body.addWidget(row)


class ChartPlaceholder(QLabel):
    def __init__(self, text: str = "GRÁFICO", parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setObjectName("chartPlaceholder")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(110, 110)


class ReportChartCard(Card):
    """Theme-aware QtCharts card with a safe empty state."""

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        parent: QWidget | None = None,
    ):
        super().__init__(title, subtitle, parent)
        self.setMinimumHeight(320)
        self.chart_view = QChartView()
        self.chart_view.setObjectName("reportChart")
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart_view.setMinimumHeight(235)
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
        self.empty_label.setMinimumHeight(235)
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
        series.setPieSize(0.78)
        for index, (label, value) in enumerate(positive_values):
            pie_slice = series.append(label, value)
            pie_slice.setColor(
                QColor(CHART_COLORS[index % len(CHART_COLORS)])
            )
            pie_slice.setBorderColor(QColor(CARD))
            pie_slice.setBorderWidth(2)
            pie_slice.setLabel(f"{label}: {value}")
            pie_slice.setLabelColor(QColor(TEXT))
            pie_slice.setLabelVisible(True)

        chart = self._new_chart()
        chart.addSeries(series)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
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
    """Small code-drawn landscape motif inspired by the reference footer."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMinimumHeight(105)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt naming convention
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width = self.width()
        height = self.height()

        back = QPainterPath()
        back.moveTo(0, height)
        back.lineTo(0, height * 0.63)
        back.cubicTo(width * 0.18, height * 0.25, width * 0.32, height * 0.75, width * 0.48, height * 0.48)
        back.cubicTo(width * 0.64, height * 0.2, width * 0.78, height * 0.72, width, height * 0.42)
        back.lineTo(width, height)
        back.closeSubpath()
        painter.fillPath(back, QColor("#c8c9b5"))

        front = QPainterPath()
        front.moveTo(0, height)
        front.lineTo(0, height * 0.78)
        front.cubicTo(width * 0.2, height * 0.5, width * 0.35, height, width * 0.55, height * 0.68)
        front.cubicTo(width * 0.75, height * 0.42, width * 0.86, height * 0.88, width, height * 0.64)
        front.lineTo(width, height)
        front.closeSubpath()
        painter.fillPath(front, QColor("#788765"))

        center_x = width * 0.52
        ground_y = height * 0.91
        painter.setPen(QPen(QColor(DARK_GREEN), 3))
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

        painter.setPen(QPen(QColor(ORANGE), 2))
        painter.drawLine(int(center_x), int(height * 0.42), int(center_x), int(height * 0.25))
        painter.drawLine(int(center_x), int(height * 0.25), int(center_x + 14), int(height * 0.3))
